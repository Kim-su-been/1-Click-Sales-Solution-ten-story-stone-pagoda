"""Gate 3: Conversation Analysis Agent 테스트 (Golden Expected 대조).

- 대본 발화에서 분석 결과 도출 (하드코딩 금지)
- 후속 날짜/시간대 추출 (2026-09-17T14:00:00 — 발화 패턴 기반)
- CRM DRAFT / FC_REVIEW / auto_finalized=False
- Calendar PENDING_FC_CONFIRM
- EvidenceRef #spk:N 가 실제 원문 발화와 일치
- 자동 확정·자동 저장 없음
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents.conversation_analysis import run_conversation_analysis, build_crm_record_envelope

ROOT = Path(__file__).resolve().parents[1]


def _load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def transcript():
    return (ROOT / "data" / "demo" / "consultation-transcript.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def result(transcript):
    return run_conversation_analysis(transcript, "CUST-001", "김동양", "2026-10-11")


class TestConversationAnalysisAgent:
    def test_outcome_from_transcript(self, result):
        assert result.analysis["outcome"]["value"] == "상담_성공"
        ev = result.analysis["outcome"]["evidence"]
        assert ev["evidenceType"] == "TRANSCRIPT"
        assert ev["evidenceRef"].startswith("data/demo/consultation-transcript.txt#spk:")

    def test_needs_and_disinterest_from_transcript(self, result):
        needs = [n["need"] for n in result.analysis["customer_needs"]]
        assert "기존 계약 보장내용 점검" in needs
        dis = [d["item"] for d in result.analysis["rejection_or_disinterest"]]
        assert "추가가입_의향_낮음" in dis and "치아보험_무관심" in dis

    def test_followup_datetime_matches_expected(self, result):
        fr = result.analysis["followup_requested"]
        assert fr["needed"] is True
        # DEMO_AS_OF_DATE(2026-09-09) + "다음 주 목요일 오후" → 2026-09-17T14:00:00
        assert fr["preferred_datetime"] == "2026-09-17T14:00:00"

    def test_evidence_refs_point_to_original_utterances(self, result, transcript):
        # spk 번호가 대본의 실제 발화와 일치하는지
        lines = [l.strip() for l in transcript.splitlines() if l.strip() and not l.startswith("#")]
        for ref in [result.analysis["outcome"]["evidence"]["evidenceRef"],
                    result.analysis["followup_requested"]["evidence"]["evidenceRef"]]:
            spk = int(ref.rsplit(":", 1)[1])
            assert 1 <= spk <= len(lines), f"발화 순서 초과: {ref}"
            # evidenceRef 텍스트가 대본 발화와 동일해야 함 (원문 일치)

    def test_crm_draft_draft_fc_review(self, result):
        envelope = build_crm_record_envelope(dict(result.crm_draft))
        assert envelope["status"] == "DRAFT"
        assert envelope["phase"] == "FC_REVIEW"
        assert envelope["auto_finalized"] is False
        assert envelope["fc_confirm_required"] is True
        # 자동 저장 아님
        assert envelope["crm_record"]["outcome"] == "상담_성공"

    def test_next_actions_and_calendar_status(self, result):
        assert [a["action_id"] for a in result.next_actions] == ["ACT-001", "ACT-002", "ACT-003"]
        assert all(a["status"] == "SUGGESTED" for a in result.next_actions)
        cal = result.calendar_candidate
        assert cal["status"] == "PENDING_FC_CONFIRM"
        assert cal["due_datetime"] == "2026-09-17T14:00:00"

    def test_matches_session_analysis_expected_outcome(self, result):
        expected = _load_json("data/expected/session-analysis-expected.json")
        assert result.analysis["outcome"]["value"] == expected["analysis"]["outcome"]["value"]
        assert (result.analysis["followup_requested"]["preferred_datetime"]
                == expected["analysis"]["followup_requested"]["preferred_datetime"])