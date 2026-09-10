"""Idempotency 테스트 — FC 확인·CRM·Calendar·STT 중복 호출 방지."""
from __future__ import annotations

from src.tools.mock_crm import MockCrmTool
from src.tools.mock_calendar import MockCalendarTool
from src.tools.mock_stt import MockSttTool
from src.tools.feedback_store import MockFeedbackStore

DRAFT = {"status": "DRAFT", "phase": "FC_REVIEW", "note": "초안"}


def test_fc_confirm_button_repeated(tmp_db):
    """FC 확인을 반복해도 CRM/Calendar 는 각각 1건만 생성되어야 한다."""
    crm = MockCrmTool(tmp_db)
    cal = MockCalendarTool(tmp_db)
    r1 = crm.save_confirmed_draft("dup", "CUST-001", DRAFT, True)
    r2 = crm.save_confirmed_draft("dup", "CUST-001", DRAFT, True)
    c1 = cal.schedule_confirmed_action("dup", "CUST-001", "재상담", "2026-09-17T14:00:00", True)
    c2 = cal.schedule_confirmed_action("dup", "CUST-001", "재상담", "2026-09-17T14:00:00", True)

    assert r1.result_ref == r2.result_ref
    assert c1.result_ref == c2.result_ref
    assert len(tmp_db.get_crm_records("dup")) == 1 if hasattr(tmp_db, "get_crm_records") else True
    assert tmp_db.get_crm_record("dup") is not None
    assert tmp_db.get_calendar_event("dup") is not None
    # execution_log: CRM_SAVED 1건 + CALENDAR_SCHEDULED 1건
    types = [e["event_type"] for e in tmp_db.get_executions("dup")]
    assert types.count("CRM_SAVED") == 1
    assert types.count("CALENDAR_SCHEDULED") == 1


def test_stt_repeated(tmp_db):
    from pathlib import Path

    probe = Path(__file__).resolve().parents[1] / "data" / "demo" / "consultation-transcript.txt"
    stt = MockSttTool(tmp_db, transcript_path=probe)
    r1 = stt.transcribe("dup-stt")
    r2 = stt.transcribe("dup-stt")
    assert r1.execution_id == r2.execution_id
    assert r2.extra.get("reused") is True


def test_feedback_repeated(tmp_db):
    fb = MockFeedbackStore(tmp_db)
    r1 = fb.store("dup-fb", "ACCEPTED", {"note": "a"}, None, {"decision": "COMPLIANT"}, {})
    r2 = fb.store("dup-fb", "ACCEPTED", {"note": "a"}, None, {"decision": "COMPLIANT"}, {})
    assert r1.result_ref == r2.result_ref