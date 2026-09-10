"""Mock Calendar 테스트 — FC 확인 전 거부 / 후 등록 / 중복 방지 / 하드코딩 금지."""
from __future__ import annotations

from src.tools.mock_calendar import MockCalendarTool


def test_schedule_rejected_without_fc(tmp_db):
    cal = MockCalendarTool(tmp_db)
    res = cal.schedule_confirmed_action("sess", "CUST-001", "재상담", "2026-09-17T14:00:00", False)
    assert res.success is False
    assert res.error_code == "FC_NOT_CONFIRMED"
    assert tmp_db.get_calendar_event("sess") is None


def test_schedule_success_after_fc(tmp_db):
    cal = MockCalendarTool(tmp_db)
    res = cal.schedule_confirmed_action("sess2", "CUST-001", "재상담", "2026-09-17T14:00:00", True)
    assert res.success is True
    assert res.event_type == "CALENDAR_SCHEDULED"
    assert res.result_ref
    ev = tmp_db.get_calendar_event("sess2")
    assert ev["due_datetime"] == "2026-09-17T14:00:00"


def test_duplicate_schedule_returns_same_event(tmp_db):
    cal = MockCalendarTool(tmp_db)
    r1 = cal.schedule_confirmed_action("sess3", "CUST-001", "재상담", "2026-09-17T14:00:00", True)
    r2 = cal.schedule_confirmed_action("sess3", "CUST-001", "재상담", "2026-09-17T14:00:00", True)
    assert r1.result_ref == r2.result_ref
    assert r2.extra.get("reused") is True