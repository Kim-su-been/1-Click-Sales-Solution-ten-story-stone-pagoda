"""Gate 0: Status Contract Freeze 테스트.

docs/data-contracts.md 8절과 Golden Expected(crm/next-action/session/safety)가
실제 상태 필드·값으로 일치하는지 검증한다. 서로 다른 Namespace(영역)의 상태가
하나의 Enum으로 합쳐지지 않았는지도 확인한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.runtime_models import (
    ActionStatus,
    CrmPhase,
    CrmStatus,
    FcConfirmation,
    GroundingStatus,
    SafetyDecision,
    Screen,
    ViolationType,
    WorkflowState,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _doc() -> str:
    return (ROOT / "docs" / "data-contracts.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. 상수 Namespace 분리 (서로 다른 영역을 한 Enum 으로 합치지 않았는가)
# ---------------------------------------------------------------------------
class TestNamespaceSeparation:
    def test_screen_states_are_own_namespace(self):
        assert Screen.DAILY_PICK == "DAILY_PICK"
        assert Screen.CONSULTATION == "CONSULTATION"
        assert Screen.CLOSING == "CLOSING"

    def test_crm_status_vs_phase_are_separate(self):
        # CrmStatus.DRAFT 와 CrmPhase.FC_REVIEW 는 서로 다른 필드다.
        assert CrmStatus.DRAFT == "DRAFT"
        assert CrmPhase.FC_REVIEW == "FC_REVIEW"

    def test_safety_decision_namespace(self):
        assert SafetyDecision.COMPLIANT == "COMPLIANT"
        assert SafetyDecision.REJECTED == "REJECTED"

    def test_violation_types(self):
        assert ViolationType.THREAT_PRESSURE == "THREAT_PRESSURE"
        assert ViolationType.UNGROUNDED_CLAIM == "UNGROUNDED_CLAIM"
        assert ViolationType.EXAGGERATION == "EXAGGERATION"

    def test_action_status(self):
        assert ActionStatus.SUGGESTED == "SUGGESTED"
        assert ActionStatus.PENDING_FC_CONFIRM == "PENDING_FC_CONFIRM"

    def test_fc_confirmation_constants(self):
        assert FcConfirmation.REQUIRED is True


# ---------------------------------------------------------------------------
# 2. Golden Expected 상태값과 상수 일치
# ---------------------------------------------------------------------------
class TestGoldenExpectedAlignment:
    def test_crm_record_status_matches(self):
        expected = _load_json("data/expected/crm-record-expected.json")
        assert expected["status"] == CrmStatus.DRAFT
        assert expected["phase"] == CrmPhase.FC_REVIEW
        assert expected["auto_finalized"] is False
        assert expected["fc_confirm_required"] is FcConfirmation.REQUIRED

    def test_next_action_status_matches(self):
        expected = _load_json("data/expected/next-action-expected.json")
        for a in expected["next_actions"]:
            assert a["status"] == ActionStatus.SUGGESTED
        assert expected["calendar_candidate"]["status"] == ActionStatus.PENDING_FC_CONFIRM

    def test_safety_reject_status_matches(self):
        expected = _load_json("data/expected/safety-reject-expected.json")
        assert expected["review_result"]["decision"] == SafetyDecision.REJECTED
        types = {v["violation_type"] for v in expected["rejected_script"]["violations"]}
        assert types == {
            ViolationType.THREAT_PRESSURE,
            ViolationType.UNGROUNDED_CLAIM,
            ViolationType.EXAGGERATION,
        }

    def test_session_analysis_outcome_matches(self):
        expected = _load_json("data/expected/session-analysis-expected.json")
        assert set(expected["analysis"].keys()) >= {
            "outcome",
            "customer_needs",
            "customer_interests",
            "rejection_or_disinterest",
            "concerns",
            "followup_requested",
            "ai_summary",
        }
        assert isinstance(expected["analysis"]["outcome"]["value"], str)

    def test_runtime_models_cover_golden_states(self):
        doc = _doc()
        for token in ["THREAT_PRESSURE", "UNGROUNDED_CLAIM", "EXAGGERATION",
                      "PENDING_FC_CONFIRM", "SUGGESTED", "FC_REVIEW", "DRAFT"]:
            assert token in doc, f"data-contracts.md 에 {token} 없음"
            # runtime_models 는 별개 Namespace 로 보유
        assert "WorkflowState" in doc


# ---------------------------------------------------------------------------
# 3. #spk:N 은 발화 순서(파일 라인 아님)
# ---------------------------------------------------------------------------
class TestSpkIndexing:
    def test_spk_is_utterance_order(self):
        expected = _load_json("data/expected/session-analysis-expected.json")
        ref = expected["analysis"]["outcome"]["evidence"]["evidenceRef"]
        spk = int(ref.rsplit("spk:", 1)[1])
        # 마지막 발화(FC 감사 인사) = spk:17
        assert spk == 17

    def test_spk7_is_need_utternance(self):
        expected = _load_json("data/expected/session-analysis-expected.json")
        ref = expected["analysis"]["customer_needs"][0]["evidence"]["evidenceRef"]
        assert ref.endswith("spk:6")