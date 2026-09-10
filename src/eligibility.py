"""Eligibility 검사 — 고객이 연락 가능하고 1-Pick 후보가 될 수 있는지 판정.

docs/data-contracts.md 2.4 절 규칙:
- consent_channels 가 비어 있으면 CONTACT_CONSENT_NONE
- active_complaint == true 이면 ACTIVE_COMPLAINT
- 유효한 계약(ACTIVE)이 하나 이상 있어야 함
- (연락 가능 채널이 하나 이상 = consent_channels 가 비어 있지 않음)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.data_loader import Customer, Contract

INELIGIBLE_REASON_CONSENT = "CONTACT_CONSENT_NONE"
INELIGIBLE_REASON_COMPLAINT = "ACTIVE_COMPLAINT"
INELIGIBLE_REASON_NO_CONTRACT = "NO_ACTIVE_CONTRACT"

# 화면 표시용 plain-language 라벨 (내부 코드값은 그대로 유지)
EXCLUSION_REASON_LABELS: dict[str, str] = {
    INELIGIBLE_REASON_CONSENT: "연락 동의된 채널 없음",
    INELIGIBLE_REASON_COMPLAINT: "진행 중인 민원 있음",
    INELIGIBLE_REASON_NO_CONTRACT: "유효한 계약 없음",
}


@dataclass
class EligibilityResult:
    eligible: bool
    exclusion_reason: str | None = None
    details: list[str] = None

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = []


def check_customer(
    customer: Customer,
    contracts: list[Contract],
) -> EligibilityResult:
    """한 명의 고객에 대한 Eligibility 검사.

    검사 순서는 data-contracts.md 2.4 절과 daily_pick_expected 의
    CUST-002(동의 없음)·CUST-003(민원) 우선순위를 따른다.
    """
    reasons: list[str] = []

    # 1) 연락 동의
    if not customer.consent_channels:
        reasons.append(INELIGIBLE_REASON_CONSENT)
    # 2) 진행 중 민원
    if customer.active_complaint:
        reasons.append(INELIGIBLE_REASON_COMPLAINT)
    # 3) 유효한 계약
    active_contracts = [c for c in contracts if c.status == "ACTIVE"]
    if not active_contracts:
        reasons.append(INELIGIBLE_REASON_NO_CONTRACT)

    if reasons:
        return EligibilityResult(
            eligible=False,
            exclusion_reason=reasons[0],
            details=reasons,
        )
    return EligibilityResult(eligible=True, exclusion_reason=None, details=[])


def classify_all(
    customers: list[Customer],
    contracts_by_customer: dict[str, list[Contract]],
) -> dict[str, EligibilityResult]:
    return {
        c.customer_id: check_customer(c, contracts_by_customer.get(c.customer_id, []))
        for c in customers
    }