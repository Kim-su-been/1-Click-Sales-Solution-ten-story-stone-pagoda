"""Safety — FC 대본의 금지 표현 검사·판정.

SAFETY_CHECK 스텝: FC 대본에 금지 표현(규칙)이 있는지 검사하고
- 위반 없으면 COMPLIANT (CONTACT_READY)
- 위반 있으면 REJECTED (안전장치: 대본을 다시 작성하도록 FEEDBACK 전이)
- grounding_status 가 MISSING 이면 UNGROUNDED_CLAIM / EXAGGERATION 으로 안전장치
Grounding and Safety Agent 의 일부 로직을 담당한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.safety_rules import check_safety, build_rule_table
from src.runtime_models import (
    Evidence,
    SafetyCheckResult,
    StepResult,
    WorkflowState,
)


@dataclass
class SafetyReviewOutput:
    decision: SafetyCheckResult
    step: StepResult


def run_safety_review(
    transcript_text: str,
    rules: list[dict[str, Any]],
    evidence_refs: list[str],
) -> SafetyReviewOutput:
    rule_table = build_rule_table(rules)
    result = check_safety(transcript_text, rule_table, evidence_refs)

    state = WorkflowState.CONTACT_READY if result.decision == "COMPLIANT" else WorkflowState.FEEDBACK

    evidence = Evidence(
        artifact_type="safety_review",
        source=WorkflowState.SAFETY_CHECK,
        summary=(
            f"decision={result.decision}, violations={len(result.violations)}, "
            f"grounded={result.grounded}"
        ),
        payload={
            "decision": result.decision,
            "violations": [
                {
                    "violation_type": v.violation_type,
                    "phrase": v.phrase,
                    "matched_text": v.matched_text,
                }
                for v in result.violations
            ],
            "grounding_status": result.grounded,
        },
    )
    step = StepResult(
        state=state,
        step_name="safety_review",
        summary=evidence.summary,
        evidence=[evidence],
    )
    return SafetyReviewOutput(decision=result, step=step)