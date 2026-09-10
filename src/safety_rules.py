"""Safety 규칙 — 금지 표현/YTN 대본 참고 문구를 ground truth 로부터 variant 로 감지.

docs/data-contracts.md 6.3 절 (SafetyContract):
- THREAT_PRESSURE: '~안 하면 손해', '빨리 하셔야', 심리적 압박 문구
- UNGROUNDED_CLAIM: 근거 없는 절대 보장 ('100%', '~반드시', '~무조건')
- EXAGGERATION: 과장 ('~최고', '~압도적')
금지 문구가 대본(transcript)에 등장하면 review_result.decision=REJECTED.
주의 문자열(위반 문자열)은 반환한다.
"""
from __future__ import annotations

import unicodedata
from typing import Any

from src.runtime_models import (
    SafetyCheckResult,
    SafetyViolation,
    ViolationType as SafetyViolationType,
)

# enum 값 매핑 안전장치: 코드가 바뀌어도 문자열로 비교 가능하게
_T = SafetyViolationType


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s) if s else s


def _is_grounded(evidence_refs: list[str]) -> bool:
    return bool(evidence_refs)


def _normalize_rules(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {**_r, "phrase": _nfc(str(_r.get("phrase", "")))}
        for _r in raw
        if _r.get("phrase")
    ]


def build_rule_table(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """scoring_rules.json 과 같은 형태의 safety_rules.json 을 전처리."""
    return _normalize_rules(rules)


def check_safety(
    transcript_text: str,
    rules: list[dict[str, Any]],
    evidence_refs: list[str],
) -> SafetyCheckResult:
    """대본 전체를 검사. 위반 발견 시 위반 문자열과 원인을 함께 반환."""
    text = _nfc(transcript_text or "")
    violations: list[SafetyViolation] = []
    used_rules: set[str] = set()

    def _append(vtype: SafetyViolationType, phrase: str, matched: str) -> None:
        violations.append(SafetyViolation(
            violation_type=vtype,
            phrase=phrase,
            matched_text=matched,
            evidence_refs=list(evidence_refs),
        ))

    for r in rules:
        phrase = r.get("phrase", "")
        vtype = r.get("violation_type", "")
        if vtype not in {_T.THREAT_PRESSURE, _T.UNGROUNDED_CLAIM, _T.EXAGGERATION}:
            continue
        if phrase in text:
            used_rules.add(phrase)
            _append(vtype, phrase, phrase)

    if violations:
        # 우선 필터: 근거 없는 절대 보장은 UNGROUNDED_CLAIM 으로 최우선 표시
        priority = {
            _T.UNGROUNDED_CLAIM: 0,
            _T.THREAT_PRESSURE: 1,
            _T.EXAGGERATION: 2,
        }
        violations.sort(key=lambda v: priority.get(v.violation_type, 3))
        return SafetyCheckResult(
            decision="REJECTED",
            reason="safety_violation_found",
            violations=violations,
            grounded=_is_grounded(evidence_refs),
        )

    return SafetyCheckResult(
        decision="COMPLIANT",
        reason="no_violation_found",
        violations=[],
        grounded=_is_grounded(evidence_refs),
    )


def filter_for_customer(
    rules: list[dict[str, Any]],
    customer: Any,
) -> list[dict[str, Any]]:
    """고객 민감 이력(예: 고객명) 기반 필터. MVP 는 전체 규칙 사용."""
    return rules