"""Rescue Score 계산 — scoring_rules.json 의 R1~R5 규칙을 DEMO_AS_OF_DATE 기준으로 계산.

docs/data-contracts.md 2.3 절:
- R1a +25 / R1b +20 (배타) · R2 +30 · R3a +25 / R3b +20 (배타) · R4 +15 · R5 +3
- 보험료 금액(월 보험료)은 어떤 규칙에도 사용하지 않는다.
- 고객 이름/ID 로 점수를 하드코딩하지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.data_loader import Contract, Customer
from src.runtime_models import days_until, months_elapsed


@dataclass
class ScoreBreakdownItem:
    rule_id: str
    name_kr: str
    points: int
    evidence_text: str


@dataclass
class ScoreResult:
    total: int
    items: list[ScoreBreakdownItem]


def _rule_lookup(points_rules: list[dict[str, Any]], rule_id: str) -> dict[str, Any] | None:
    for r in points_rules:
        if r.get("rule_id") == rule_id:
            return r
    return None


def _rule_condition(points_rules: list[dict[str, Any]], rule_id: str) -> int | None:
    rule = _rule_lookup(points_rules, rule_id)
    return int(rule.get("points", 0)) if rule else None


def _rule_name_kr(points_rules: list[dict[str, Any]], rule_id: str) -> str:
    rule = _rule_lookup(points_rules, rule_id)
    return rule.get("name_kr", rule_id) if rule else rule_id


def compute_score(
    customer: Customer,
    contracts: list[Contract],
    score_rules: list[dict[str, Any]],
    as_of: str,
) -> ScoreResult:
    """Eligible 고객 한 명의 Rescue Score 와 breakdown 을 계산."""
    items: list[ScoreBreakdownItem] = []
    total = 0

    # --- R1: FC 변경 후 경과 개월 (R1a/R1b 배타) ---
    fc_months = months_elapsed(as_of, customer.fc_changed_at)
    if customer.previous_fc_id and fc_months is not None:
        if fc_months <= 3:
            pts = _rule_condition(score_rules, "R1a")
            if pts:
                items.append(ScoreBreakdownItem(
                    "R1a", _rule_name_kr(score_rules, "R1a"), pts,
                    f"fc_changed_at={customer.fc_changed_at} 기준 {fc_months}개월 경과(3개월 이내)",
                ))
                total += pts
        elif fc_months <= 12:
            pts = _rule_condition(score_rules, "R1b")
            if pts:
                items.append(ScoreBreakdownItem(
                    "R1b", _rule_name_kr(score_rules, "R1b"), pts,
                    f"fc_changed_at={customer.fc_changed_at} 기준 {fc_months}개월 경과(3개월 초과~12개월 이내)",
                ))
                total += pts

    # --- R2: 최근 접촉 후 12개월 이상 ---
    contact_months = months_elapsed(as_of, customer.last_contacted_at)
    if contact_months is not None and contact_months >= 12:
        pts = _rule_condition(score_rules, "R2")
        if pts:
            items.append(ScoreBreakdownItem(
                "R2", _rule_name_kr(score_rules, "R2"), pts,
                f"last_contacted_at={customer.last_contacted_at} 기준 {contact_months}개월 경과(12개월 이상)",
            ))
            total += pts

    # --- R3: 특약 갱신일까지 D-day (R3a/R3b 배타) ---
    renewal_dates = [c.renewal_date for c in contracts if c.renewal_date]
    if renewal_dates:
        d_min = min(days_until(as_of, d) for d in renewal_dates)
        if d_min is not None and d_min <= 45:
            pts = _rule_condition(score_rules, "R3a")
            if pts:
                items.append(ScoreBreakdownItem(
                    "R3a", _rule_name_kr(score_rules, "R3a"), pts,
                    f"renewal_date={min(renewal_dates, key=lambda d: days_until(as_of, d))}, D-{d_min}(45일 이내)",
                ))
                total += pts
        elif d_min is not None and d_min <= 60:
            pts = _rule_condition(score_rules, "R3b")
            if pts:
                items.append(ScoreBreakdownItem(
                    "R3b", _rule_name_kr(score_rules, "R3b"), pts,
                    f"renewal_date={min(renewal_dates, key=lambda d: days_until(as_of, d))}, D-{d_min}(46~60일)",
                ))
                total += pts

    # --- R4: 최근 6개월 내 상담 이력 없음 ---
    consultation_months = months_elapsed(as_of, customer.last_consultation_at)
    if customer.last_consultation_at is None or (
        consultation_months is not None and consultation_months >= 6
    ):
        pts = _rule_condition(score_rules, "R4")
        if pts:
            lc = customer.last_consultation_at if customer.last_consultation_at else "null"
            items.append(ScoreBreakdownItem(
                "R4", _rule_name_kr(score_rules, "R4"), pts,
                f"last_consultation_at={lc}(최근 6개월 내 상담 이력 없음)",
            ))
            total += pts

    # --- R5: 보험료 연체 이력 ---
    if any(c.premium_status == "OVERDUE" for c in contracts):
        pts = _rule_condition(score_rules, "R5")
        if pts:
            items.append(ScoreBreakdownItem(
                "R5", _rule_name_kr(score_rules, "R5"), pts,
                "해당 고객 계약 중 premium_status==OVERDUE 인 계약 1건 이상",
            ))
            total += pts

    return ScoreResult(total=total, items=items)