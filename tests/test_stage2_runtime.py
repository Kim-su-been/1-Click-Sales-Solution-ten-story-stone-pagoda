"""Stage 2 Runtime — 상태 전이 · 서비스 모듈 · 파이프라인 통합 테스트.

- 상태 전이 테이블 (is_valid_transition)
- Eligibility / Rescue Score (daily_pick_expected CUST-001 = 90점)
- Safety 규칙 (COMPLIANT / REJECTED · 3가지 위반 유형)
- Grounding (FC 발화 → knowledge evidenceRef 부여)
- Orchestrator 전체 파이프라인 (DONE / SAFETY-REJECT → FEEDBACK)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.runtime_models import (
    WorkflowState,
    is_valid_transition,
    days_until,
    months_elapsed,
)
from src.eligibility import check_customer
from src.rescue_score import compute_score
from src.safety_rules import build_rule_table, check_safety

ROOT = Path(__file__).resolve().parents[1]


def _load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. 상태 전이
# ---------------------------------------------------------------------------
class TestWorkflowTransitions:
    def test_idle_to_pool_scan(self):
        assert is_valid_transition(WorkflowState.IDLE, WorkflowState.POOL_SCAN)

    def test_normal_sequence(self):
        seq = [
            WorkflowState.POOL_SCAN,
            WorkflowState.SCORING,
            WorkflowState.PICK_READY,
            WorkflowState.GROUNDING,
            WorkflowState.SAFETY_CHECK,
            WorkflowState.CONTACT_READY,
        ]
        for cur, nxt in zip(seq, seq[1:]):
            assert is_valid_transition(cur, nxt), f"{cur} -> {nxt}"

    def test_contact_ready_to_transcript(self):
        assert is_valid_transition(WorkflowState.CONTACT_READY, WorkflowState.TRANSCRIPT_READY)

    def test_next_action_to_done(self):
        # 정상 사이클: NEXT_ACTION 은 FEEDBACK 을 건너뛰고 DONE
        assert is_valid_transition(WorkflowState.NEXT_ACTION, WorkflowState.DONE)

    def test_invalid_skip(self):
        assert not is_valid_transition(WorkflowState.IDLE, WorkflowState.SCORING)
        assert not is_valid_transition(WorkflowState.PICK_READY, WorkflowState.SAFETY_CHECK)


# ---------------------------------------------------------------------------
# 2. 날짜 계산
# ---------------------------------------------------------------------------
class TestDateMath:
    def test_days_until(self):
        assert days_until("2026-09-09", "2026-10-11") == 32
        assert days_until("2026-09-09", None) is None

    def test_months_elapsed(self):
        # year/month 차이 (일 무시)
        assert months_elapsed("2026-09-09", "2025-10-09") == 11
        assert months_elapsed("2026-09-09", "2025-01-09") == 20


# ---------------------------------------------------------------------------
# 3. Eligibility + Rescue Score (seed 데이터 기반)
# ---------------------------------------------------------------------------
class TestEligibilityAndScore:
    @pytest.fixture(autouse=True)
    def _loader(self):
        from src.data_loader import DataLoader

        self.loader = DataLoader().load_all()

    def test_eligibility_rules(self):
        c2 = self.loader.customers["CUST-002"]  # 동의 없음
        assert check_customer(c2, self.loader.contracts_of("CUST-002")).exclusion_reason == "CONTACT_CONSENT_NONE"
        c3 = self.loader.customers["CUST-003"]  # 민원
        assert check_customer(c3, self.loader.contracts_of("CUST-003")).exclusion_reason == "ACTIVE_COMPLAINT"

    def test_cust001_score_90(self):
        c1 = self.loader.customers["CUST-001"]
        rules = [dict(r.raw) for r in self.loader.scoring_rules]
        result = compute_score(c1, self.loader.contracts_of("CUST-001"), rules, "2026-09-09")
        assert result.total == 90, f"실제 점수: {result.total}"
        ids = [i.rule_id for i in result.items]
        # R1b(20)+R2(30)+R3a(25)+R4(15) = 90. R5(연체)는 CUST-001 에 해당 없음.
        assert "R1b" in ids and "R2" in ids and "R3a" in ids and "R4" in ids
        assert "R5" not in ids


# ---------------------------------------------------------------------------
# 4. Safety 규칙
# ---------------------------------------------------------------------------
class TestSafetyRules:
    @pytest.fixture(autouse=True)
    def _rules(self):
        raw = _load_json("config/safety_rules.json")["safety_rules"]
        self.rules = build_rule_table(raw)

    def test_compliant(self):
        result = check_safety(
            "갱신 예정일이 다가와 갱신 조건을 미리 안내드립니다. 갱신 시 보험료가 재산정될 수 있습니다.",
            self.rules,
            ["data/knowledge/renewal-faq.md#Q3"],
        )
        assert result.decision == "COMPLIANT"
        assert result.violations == []
        assert result.grounded is True

    def test_rejected_three_types(self):
        result = check_safety(
            "지금 바꾸지 않으면 보장이 크게 줄어듭니다. "
            "이 상품은 보험료가 절대 오르지 않습니다. "
            "세상에서 가장 좋은 보장입니다.",
            self.rules,
            [],
        )
        assert result.decision == "REJECTED"
        vtypes = {v.violation_type for v in result.violations}
        assert vtypes == {"THREAT_PRESSURE", "UNGROUNDED_CLAIM", "EXAGGERATION"}

    def test_grounded_with_evidence(self):
        result = check_safety("갱신 시 보험료가 재산정될 수 있습니다.", self.rules, ["ref"])
        # 위반이 없어도 evidence_refs 로 grounded=True
        assert result.grounded is True


# ---------------------------------------------------------------------------
# 5. Grounding (FC 발화 → evidenceRef)
# ---------------------------------------------------------------------------
class TestGrounding:
    def test_extract_claims_from_fc_lines(self):
        from src.agents.grounding import extract_claim_sentences

        text = (
            "[FC-001] 갱신 예정일이 다가와 안내드립니다.\n"
            "[CUST-001] 네.\n"
            "[FC-001] 보험료가 재산정될 수 있습니다.\n"
        )
        claims = extract_claim_sentences(text)
        assert len(claims) == 2

    def test_run_grounding_grounded(self):
        from src.agents.grounding import run_grounding, discover_knowledge
        from src.runtime_models import GroundingStatus

        sections = discover_knowledge(ROOT / "data" / "knowledge")
        result, _ = run_grounding(
            "[FC-001] 갱신 예정일이 다가와 갱신 조건을 미리 안내드립니다. 갱신 시 보험료가 재산정될 수 있습니다.",
            sections,
        )
        assert result.status == GroundingStatus.GROUNDED
        assert all(i.grounded for i in result.items)


# ---------------------------------------------------------------------------
# 6. Orchestrator 통합 파이프라인
# ---------------------------------------------------------------------------
class TestOrchestrator:
    def test_full_pipeline_done(self):
        from src.agents.orchestrator import run_demo_pipeline

        result = run_demo_pipeline()
        assert result.output.workflow_state == WorkflowState.DONE
        assert result.output.errors == []
        assert result.output.daily_pick["customer_id"] == "CUST-001"
        assert result.output.daily_pick["score"] == 90

    def test_safety_reject_leads_feedback(self):
        from src.agents.orchestrator import run_pipeline
        from src.agents.orchestrator import _load_pipeline_input
        from src.safety_rules import build_rule_table, check_safety
        from src.runtime_models import WorkflowState as WS

        data_root = ROOT / "data"
        inp = _load_pipeline_input(data_root)
        rejected = (
            "지금 바꾸지 않으면 보장이 크게 줄어듭니다. "
            "이 상품은 보험료가 절대 오르지 않습니다."
        )
        result = run_pipeline(inp, saved_transcript=rejected)
        assert result.output.workflow_state == WS.FEEDBACK

    def test_workflow_evidence_populated(self):
        from src.agents.orchestrator import run_demo_pipeline

        result = run_demo_pipeline()
        names = [s.step_name for s in result.steps]
        assert "customer_selection" in names
        assert "grounding" in names
        assert "safety_review" in names
        assert "done" in names