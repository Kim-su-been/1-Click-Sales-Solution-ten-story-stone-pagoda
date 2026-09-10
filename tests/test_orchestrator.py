"""Gate 4: Orchestrator 테스트.

- 정상 순서 호출 → DONE
- 잘못된 순서 차단 (is_valid_transition)
- Agent 실패 처리 (no_eligible_candidate)
- Agent 간 Output 전달 (selection → grounding → analysis)
- CRM Draft 생성 후 FC 확인 대기
- Workflow 상태와 업무 데이터 상태 분리 (WorkflowState vs CrmStatus)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.runtime_models import (
    WorkflowState,
    CrmStatus,
    CrmPhase,
    ActionStatus,
    is_valid_transition,
)
from src.agents.orchestrator import run_demo_pipeline, _load_pipeline_input, run_pipeline

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def inp():
    return _load_pipeline_input(ROOT / "data")


class TestOrchestrator:
    def test_normal_flow_to_done(self, inp):
        # 정상 transcript 로드하여 전체 파이프라인 DONE
        transcript = (ROOT / "data" / "demo" / "consultation-transcript.txt").read_text(encoding="utf-8")
        inp.transcript_text = transcript
        result = run_pipeline(inp)
        assert result.output.workflow_state == WorkflowState.DONE
        assert result.output.errors == []
        assert result.output.daily_pick["score"] == 90

    def test_agent_outputs_propagate(self, inp):
        transcript = (ROOT / "data" / "demo" / "consultation-transcript.txt").read_text(encoding="utf-8")
        inp.transcript_text = transcript
        result = run_pipeline(inp)
        # Grounding/안전 결과가 다음 단계로 전달됨
        assert result.output.script_result["contact_reason"]["code"] == "RENEWAL_PRENOTICE"
        assert result.output.analysis_result["outcome"]["value"] == "상담_성공"
        assert result.output.crm_draft["status"] == CrmStatus.DRAFT
        assert result.output.next_action_result["calendar_candidate"]["status"] == ActionStatus.PENDING_FC_CONFIRM

    def test_invalid_transition_blocked(self):
        # 건너뛰기 금지
        assert not is_valid_transition(WorkflowState.IDLE, WorkflowState.SCORING)
        assert not is_valid_transition(WorkflowState.PICK_READY, WorkflowState.SAFETY_CHECK)

    def test_workflow_state_separate_from_business_state(self, inp):
        transcript = (ROOT / "data" / "demo" / "consultation-transcript.txt").read_text(encoding="utf-8")
        inp.transcript_text = transcript
        result = run_pipeline(inp)
        # WorkflowState(실행 단계)와 CRM 상태(업무 데이터)는 별도
        assert result.output.workflow_state == WorkflowState.DONE
        assert result.output.crm_draft["status"] == CrmStatus.DRAFT
        assert result.output.crm_draft["phase"] == CrmPhase.FC_REVIEW

    def test_safety_reject_leads_feedback(self, inp):
        rejected = (
            "지금 바꾸지 않으면 보장이 크게 줄어듭니다. "
            "이 상품은 보험료가 절대 오르지 않습니다."
        )
        result = run_pipeline(inp, saved_transcript=rejected)
        assert result.output.workflow_state == WorkflowState.FEEDBACK

    def test_no_eligible_candidate_reports_error(self, inp):
        # 모든 고객을 ineligible 로 만든 가짜 입력 → no_eligible_candidate
        from src.data_loader import Customer

        cust = Customer(
            customer_id="X-001", name="테스트", birth_year=1990, sex="F", phone="010-0000-0000",
            consent_channels=[], active_complaint=False, complaint_detail=None,
            fc_id="FC-001", previous_fc_id=None, fc_changed_at=None,
            last_contacted_at=None, last_consultation_at=None,
        )
        dummy = type(inp)(customers=[cust], contracts=[], score_rules=inp.score_rules,
                          safety_rules=inp.safety_rules, knowledge_dir=inp.knowledge_dir)
        result = run_pipeline(dummy)
        assert result.output.errors
        assert any(e.agent == "customer_selection" and "no_eligible" in e.reason for e in result.output.errors)

    def test_demo_pipeline_done(self):
        result = run_demo_pipeline()
        assert result.output.workflow_state == WorkflowState.DONE
        assert result.output.daily_pick["customer_id"] == "CUST-001"