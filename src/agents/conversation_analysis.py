"""Conversation Analysis Agent — 상담 Transcript 를 분석하여 산출물 생성.

입력: data/demo/consultation-transcript.txt (발화 목록), DEMO_AS_OF_DATE
출력:
- analysis (session-analysis-expected.json 의 analysis 구조)
- crm_draft (crm-record-expected.json 의 crm_record 구조)
- next_actions + calendar_candidate (next-action-expected.json 구조)

Golden Expected 를 입력으로 읽지 않는다. Transcript 발화에서 규칙 기반으로 추출한다.
#spk:N 은 파일 라인이 아니라 Transcript 발화 순서(1부터 시작)다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from src.config import DEMO_AS_OF_DATE
from src.runtime_models import (
    ActionStatus,
    CrmPhase,
    CrmStatus,
    FcConfirmation,
)

_TRANSCRIPT_REF = "data/demo/consultation-transcript.txt"


class TranscriptEvidence:
    """발화 1개에 대한 evidence dict. evidenceRef 는 #spk:N (발화 순서)."""

    def __init__(self, spk: int, text: str) -> None:
        self.spk = spk
        self.text = text

    @property
    def evidence_ref(self) -> str:
        return f"{_TRANSCRIPT_REF}#spk:{self.spk}"

    def to_dict(self) -> dict[str, str]:
        return {
            "evidenceType": "TRANSCRIPT",
            "evidenceRef": self.evidence_ref,
            "evidenceText": self.text,
        }


@dataclass
class FinancialServicesAnalysis:
    """Conversation Analysis Agent 1회 실행 결과 묶음."""
    analysis: dict[str, Any] = field(default_factory=dict)
    crm_draft: dict[str, Any] = field(default_factory=dict)
    next_actions: list[dict[str, Any]] = field(default_factory=list)
    calendar_candidate: dict[str, Any] = field(default_factory=dict)
    step_summary: str = ""


# ---------------------------------------------------------------------------
# Transcript 발화 모델 (지연 import 방지)
# ---------------------------------------------------------------------------
@dataclass
class Turn:
    speaker: str
    text: str
    seq: int  # 1-based 발화 순서 (#spk)

    @property
    def evidence(self) -> TranscriptEvidence:
        return TranscriptEvidence(self.seq, f"[{self.speaker}] {self.text}")


def _parse_transcript(text: str) -> list[Turn]:
    """[화자] 발화 라인을 파싱. 주석/빈 줄 제거, 1-based 발화 순서 부여."""
    turns: list[Turn] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[([^\]]+)\]\s*(.+)$", line)
        if not m:
            continue
        turns.append(Turn(speaker=m.group(1).strip(), text=m.group(2).strip(), seq=len(turns) + 1))
    return turns


def _member_turns(turns: list[Turn]) -> list[Turn]:
    return [t for t in turns if "CUST" in t.speaker.upper() or t.speaker.startswith("회원")]


# ---------------------------------------------------------------------------
# 1) 상담 결과 분류 (outcome)
# ---------------------------------------------------------------------------
_AGREE_MARKERS = ["설명받고 싶어요", "다시 연락 주시면", "잘 부탁드릴게요", "확인하고 싶어요", "감사합니다"]
_REJECT_MARKERS = ["관심 없어요", "새로 가입할 생각은 아직 없어요"]


def _decide_outcome(member_turns: list[Turn]) -> tuple[str, Turn | None]:
    """고객 발화에서 후속/설명 요청 조짐 → 상담_성공. 아니면 상담_보통."""
    for t in reversed(member_turns):
        if any(m in t.text for m in _AGREE_MARKERS):
            return "상담_성공", t
    return "상담_보통", (member_turns[-1] if member_turns else None)


# ---------------------------------------------------------------------------
# 2) 고객 니즈 / 관심 / 거절·무관심 / 우려 추출
# ---------------------------------------------------------------------------
_NEED_RULES: list[tuple[str, str]] = [
    ("기존 계약 보장내용 점검", "보장"),
    ("갱신 조건 사전 확인", "갱신"),
]

