"""Customer Selection Agent — 1-Pick 후보 선정(customer_selection).

POOL_SCAN → SCORING → PICK_READY 흐름에서 eligibility 와 rescue_score 를 실행한다.
- 어느 고객이 연락 가능한지(eligible), 점수(Rescue Score), 제외 사유를 판정.
- POOL_SCAN 결과 eligible 고객만 점수를 계산하고 상위 1명을 1-Pick 으로 선정.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.data_loader import Customer, Contract
from src.eligibility import EligibilityResult, classify_all
from src.rescue_score import ScoreResult, compute_score
from src.runtime_models import (
    Evidence,
    StepResult,
    WorkflowState,
)


@dataclass
class SelectionSummary:
    picked_customer: Customer | None
    picked_score: ScoreResult | None
    eligible: dict[str, EligibilityResult]
    all_scores: dict[str, ScoreResult]


def run_customer_selection(
    customers: list[Customer],
    contracts_by_customer: dict[str, list[Contract]],
    score_rules: list[dict[str, Any]],
    as_of: str,
) -> tuple[SelectionSummary, StepResult]:
    """1-Pick 후보 선정 파이프라인의 한 스텝.

    - 모든 고객 eligibility 검사
    - eligible 만 rescue score 계산
    - 최고 점수 고객 1명을 picked_customer 로 반환
    """
    elig = classify_all(customers, contracts_by_customer)
    scores: dict[str, ScoreResult] = {}
    for c in customers:
        if elig[c.customer_id].eligible:
            scores[c.customer_id] = compute_score(
                c, contracts_by_customer.get(c.customer_id, []), score_rules, as_of
            )

    picked_customer = None
    picked_score = None
    if scores:
        top_id = max(scores, key=lambda k: scores[k].total)
        picked_customer = next(c for c in customers if c.customer_id == top_id)
        picked_score = scores[top_id]

    state = WorkflowState.PICK_READY if picked_customer else WorkflowState.POOL_SCAN

    # 스텝 출력
    evidence: list[Evidence] = []
    if picked_customer and picked_score:
        evidence.append(Evidence(
            artifact_type="score_breakdown",
            source=state,
            summary=(
                f"1-Pick: {picked_customer.name}({picked_customer.customer_id}) "
                f"Rescue Score {picked_score.total}"
            ),
            payload={
                "customer_id": picked_customer.customer_id,
                "score": picked_score.total,
                "breakdown": [
                    {"rule_id": i.rule_id, "points": i.points, "evidence_text": i.evidence_text}
                    for i in picked_score.items
                ],
            },
        ))

    step = StepResult(
        state=state,
        step_name="customer_selection",
        summary=(
            f"eligible {len(scores)}/{len(customers)}, "
            f"picked={picked_customer.customer_id if picked_customer else 'NONE'}"
        ),
        evidence=evidence,
    )
    return SelectionSummary(picked_customer, picked_score, elig, scores), step


def load_contracts_by_customer(contracts: list[Contract]) -> dict[str, list[Contract]]:
    grouped: dict[str, list[Contract]] = {}
    for c in contracts:
        grouped.setdefault(c.customer_id, []).append(c)
    return grouped