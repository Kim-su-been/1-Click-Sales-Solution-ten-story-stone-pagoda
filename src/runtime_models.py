"""Runtime 모델 — Stage 2 Status Contract 에 따른 상태 상수·데이터 구조.

docs/data-contracts.md 의 "Runtime Status Contract"(8절)를 코드로 옮긴다.
영역별 상태는 각각 별도 Namespace(cluster)의 상수로 유지한다.
(서로 다른 영역을 하나의 Enum/상수로 합치지 않음)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


# ============================================================
# 8.2 Streamlit 화면 상태 (Screen)
# ============================================================
class Screen:
    DAILY_PICK = "DAILY_PICK"
    CONSULTATION = "CONSULTATION"
    CLOSING = "CLOSING"


# ============================================================
# 8.1 Orchestrator Workflow State (WorkflowState)
# ============================================================
class WorkflowState:
    IDLE = "IDLE"
    POOL_SCAN = "POOL_SCAN"
    SCORING = "SCORING"
    PICK_READY = "PICK_READY"
    GROUNDING = "GROUNDING"
    SAFETY_CHECK = "SAFETY_CHECK"
    CONTACT_READY = "CONTACT_READY"
    TRANSCRIPT_READY = "TRANSCRIPT_READY"
    ANALYSIS = "ANALYSIS"
    CRM_DRAFT = "CRM_DRAFT"
    NEXT_ACTION = "NEXT_ACTION"
    FEEDBACK = "FEEDBACK"
    DONE = "DONE"


# ============================================================
# 8.3 Grounding/Safety 판정 상태 (SafetyDecision)
# ============================================================
class SafetyDecision:
    COMPLIANT = "COMPLIANT"
    REJECTED = "REJECTED"


class ViolationType:
    THREAT_PRESSURE = "THREAT_PRESSURE"
    UNGROUNDED_CLAIM = "UNGROUNDED_CLAIM"
    EXAGGERATION = "EXAGGERATION"


class GroundingStatus:
    GROUNDED = "GROUNDED"
    MISSING = "MISSING"


# ============================================================
# 8.4 CRM Record 상태 (CrmStatus / CrmPhase — 별도 관리)
# ============================================================
class CrmStatus:
    DRAFT = "DRAFT"
    # SAVED 는 이후 Mock Tool 단계에서만 사용 (MVP 에서는 DRAFT 만)

class CrmPhase:
    FC_REVIEW = "FC_REVIEW"


# ============================================================
# 8.5 FC Review / Confirmation 상태 (FcConfirmation)
# ============================================================
class FcConfirmation:
    REQUIRED = True
    CONFIRM = "CONFIRM"
    EDIT = "EDIT"


# ============================================================
# 8.6 Calendar / Next Action 상태 (ActionStatus)
# ============================================================
class ActionStatus:
    SUGGESTED = "SUGGESTED"
    PENDING_FC_CONFIRM = "PENDING_FC_CONFIRM"


# ============================================================
# 1. Evidence 모델 (공통)
# ============================================================
class EvidenceType:
    CUSTOMER_DATA = "CUSTOMER_DATA"
    KNOWLEDGE_DOCUMENT = "KNOWLEDGE_DOCUMENT"
    TRANSCRIPT = "TRANSCRIPT"
    EXECUTION_LOG = "EXECUTION_LOG"  # 런타임 이력용 (Stage 2 expected 근거로 사용 금지)


def make_evidence(evidence_type: str, evidence_ref: str, evidence_text: str) -> dict[str, str]:
    """evidenceType/evidenceRef/evidenceText 3종 구조 생성."""
    return {
        "evidenceType": evidence_type,
        "evidenceRef": evidence_ref,
        "evidenceText": evidence_text,
    }


# ============================================================
# 날짜 계산 (DEMO_AS_OF_DATE 기준, 시스템 현재 날짜 사용 금지)
# ============================================================
def days_until(as_of: str, target: str | None) -> int | None:
    if not target:
        return None
    return (date.fromisoformat(target) - date.fromisoformat(as_of)).days


def months_elapsed(as_of: str, past: str | None) -> int | None:
    """과거 시점(past)이 기준일(as_of)로부터 몇 개월 지났는지.

    보험 도메인 규칙(R1/R2/R4)과 daily_pick_expected 의 계산과 일치시키기 위해
    '연(年)과 월(月) 차이'로 계산한다 (일자 차이는 사용하지 않음).
    """
    if not past:
        return None
    d_past = date.fromisoformat(past)
    d_asof = date.fromisoformat(as_of)
    return (d_asof.year - d_past.year) * 12 + (d_asof.month - d_past.month)


# ============================================================
# Agent 실행 로그/오류 모델
# ============================================================
@dataclass
class AgentError:
    agent: str
    reason: str


@dataclass
class RuntimeResult:
    """Orchestrator 가 한 사이클 동안 생성한 최종 산출물 묶음(순수 데이터)."""
    daily_pick: dict[str, Any] = field(default_factory=dict)
    script_result: dict[str, Any] = field(default_factory=dict)
    analysis_result: dict[str, Any] = field(default_factory=dict)
    crm_draft: dict[str, Any] = field(default_factory=dict)
    next_action_result: dict[str, Any] = field(default_factory=dict)
    workflow_state: str = WorkflowState.IDLE
    errors: list[AgentError] = field(default_factory=list)


# ============================================================
# 8.1 Workflow 전이 테이블 (잘못된 순서 호출 차단용)
# ============================================================
WORKFLOW_ORDER: list[str] = [
    WorkflowState.POOL_SCAN,
    WorkflowState.SCORING,
    WorkflowState.PICK_READY,
    WorkflowState.GROUNDING,
    WorkflowState.SAFETY_CHECK,
    WorkflowState.CONTACT_READY,
    WorkflowState.TRANSCRIPT_READY,
    WorkflowState.ANALYSIS,
    WorkflowState.CRM_DRAFT,
    WorkflowState.NEXT_ACTION,
    WorkflowState.FEEDBACK,
    WorkflowState.DONE,
]


def is_valid_transition(current: str, next_state: str) -> bool:
    """정상 순서의 다음 상태인지 검사. 중복 호출이나 건너뜀 방지."""
    if current == WorkflowState.IDLE:
        return next_state == WorkflowState.POOL_SCAN
    if current == WorkflowState.CONTACT_READY:
        # 연락 준비 후 transcript 대기/분석 진입
        return next_state in (WorkflowState.TRANSCRIPT_READY, WorkflowState.ANALYSIS)
    if current == WorkflowState.NEXT_ACTION:
        # FEEDBACK 은 오류/재작성 상태이므로 정상 사이클에서는 건너뛰어 DONE 으로
        return next_state == WorkflowState.DONE
    try:
        return WORKFLOW_ORDER.index(next_state) == WORKFLOW_ORDER.index(current) + 1
    except ValueError:
        return False


# ============================================================
# Evidence / 실행 스텝 / 상태 전이 보조 데이터 클래스
# ============================================================
@dataclass
class Evidence:
    """한 실행 스텝이 남기는 근거 묶음.

    artifact_type: EvidenceType 기반 문자열 (score_breakdown, grounding_report, safety_review 등)
    source: 해당 스텝의 WorkflowState
    summary: 사람이 읽는 한 줄 요약
    payload: 기계 판독용 dict (JSON 직렬화 가능해야 함)
    """
    artifact_type: str
    source: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """customer_selection / grounding / safety 등 각 에이전트 스텝의 결과 합계."""
    state: str
    step_name: str
    summary: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class Turn:
    """전화 대본의 발화 하나 (transcript_parser 산출물)."""
    speaker: str
    text: str
    seq: int


# ============================================================
# Safety 검토 결과 (6.3 SafetyContract)
# ============================================================
@dataclass
class SafetyViolation:
    violation_type: str  # ViolationType.THREAT_PRESSURE / UNGROUNDED_CLAIM / EXAGGERATION
    phrase: str          # 위반 규칙의 원문 문구
    matched_text: str    # 대본에서 실제로 매칭된 문자열
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class SafetyCheckResult:
    """safety_rules.check_safety() 의 반환값 (기존 SafetyDecision 상수와 별개)."""
    decision: str  # SafetyDecision.COMPLIANT / REJECTED
    reason: str
    violations: list[SafetyViolation] = field(default_factory=list)
    grounded: bool = False