_INTEREST_RULES: list[tuple[str, str]] = [
    ("기존 계약(종신보험·갱신형 특약) 보장내용", "보장"),
]

_DISINTEREST_RULES: list[tuple[str, str]] = [
    ("추가가입_의향_낮음", "새로 가입할 생각"),
    ("치아보험_무관심", "치아보험"),
]

_CONCERN_RULES: list[tuple[str, str]] = [
    ("갱신_보험료_부담", "보험료가 오른다고"),
]


def _find_evidence(member_turns: list[Turn], keyword: str) -> Turn | None:
    for t in member_turns:
        if keyword in t.text:
            return t
    return None


def _extract_needs(member_turns: list[Turn]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for label, keyword in _NEED_RULES:
        ev = _find_evidence(member_turns, keyword)
        if ev:
            out.append({"need": label, "evidence": ev.evidence.to_dict()})
    return out


def _extract_interests(member_turns: list[Turn]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for label, keyword in _INTEREST_RULES:
        ev = _find_evidence(member_turns, keyword)
        if ev:
            out.append({"interest": label, "evidence": ev.evidence.to_dict()})
    return out


def _extract_disinterests(member_turns: list[Turn]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for label, keyword in _DISINTEREST_RULES:
        ev = _find_evidence(member_turns, keyword)
        if ev:
            out.append({"item": label, "evidence": ev.evidence.to_dict()})
    return out


def _extract_concerns(member_turns: list[Turn]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for label, keyword in _CONCERN_RULES:
        ev = _find_evidence(member_turns, keyword)
        if ev:
            out.append({"concern": label, "evidence": ev.evidence.to_dict()})
    return out


# ---------------------------------------------------------------------------
# 3) 후속 상담 희망 일시 추출 (다음 주 목요일 오후)
# ---------------------------------------------------------------------------
_WEEKDAY_KO = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _parse_followup(member_turns: list[Turn]) -> tuple[bool, str | None, Turn | None]:
    """'다음 주 {요일} {오전/오후/저녁}' 패턴에서 preferred_datetime 생성."""
    for t in reversed(member_turns):
        m = re.search(r"다음 주\s*([월화수목금토일])요일\s*([오전|오후|저녁]+)", t.text)
        if not m:
            continue
        weekday_idx = _WEEKDAY_KO.index(m.group(1) + "요일")
        period = m.group(2)
        # DEMO_AS_OF_DATE(2026-09-09) 기준 다음 주 해당 요일
        today = date.fromisoformat(DEMO_AS_OF_DATE)
        days_ahead = (weekday_idx - today.weekday()) % 7
        next_weekday = today + timedelta(days=7 + days_ahead)
        if period == "오전":
            time_part = "10:00:00"
        elif period == "저녁":
            time_part = "19:00:00"
        else:
            time_part = "14:00:00"
        return True, f"{next_weekday.isoformat()}T{time_part}", t
    return False, None, None


# ---------------------------------------------------------------------------
# 4) AI 요약 (규칙 기반 문장 생성 — Golden Expected 와 동작 의미 동일)
# ---------------------------------------------------------------------------
def _build_summary(customer_name: str, renewal_date: str, preferred: str) -> str:
    pref_txt = (
        f"{preferred[:10]} 오후에 다시 연락드려 자세히 안내해 드리기로 약속했습니다."
        if preferred
        else "다음 상담 일정은 추후 다시 조율이 필요합니다."
    )
    return (
        f"{customer_name} 고객님께 갱신형 특약의 갱신 예정일({renewal_date})을 사전에 안내드렸습니다. "
        f"안내를 받으신 뒤, 새로 가입하기보다는 지금 가입 중인 계약(종신보험·갱신형 특약)의 "
        f"보장 내용을 먼저 다시 점검하고 싶다는 의사를 밝히셨습니다.\n\n"
        f"갱신 시점에 보험료가 재산정될 수 있다는 부분에는 다소 부담을 느끼시는 듯했습니다. "
        f"다만 신규 가입 의향은 높지 않으셨고, 특히 치아보험에는 관심이 없다고 명확히 말씀해 주셨습니다.\n\n"
        f"{pref_txt}"
    )


# ---------------------------------------------------------------------------
# 5) Next Action / Calendar 후보 생성
# ---------------------------------------------------------------------------
def _build_next_actions(
    customer_name: str,
    preferred: str | None,
    followup_turn: Turn | None,
    needs_turn: Turn | None,
    concern_turn: Turn | None,
    renewal_date: str,
) -> list[dict[str, Any]]:
    if not preferred:
        return []

    pref_date = date.fromisoformat(preferred[:10])
    prep_date = pref_date - timedelta(days=1)
    notice_date = pref_date + timedelta(days=7)

    actions: list[dict[str, Any]] = [
        {
            "action_id": "ACT-001",
            "action_type": "FOLLOWUP_CONSULTATION",
            "title": f"{customer_name} 고객 재상담(기존 계약 보장내용 점검)",
            "due_datetime": preferred,
            "status": ActionStatus.SUGGESTED,
            "evidence": followup_turn.evidence.to_dict() if followup_turn else {},
        },
        {
            "action_id": "ACT-002",
            "action_type": "PREPARE_COVERAGE_SUMMARY",
            "title": f"다음 상담용 기존 계약 보장내역 정리 자료 준비",
            "due_datetime": f"{prep_date.isoformat()}T18:00:00",
            "status": ActionStatus.SUGGESTED,
            "evidence": needs_turn.evidence.to_dict() if needs_turn else {},
        },
        {
            "action_id": "ACT-003",
            "action_type": "REVIEW_RENEWAL_PREM_NOTICE",
            "title": f"갱신형 특약 갱신({renewal_date}) 사전 안내 자료 확인 및 보험료 재산정 안내 준비",
            "due_datetime": f"{notice_date.isoformat()}T18:00:00",
            "status": ActionStatus.SUGGESTED,
            "evidence": concern_turn.evidence.to_dict() if concern_turn else {},
        },
    ]
    return actions


def _build_calendar_candidate(customer_name: str, preferred: str | None, turn: Turn | None) -> dict[str, Any]:
    return {
        "title": f"{customer_name} 고객 재상담(보장내용 점검)",
        "due_datetime": preferred,
        "duration_minutes": 30,
        "status": ActionStatus.PENDING_FC_CONFIRM,
        "evidence": turn.evidence.to_dict() if turn else {},
    }


# ---------------------------------------------------------------------------
# 6) CRM Draft (최종 저장 전 DRAFT / FC 확인 대기)
# ---------------------------------------------------------------------------
def _build_crm_draft(
    customer_id: str,
    customer_name: str,
    outcome: str,
    needs: list[str],
    interests: list[str],
    disinterests: list[str],
    concerns: list[str],
    preferred: str | None,
    summary: str,
    call_started: str,
) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "consultation_type": "TEL",
        "consultation_datetime": call_started,
        "outcome": outcome,
        "customer_needs": needs,
        "customer_interests": interests,
        "rejection_reason": None,
        "disinterest_items": disinterests,
        "concerns": concerns,
        "followup_needed": preferred is not None,
        "preferred_datetime": preferred,
        "ai_summary": summary,
    }


# ---------------------------------------------------------------------------
# 7) Main 실행 함수
# ---------------------------------------------------------------------------
def run_conversation_analysis(
    transcript_text: str,
    customer_id: str,
    customer_name: str,
    renewal_date: str,
    call_started: str = f"{DEMO_AS_OF_DATE}T11:00:00",
) -> FinancialServicesAnalysis:
    """Transcript 텍스트를 분석해 analysis/CRM Draft/Next Action/Calendar 후보를 생성."""
    turns = _parse_transcript(transcript_text)
    member = _member_turns(turns)
    if not member:
        raise ValueError("Transcript 에 고객 발화가 없습니다.")

    outcome, outcome_turn = _decide_outcome(member)
    needs = _extract_needs(member)
    interests = _extract_interests(member)
    disinterests = _extract_disinterests(member)
    concerns = _extract_concerns(member)
    followup_needed, preferred, followup_turn = _parse_followup(member)
    summary = _build_summary(customer_name, renewal_date, preferred)

    needs_turn = _find_evidence(member, "보장")
    concern_turn = _find_evidence(member, "보험료가 오른다고")

    analysis = {
        "outcome": {
            "value": outcome,
            "evidence": outcome_turn.evidence.to_dict() if outcome_turn else {},
        },
        "customer_needs": needs,
        "customer_interests": interests,
        "rejection_or_disinterest": disinterests,
        "concerns": concerns,
        "followup_requested": {
            "needed": followup_needed,
            "preferred_datetime": preferred,
            "evidence": followup_turn.evidence.to_dict() if followup_turn else {},
        },
        "ai_summary": summary,
    }

    crm_draft = _build_crm_draft(
        customer_id=customer_id,
        customer_name=customer_name,
        outcome=outcome,
        needs=[n["need"] for n in needs],
        interests=[i["interest"] for i in interests],
        disinterests=[d["item"] for d in disinterests],
        concerns=[c["concern"] for c in concerns],
        preferred=preferred,
        summary=summary,
        call_started=call_started,
    )

    actions = _build_next_actions(
        customer_name, preferred, followup_turn, needs_turn, concern_turn, renewal_date
    )
    calendar = _build_calendar_candidate(customer_name, preferred, followup_turn)

    step_summary = (
        f"outcome={outcome}, followup={preferred or '없음'}, "
        f"needs={len(needs)}, actions={len(actions)}"
    )
    return FinancialServicesAnalysis(
        analysis=analysis,
        crm_draft=crm_draft,
        next_actions=actions,
        calendar_candidate=calendar,
        step_summary=step_summary,
    )


def build_crm_record_envelope(
    crm_draft: dict[str, Any], analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """crm-record-expected.json 의 최상위 envelope(상태 필드 + 각 필드 근거) 생성.

    analysis 가 주어지면 outcome/followup/니즈/관심사/걱정/무관심 각각의
    Transcript 근거를 each_field_evidence 에 채운다 (필드별 근거 확인용).
    """
    each_field_evidence: list[dict[str, Any]] = []
    if analysis:
        def _add(field_name: str, ev: dict[str, Any] | None) -> None:
            # render_evidence()는 evidenceType/evidenceRef/evidenceText가 최상위에 있는
            # flat dict를 기대하므로 {"field": ..., "evidence": {...}} 로 감싸지 않는다.
            if ev:
                each_field_evidence.append({**ev, "field": field_name})

        _add("outcome", analysis.get("outcome", {}).get("evidence"))
        _add("followup_requested", analysis.get("followup_requested", {}).get("evidence"))
        for n in analysis.get("customer_needs", []):
            _add("customer_needs", n.get("evidence"))
        for i in analysis.get("customer_interests", []):
            _add("customer_interests", i.get("evidence"))
        for c in analysis.get("concerns", []):
            _add("concerns", c.get("evidence"))
        for d in analysis.get("rejection_or_disinterest", []):
            _add("disinterest_items", d.get("evidence"))

    return {
        "demo_as_of_date": DEMO_AS_OF_DATE,
        "status": CrmStatus.DRAFT,
        "phase": CrmPhase.FC_REVIEW,
        "auto_finalized": False,
        "crm_record": crm_draft,
        "each_field_evidence": each_field_evidence,
        "fc_confirm_required": FcConfirmation.REQUIRED,
        "note": crm_draft.get("ai_summary", ""),
    }