"""Orchestrator — 1-Pick Rescue Agent 라이프사이클을 실행.

IDLE → POOL_SCAN → SCORING → PICK_READY → GROUNDING → SAFETY_CHECK →
CONTACT_READY → TRANSCRIPT_READY → ANALYSIS → CRM_DRAFT → NEXT_ACTION → DONE

- Customer Selection Agent / Grounding and Safety Agent / Conversation Analysis Agent 를 순서대로 호출
- 각 단계의 StepResult evidence 를 수집
- 잘못된 순서 호출 / 미정의 상태는 RuntimeResult.errors 에 기록하고 중단
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from src.data_loader import Customer, Contract, DataLoader, DataLoadingError
from src.config import DEMO_AS_OF_DATE
from src.demo_state import (
    set_transcript_loaded,
)
from src.runtime_models import (
    AgentError,
    RuntimeResult,
    StepResult,
    WorkflowState,
)
from src.agents.customer_selection import (
    run_customer_selection,
    load_contracts_by_customer,
)
from src.agents.grounding import (
    default_grounding,
)
from src.agents.safety import run_safety_review
from src.agents.grounding_safety import run_grounding_safety
from src.agents.conversation_analysis import run_conversation_analysis, build_crm_record_envelope

_STATE_KEY = "workflow_state"
_EVIDENCE_KEY = "workflow_evidence"
_OUTPUT_KEY = "runtime_result"


@dataclass
class PipelineInput:
    customers: list[Customer]
    contracts: list[Contract]
    score_rules: list[dict[str, Any]]
    safety_rules: list[dict[str, Any]]
    knowledge_dir: Path
    transcript_text: str = ""


@dataclass
class OrchestratorResult:
    steps: list[StepResult]
    output: RuntimeResult


def _read_transcript(transcript_text: str) -> str:
    """transcript 텍스트를 전달받아 사용. 파일 경로가 아닌 텍스트 본문."""
    return transcript_text


def _load_pipeline_input(
    data_root: Path,
    customers_json: str = "customers.json",
    contracts_json: str = "contracts.json",
    scoring_rules_json: str = "scoring_rules.json",
    safety_rules_json: str | None = None,
    knowledge_dir: str = "knowledge",
) -> PipelineInput:
    """파일 경로 기반 로딩 — 데모 실행 편의 함수.

    시드(customers/contracts/scoring_rules)는 DataLoader 의 검증 로딩을 사용하고,
    safety_rules.json 은 별도로 읽는다. safety_rules_json 이 None 이면
    config/safety_rules.json 을 사용한다.
    """
    loader = DataLoader().load_all()
    customers = list(loader.customers.values())
    contracts = loader.contracts
    score_rules: list[dict[str, Any]] = []
    for r in loader.scoring_rules:
        score_rules.append(dict(r.raw) if r.raw else {
            "rule_id": r.rule_id,
            "name_kr": r.name_kr,
            "condition": r.condition,
            "points": r.points,
            "category": r.category,
        })

    safety_rules: list[dict[str, Any]] = []
    if safety_rules_json:
        # 명시 경로: data_root 를 기준으로 하는 상대 경로로 취급한다
        safety_path = data_root / safety_rules_json
    else:
        # 기본 경로: 프로젝트 루트의 config/safety_rules.json
        safety_path = data_root.parent / "config" / "safety_rules.json"
    if safety_path.exists():
        raw = json.loads(safety_path.read_text(encoding="utf-8"))
        safety_rules = raw.get("safety_rules", []) if isinstance(raw, dict) else raw
    kh_dir = data_root / knowledge_dir

    return PipelineInput(
        customers=customers,
        contracts=contracts,
        score_rules=score_rules,
        safety_rules=safety_rules,
        knowledge_dir=kh_dir,
    )


def _assert_transition(current: str, next_state: str, errors: list[AgentError]) -> bool:
    """정상 순서가 아니면 errors 에 기록하고 False."""
    from src.runtime_models import is_valid_transition

    if not is_valid_transition(current, next_state):
        errors.append(AgentError(
            agent="orchestrator",
            reason=f"invalid_transition: {current} -> {next_state}",
        ))
        return False
    return True


def run_pipeline(inp: PipelineInput, saved_transcript: str | None = None) -> OrchestratorResult:
    """전체 라이프사이클을 한 번에 실행하고 (steps, output) 을 반환.

    saved_transcript 가 주어지면 CONTACT_READY 이후 해당 대본을 사용한다.
    없으면 이미 로드된 transcript (demo_state) 를 사용한다 (있는 경우).
    """
    steps: list[StepResult] = []
    errors: list[AgentError] = []
    state = WorkflowState.IDLE

    # 1) POOL_SCAN → SCORING → PICK_READY
    if not _assert_transition(state, WorkflowState.POOL_SCAN, errors):
        return _error_result(errors)
    state = WorkflowState.POOL_SCAN
    # POOL_SCAN 자체는 스텝 없음(명시적 스텝은 customer_selection 이 SCORING 수행)

    if not _assert_transition(state, WorkflowState.SCORING, errors):
        return _error_result(errors)
    state = WorkflowState.SCORING
    selection, sel_step = run_customer_selection(
        inp.customers,
        load_contracts_by_customer(inp.contracts),
        inp.score_rules,
        DEMO_AS_OF_DATE,
    )
    state = sel_step.state  # PICK_READY 또는 POOL_SCAN(후보 없음)
    steps.append(sel_step)

    if not selection.picked_customer:
        errors.append(AgentError(
            agent="customer_selection",
            reason="no_eligible_candidate",
        ))
        return OrchestratorResult(steps=steps, output=RuntimeResult(
            workflow_state=WorkflowState.POOL_SCAN,
            errors=errors,
        ))

    # 2) GROUNDING
    if not _assert_transition(state, WorkflowState.GROUNDING, errors):
        return _error_result(errors, steps, WorkflowState.PICK_READY)
    state = WorkflowState.GROUNDING
    script_text = saved_transcript or _read_transcript(inp.transcript_text)
    grounding, g_step = default_grounding(script_text, inp.knowledge_dir)
    steps.append(g_step)

    # 2-1) Grounding and Safety Agent — Contact Reason + 채널별 스크립트 + Safety
    picked_contracts = [c for c in inp.contracts if c.customer_id == selection.picked_customer.customer_id]
    gs = run_grounding_safety(
        selection.picked_customer,
        picked_contracts,
        inp.knowledge_dir,
        inp.safety_rules,
    )

    # 3) SAFETY_CHECK
    if not _assert_transition(state, WorkflowState.SAFETY_CHECK, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.SAFETY_CHECK
    evidence_refs = [i.evidence_ref for i in grounding.items if i.evidence_ref]
    safety = run_safety_review(script_text, inp.safety_rules, evidence_refs)
    s_step = safety.step
    steps.append(s_step)

    if safety.decision.decision == "REJECTED":
        # 안전장치: FEEDBACK 으로 전이하고 중단(재작성 요청)
        return OrchestratorResult(steps=steps, output=RuntimeResult(
            workflow_state=WorkflowState.FEEDBACK,
            errors=errors,
        ))

    # 4) CONTACT_READY (연락 준비 완료)
    if not _assert_transition(state, WorkflowState.CONTACT_READY, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.CONTACT_READY
    steps.append(StepResult(
        state=state,
        step_name="contact_ready",
        summary=f"1-Pick: {selection.picked_customer.name} 연락 준비 완료",
    ))

    # 5) TRANSCRIPT_READY (대본 로드 확인)
    if not _assert_transition(state, WorkflowState.TRANSCRIPT_READY, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.TRANSCRIPT_READY
    set_transcript_loaded(bool(script_text))
    steps.append(StepResult(
        state=state,
        step_name="transcript_ready",
        summary=f"transcript_loaded={bool(script_text)}",
    ))

    # 6) ANALYSIS — Conversation Analysis Agent
    if not _assert_transition(state, WorkflowState.ANALYSIS, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.ANALYSIS
    renewal_dates = [c.renewal_date for c in picked_contracts if c.renewal_date]
    renewal = min(renewal_dates) if renewal_dates else None
    ca = run_conversation_analysis(
        script_text,
        selection.picked_customer.customer_id,
        selection.picked_customer.name,
        renewal or "",
    )
    steps.append(StepResult(
        state=state,
        step_name="conversation_analysis",
        summary=ca.step_summary,
    ))

    # 7) CRM_DRAFT — DRAFT / FC_REVIEW envelope
    if not _assert_transition(state, WorkflowState.CRM_DRAFT, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.CRM_DRAFT
    crm_envelope = build_crm_record_envelope(dict(ca.crm_draft))
    steps.append(StepResult(
        state=state,
        step_name="crm_draft",
        summary=(
            f"status={crm_envelope['status']}, phase={crm_envelope['phase']}, "
            f"fc_confirm_required={crm_envelope['fc_confirm_required']}"
        ),
    ))

    # 8) NEXT_ACTION — SUGGESTED / Calendar PENDING_FC_CONFIRM
    if not _assert_transition(state, WorkflowState.NEXT_ACTION, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.NEXT_ACTION
    steps.append(StepResult(
        state=state,
        step_name="next_action",
        summary=f"actions={len(ca.next_actions)}, calendar={ca.calendar_candidate.get('status')}",
    ))

    # 9) DONE
    if not _assert_transition(state, WorkflowState.DONE, errors):
        return _error_result(errors, steps, state)
    state = WorkflowState.DONE
    steps.append(StepResult(state=state, step_name="done", summary="파이프라인 완료"))

    output = RuntimeResult(
        daily_pick={
            "customer_id": selection.picked_customer.customer_id,
            "name": selection.picked_customer.name,
            "score": selection.picked_score.total if selection.picked_score else None,
        },
        script_result={
            "contact_reason": gs.contact_reason,
            "scripts": gs.scripts,
            "grounding_docs": gs.grounding_docs,
        },
        analysis_result=ca.analysis,
        crm_draft=crm_envelope,
        next_action_result={
            "next_actions": ca.next_actions,
            "calendar_candidate": ca.calendar_candidate,
        },
        workflow_state=state,
        errors=errors,
    )
    return OrchestratorResult(steps=steps, output=output)


def _error_result(
    errors: list[AgentError],
    steps: list[StepResult] | None = None,
    state: str = WorkflowState.IDLE,
) -> OrchestratorResult:
    return OrchestratorResult(
        steps=steps or [],
        output=RuntimeResult(workflow_state=state, errors=errors),
    )


def get_workflow_state() -> str:
    """현재 workflow 상태 (demo_state 와 별개)."""
    import streamlit as st

    return st.session_state.get(_STATE_KEY, WorkflowState.IDLE)


def set_workflow_state(state: str) -> None:
    import streamlit as st

    st.session_state[_STATE_KEY] = state


def get_workflow_evidence() -> list[StepResult]:
    import streamlit as st

    return st.session_state.get(_EVIDENCE_KEY, [])


def run_demo_pipeline() -> OrchestratorResult:
    """Streamlit 데모에서 호출하는 함수: 현재 세션 transcript 로 파이프라인 실행."""
    # 데이터 경로: 데모는 프로젝트 루트의 data/ 사용
    project_root = Path(__file__).resolve().parents[2]
    data_root = project_root / "data"
    inp = _load_pipeline_input(
        data_root,
        customers_json="customers.json",
        contracts_json="contracts.json",
        scoring_rules_json="scoring_rules.json",
        knowledge_dir="knowledge",
    )
    transcript_path = data_root / "demo" / "consultation-transcript.txt"
    if transcript_path.exists():
        inp.transcript_text = transcript_path.read_text(encoding="utf-8")
    return run_pipeline(inp)


# =========================================================================
# Stage 3: Tool 실행 메서드 (Mock Tool 연결)
# =========================================================================
# Orchestrator 는 Tool 을 직접 구현하지 않고 Interface 를 통해 호출한다.
# 실행 결과는 ToolExecutionResult 로 반환되며, 기존 상태 Namespace 와 분리된다.

import src.tools.interfaces as _tool_iface
from src.runtime_db import RuntimeDB


def _runtime_db(db: RuntimeDB | None = None) -> RuntimeDB:
    """주어진 DB 또는 기본 RuntimeDB 인스턴스 반환 (session_id 를 키로 사용)."""
    return db if db is not None else RuntimeDB()


def make_channel(approved_script: str, db: RuntimeDB | None = None) -> _tool_iface.ChannelGateway:
    from src.tools.mock_channel import MockChannelGateway

    return MockChannelGateway(db=db)


def start_mock_call(
    session_id: str, customer_id: str, approved_script: str, db: RuntimeDB | None = None,
) -> _tool_iface.ToolExecutionResult:
    """오늘의 1-Pick: Mock 전화 시작 (CALL_STARTED)."""
    from src.tools.mock_channel import MockChannelGateway

    gw = MockChannelGateway(db=db)
    return gw.start_call(customer_id, session_id, approved_script)


def complete_mock_call(
    session_id: str, customer_id: str, db: RuntimeDB | None = None,
) -> _tool_iface.ToolExecutionResult:
    """상담 완료: Mock 전화 종료 (CALL_COMPLETED)."""
    from src.tools.mock_channel import MockChannelGateway

    gw = MockChannelGateway(db=db)
    return gw.complete_call(customer_id, session_id)


def send_mock_sms(
    session_id: str, customer_id: str, approved_script: str, db: RuntimeDB | None = None,
) -> _tool_iface.ToolExecutionResult:
    from src.tools.mock_channel import MockChannelGateway

    gw = MockChannelGateway(db=db)
    return gw.send_sms(customer_id, session_id, approved_script)


def send_mock_kakao(
    session_id: str, customer_id: str, approved_script: str, db: RuntimeDB | None = None,
) -> _tool_iface.ToolExecutionResult:
    from src.tools.mock_channel import MockChannelGateway

    gw = MockChannelGateway(db=db)
    return gw.send_kakao(customer_id, session_id, approved_script)


def process_mock_stt(session_id: str, db: RuntimeDB | None = None) -> _tool_iface.ToolExecutionResult:
    """Mock STT: data/demo/consultation-transcript.txt 반환 (STT_COMPLETED)."""
    from src.tools.mock_stt import MockSttTool

    stt = MockSttTool(db=db)
    return stt.transcribe(session_id)


def confirm_and_execute(
    session_id: str,
    customer_id: str,
    fc_confirmed: bool,
    crm_draft: dict | None = None,
    calendar_title: str = "재상담 (Mock)",
    calendar_due_datetime: str = "",
    fc_action: str = "ACCEPTED",
    safety_result: dict | None = None,
    db: RuntimeDB | None = None,
) -> dict:
    """FC 확인 → Mock CRM 저장 → Mock Calendar 등록 → Feedback 저장.

    실행 순서:
    1. FC 확인 여부 검사
    2. FC 확인 이벤트 기록 (FC_CONFIRMED)
    3. FC 수정 CRM Draft 확보
    4. Mock CRM 저장
    5. Mock Calendar 등록
    6. Feedback 저장
    7. 각 Tool 실행 결과 반환
    """
    from src.tools.mock_crm import MockCrmTool
    from src.tools.mock_calendar import MockCalendarTool
    from src.tools.feedback_store import MockFeedbackStore

    results: dict[str, _tool_iface.ToolExecutionResult] = {}
    db = _runtime_db(db)

    # 1) FC 확인 여부 검사
    if not fc_confirmed:
        from src.tools.interfaces import ERR_FC_NOT_CONFIRMED

        return {
            "success": False,
            "results": results,
            "reason": ERR_FC_NOT_CONFIRMED,
        }

    # 2) FC 확인 이벤트 기록
    fc_rec = db.record_execution(session_id, "orchestrator", "FC_CONFIRMED", True)
    results["fc_confirmed"] = _tool_iface.ToolExecutionResult(
        execution_id=fc_rec["execution_id"],
        session_id=session_id,
        tool_name="orchestrator",
        event_type="FC_CONFIRMED",
        success=True,
        executed_at=fc_rec["executed_at"],
        result_ref=fc_rec["result_ref"],
        extra={"reused": fc_rec.get("reused", False)},
    )

    # 3) FC 수정 CRM Draft 확보
    draft = crm_draft or {}

    # 4) Mock CRM 저장
    crm = MockCrmTool(db)
    crm_res = crm.save_confirmed_draft(session_id, customer_id, draft, True)
    results["crm"] = crm_res

    # 5) Mock Calendar 등록
    if calendar_due_datetime:
        cal = MockCalendarTool(db)
        results["calendar"] = cal.schedule_confirmed_action(
            session_id, customer_id, calendar_title, calendar_due_datetime, True,
        )

    # 6) Feedback 저장
    fb = MockFeedbackStore(db)
    results["feedback"] = fb.store(
        session_id,
        fc_action=fc_action,
        original_draft=draft if fc_action == "ACCEPTED" else {"source": "agent_draft"},
        revised_draft=draft if fc_action != "ACCEPTED" else None,
        safety_result=safety_result or {},
        final_execution={k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in results.items()},
    )

    all_ok = all(r.success for r in results.values())
    return {"success": all_ok, "results": results}


def reset_demo_session(session_id: str) -> None:
    """Demo 초기화: 현재 session_id 의 Runtime Mock 데이터만 삭제한다.

    고객 Seed·Expected·Knowledge 문서는 삭제하지 않는다.
    """
    db = _runtime_db()
    db.reset_session(session_id)