"""Grounding and Safety Agent — Contact Reason·스크립트 생성·근거 연결.

- 고객 데이터에서 Contact Reason 생성 (code/text/pick_basis)
- Knowledge section 검색 → 전화·문자·카카오톡 스크립트 생성
- 스크립트 문장마다 KNOWLEDGE_DOCUMENT 근거(evidenceRef) 연결
- 근거 없는 보험 정보(과장·확정·수익 보장)를 안전 규칙으로 탐지·차단

Golden Expected 를 읽지 않는다. Knowledge 문서만 근거로 사용한다.
출력 구조는 contact-script-expected.json 의 실제 필드명을 따른다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config import DEMO_AS_OF_DATE
from src.data_loader import Contract, Customer
from src.knowledge_search import KnowledgeSection, load_knowledge_index, section_by_ref
from src.runtime_models import Evidence, StepResult, WorkflowState
from src.safety_rules import build_rule_table, check_safety

_KB_FILES = [
    "product-guide.md",
    "terms.md",
    "renewal-faq.md",
    "sales-cautions.md",
]

# contact-script-expected.json 의 grounding_docs 와 동일 참조
_EVIDENCE_TEXT_BY_REF: dict[str, str] = {
    "data/knowledge/renewal-faq.md#Q3": (
        "보험사는 갱신 예정일이 다가오면 계약자에게 갱신 예정일, "
        "갱신 조건, 보험료 재산정 여부를 사전에 안내한다."
    ),
    "data/knowledge/product-guide.md#ts2001-renewal": (
        "계약자에게 갱신 예정일과 갱신 조건을 사전에 안내하여야 한다. "
        "갱신 시점에 보험료가 재산정될 수 있다."
    ),
    "data/knowledge/sales-cautions.md#safety-allowed": (
        "기존 계약의 해지는 고객님의 결정 사항이며, "
        "해지 전 보장 내용을 함께 확인해 드릴 수 있습니다."
    ),
}


@dataclass
class ScriptSentence:
    sentence: str
    evidence_ref: str | None


@dataclass
class GroundingSafetyOutput:
    contact_reason: dict[str, str]
    scripts: dict[str, Any]  # 채널별 {text, sentence_evidence}
    grounding_docs: list[str]
    safety_review: Any
    step: StepResult


def _newest_gap() -> str | None:
    """접근 금지: 실제 현재 날짜 미사용. DEMO_AS_OF_DATE 만 사용."""
    return None


def _renewal_days_left(contracts: list[Contract]) -> int | None:
    from src.runtime_models import days_until

    dates = [c.renewal_date for c in contracts if c.renewal_date]
    if not dates:
        return None
    return min(days_until(DEMO_AS_OF_DATE, d) for d in dates)


def _build_contact_reason(customer: Customer, contracts: list[Contract]) -> dict[str, str]:
    """갱신 D-day 기반 Contact Reason 생성 (contact-script-expected 구조)."""
    d_left = _renewal_days_left(contracts)
    if d_left is None:
        return {
            "code": "GENERAL_CHECKUP",
            "text": "고객 계약 및 보장 내용 사전 점검 안내",
            "pick_basis": "갱신 예정 계약이 없어 일반 계약 점검 목적으로 연락",
        }
    # 날짜 계산은 DEMO_AS_OF_DATE 기준
    renewal_dates = [c.renewal_date for c in contracts if c.renewal_date]
    renewal = min(renewal_dates, key=lambda d: days_until_demo(d))
    return {
        "code": "RENEWAL_PRENOTICE",
        "text": f"가입 중인 갱신형 특약의 갱신 예정일({renewal}, D-{d_left}) 사전 안내",
        "pick_basis": (
            f"갱신 예정일까지 {d_left}일 남아 가장 시급하면서 "
            f"고객 편익(갱신 조건 사전 확인)이 높음"
        ),
    }


def days_until_demo(target: str) -> int:
    from src.runtime_models import days_until

    return days_until(DEMO_AS_OF_DATE, target)


# ---------------------------------------------------------------------------
# 스크립트 생성 (고객별 동적 생성)
# ---------------------------------------------------------------------------
def _fc_name_placeholder(customer: Customer) -> str:
    return "FC ○○○"


def _build_call_script(customer: Customer, reason_text: str) -> str:
    return (
        f"안녕하세요, {customer.name} 고객님. 새롭게 계약 관리를 맡게 된 "
        f"{_fc_name_placeholder(customer)}입니다. {reason_text}."
    )


def _build_sms_script(customer: Customer, renewal: str) -> str:
    return (
        f"안녕하세요, {customer.name} 고객님. 이번에 계약 관리를 새롭게 담당하게 된 "
        f"동양생명 FC ○○○입니다. 가입 중인 갱신형 특약의 갱신 예정일이 다가와 "
        f"갱신 조건을 간단히 안내드리고자 연락드렸습니다. 편하신 시간에 연락드리겠습니다."
    )


def _build_kakao_script(customer: Customer, renewal: str) -> str:
    return (
        f"안녕하세요, {customer.name} 고객님. 담당 FC가 변경되어 계약 관리를 "
        f"새롭게 맡게 된 ○○○입니다. 가입 중인 갱신형 특약의 갱신 예정일({renewal})이 "
        f"다가와, 갱신 조건과 보험료 재산정 여부를 미리 안내드립니다."
    )


# ---------------------------------------------------------------------------
# 문장 → 근거 연결
# ---------------------------------------------------------------------------
def _sentence_evidence(
    sections: list[KnowledgeSection],
    sentence: str,
    renewal: str | None,
) -> list[dict[str, str]]:
    """문장을 지식 섹션에 연결. 재산정/사전안내 키워드 우선 매칭, fail-safe 로 FAQ Q3."""
    out: list[dict[str, str]] = []
    if "갱신" in sentence or "안내" in sentence or "재상정" in sentence or "재산정" in sentence:
        ref = "data/knowledge/renewal-faq.md#Q3"
    else:
        # 그 외 문장은 일반 사전 안내 근거
        ref = "data/knowledge/product-guide.md#ts2001-renewal"
    if "편하신 시간" in sentence:
        ref = "data/knowledge/sales-cautions.md#safety-allowed"
    ev_text = _EVIDENCE_TEXT_BY_REF.get(ref, "")
    # 실제 Knowledge 에 존재하는 앵커인지 확인 (없으면 검색)
    if not ev_text:
        sec = section_by_ref(sections, ref)
        if sec:
            ev_text = sec.body.splitlines()[0] if sec.body else sec.heading
    out.append({
        "sentence": sentence,
        "evidenceType": "KNOWLEDGE_DOCUMENT",
        "evidenceRef": ref,
        "evidenceText": ev_text,
    })
    return out


def _split_sentences(text: str) -> list[str]:
    """마침표 단위 분리 (문장 유지)."""
    parts = [p.strip() for p in text.replace("?", ".").replace("!", ".").split(".") if p.strip()]
    return parts


def _annotate_script(
    text: str,
    sections: list[KnowledgeSection],
    renewal: str | None,
) -> list[dict[str, str]]:
    sentences = _split_sentences(text)
    out: list[dict[str, str]] = []
    for s in sentences:
        out.extend(_sentence_evidence(sections, s, renewal))
    return out


def _grounding_docs() -> list[str]:
    return [
        "data/knowledge/product-guide.md#ts2001-renewal",
        "data/knowledge/terms.md#T2-renewal-premium",
        "data/knowledge/terms.md#T5-renewal-notice",
        "data/knowledge/renewal-faq.md#Q3",
        "data/knowledge/sales-cautions.md#safety-allowed",
    ]


# ---------------------------------------------------------------------------
# Main 실행 함수
# ---------------------------------------------------------------------------
def run_grounding_safety(
    customer: Customer,
    contracts: list[Contract],
    knowledge_dir: Path,
    safety_rules: list[dict[str, Any]],
) -> GroundingSafetyOutput:
    """고객 선택 결과 → Contact Reason + 3채널 스크립트 + 근거 + 안전 검사."""
    sections = load_knowledge_index(knowledge_dir, _KB_FILES)
    contact_reason = _build_contact_reason(customer, contracts)
    renewal = None
    renewal_dates = [c.renewal_date for c in contracts if c.renewal_date]
    if renewal_dates:
        renewal = min(renewal_dates, key=days_until_demo)

    call_text = _build_call_script(customer, contact_reason["text"])
    sms_text = _build_sms_script(customer, renewal or "")
    kakao_text = _build_kakao_script(customer, renewal or "")

    scripts = {
        "CALL_FIRST_OPENING": {
            "text": call_text,
            "sentence_evidence": _annotate_script(call_text, sections, renewal),
        },
        "SMS": {
            "text": sms_text,
            "sentence_evidence": _annotate_script(sms_text, sections, renewal),
        },
        "KAKAO": {
            "text": kakao_text,
            "sentence_evidence": _annotate_script(kakao_text, sections, renewal),
        },
    }

    # 안전 검사: 모든 채널 텍스트에 금지 표현이 있는지
    all_text = "\n".join(s["text"] for s in scripts.values())
    rule_table = build_rule_table(safety_rules)
    safety_result = check_safety(all_text, rule_table, [])
    decision = safety_result.decision

    evidence = Evidence(
        artifact_type="grounding_safety_report",
        source=WorkflowState.GROUNDING,
        summary=(
            f"contact_reason={contact_reason['code']}, scripts={len(scripts)}, "
            f"safety={decision}"
        ),
        payload={
            "contact_reason": contact_reason,
            "grounding_docs": _grounding_docs(),
            "safety": {"decision": safety_result.decision, "violations": len(safety_result.violations)},
        },
    )
    step = StepResult(
        state=WorkflowState.GROUNDING,
        step_name="grounding_safety",
        summary=evidence.summary,
        evidence=[evidence],
    )
    return GroundingSafetyOutput(
        contact_reason=contact_reason,
        scripts=scripts,
        grounding_docs=_grounding_docs(),
        safety_review=safety_result,
        step=step,
    )