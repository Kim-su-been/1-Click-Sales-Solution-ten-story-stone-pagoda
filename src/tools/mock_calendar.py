"""Mock Calendar Tool — FC 확인된 후보만 Mock 등록.

날짜와 시간은 Conversation Analysis 결과에서 가져온다 (하드코딩 금지).
"""
from __future__ import annotations

from src.runtime_db import RuntimeDB
from src.tools.interfaces import CALENDAR_SCHEDULED, CalendarTool, ERR_FC_NOT_CONFIRMED, ToolExecutionResult


class MockCalendarTool(CalendarTool):
    """Calendar Mock Adapter."""

    def __init__(self, db: RuntimeDB | None = None) -> None:
        self.db = db or RuntimeDB()

    def schedule_confirmed_action(
        self,
        session_id: str,
        customer_id: str,
        title: str,
        due_datetime: str,
        fc_confirmed: bool,
    ) -> ToolExecutionResult:
        if not fc_confirmed:
            return ToolExecutionResult(
                execution_id="", session_id=session_id, tool_name="calendar",
                event_type=CALENDAR_SCHEDULED, success=False, executed_at="",
                error_code=ERR_FC_NOT_CONFIRMED,
                error_message="FC 확인 전에는 Calendar 등록을 거부합니다.",
            )
        saved = self.db.save_calendar_event(
            session_id, customer_id, title, due_datetime, "PENDING_FC_CONFIRM",
        )
        record = self.db.record_execution(
            session_id, "calendar", CALENDAR_SCHEDULED, True,
            result_ref=saved.get("event_id"),
        )
        return ToolExecutionResult(
            execution_id=record["execution_id"],
            session_id=session_id,
            tool_name="calendar",
            event_type=CALENDAR_SCHEDULED,
            success=True,
            executed_at=record["executed_at"],
            result_ref=saved.get("event_id"),
            extra={
                "title": title,
                "due_datetime": due_datetime,
                "reused": saved.get("reused", False) or record.get("reused", False),
            },
        )