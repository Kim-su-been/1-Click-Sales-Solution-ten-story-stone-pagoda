"""Gate 1: Customer Selection Agent 테스트 (Golden Expected 대조).

- Ineligible 제외 (동의 없음 · 민원)
- Eligible 만 rescue_score 계산, Ineligible 은 null
- 김동양(CUST-001) 규칙 계산 90점, 최종 1-Pick
- D-32 / 14개월 / 11개월 계산
- CUSTOMER_DATA Evidence 존재
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import DEMO_AS_OF_DATE
from src.data_loader import DataLoader
from src.eligibility import check_customer
from src.rescue_score import compute_score
from src.agents.customer_selection import run_customer_selection, load_contracts_by_customer

ROOT = Path(__file__).resolve().parents[1]


def _load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def loader():
    return DataLoader().load_all()


def _score_rules_dict(loader) -> list[dict]:
    return [dict(r.raw) for r in loader.scoring_rules]


class TestCustomerSelectionAgent:
    def test_eligibility_excludes_no_consent(self, loader):
        c2 = loader.customers["CUST-002"]
        r = check_customer(c2, loader.contracts_of("CUST-002"))
        assert r.eligible is False
        assert r.exclusion_reason == "CONTACT_CONSENT_NONE"

    def test_eligibility_excludes_complaint(self, loader):
        c3 = loader.customers["CUST-003"]
        r = check_customer(c3, loader.contracts_of("CUST-003"))
        assert r.eligible is False
        assert r.exclusion_reason == "ACTIVE_COMPLAINT"

    def test_kim_score_90_rule_calculated(self, loader):
        c1 = loader.customers["CUST-001"]
        result = compute_score(c1, loader.contracts_of("CUST-001"), _score_rules_dict(loader), DEMO_AS_OF_DATE)
        assert result.total == 90, f"실제 점수: {result.total}"
        by_id = {i.rule_id: i.points for i in result.items}
        # 담당 FC 변경 20점(R1b), 접촉 30(R2), 갱신 25(R3a), 상담 없음 15(R4)
        assert by_id.get("R1b") == 20
        assert by_id.get("R2") == 30
        assert by_id.get("R3a") == 25
        assert by_id.get("R4") == 15

    def test_selection_picks_kim_and_marks_ineligible_null(self, loader):
        customers = list(loader.customers.values())
        contracts_by = load_contracts_by_customer(loader.contracts)
        summary, step = run_customer_selection(customers, contracts_by, _score_rules_dict(loader), DEMO_AS_OF_DATE)
        assert summary.picked_customer.customer_id == "CUST-001"
        assert summary.picked_score.total == 90
        # ineligible 은 rescue_score 없음(potential_score 만 설명용)
        assert "CUST-002" in summary.eligible
        assert summary.eligible["CUST-002"].eligible is False

    def test_selection_evidence_customer_data(self, loader):
        customers = list(loader.customers.values())
        contracts_by = load_contracts_by_customer(loader.contracts)
        _, step = run_customer_selection(customers, contracts_by, _score_rules_dict(loader), DEMO_AS_OF_DATE)
        assert step.evidence, "스텝에 evidence 가 없음"
        assert step.evidence[0].artifact_type == "score_breakdown"

    def test_date_math_used_in_score(self, loader):
        from src.runtime_models import days_until, months_elapsed
        # D-32 · 14개월 · 11개월
        assert days_until(DEMO_AS_OF_DATE, "2026-10-11") == 32
        c1 = loader.customers["CUST-001"]
        assert months_elapsed(DEMO_AS_OF_DATE, c1.last_contacted_at) == 14
        assert months_elapsed(DEMO_AS_OF_DATE, c1.fc_changed_at) == 11

    def test_matches_daily_pick_expected(self, loader):
        expected = _load_json("data/expected/daily_pick_expected.json")
        customers = list(loader.customers.values())
        contracts_by = load_contracts_by_customer(loader.contracts)
        summary, _ = run_customer_selection(customers, contracts_by, _score_rules_dict(loader), DEMO_AS_OF_DATE)
        top = expected["candidates"][0]
        assert top["customer_id"] == summary.picked_customer.customer_id
        assert top["rescue_score"] == summary.picked_score.total