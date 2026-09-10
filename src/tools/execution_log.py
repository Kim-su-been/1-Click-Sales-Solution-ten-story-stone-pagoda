"""Runtime Execution Log — EXECUTION_LOG evidenceType 근거가 되는 실행 기록을 남긴다.

동일 (session_id, event_type) 반복 호출 시 기존 결과를 재사용한다 (idempotency).
"""
from __future__ import annotations

from src.runtime_db import RuntimeDB
from src.tools.interfaces import ExecutionLog as ExecutionLogInterface
from src.tools.interfaces import ToolExecutionResult


class MockExecutionLog(ExecutionLogInterface):
    """Execution Log Mock Adapter."""

    def __init__(self, db: RuntimeDB | None = None) -> None:
        self.db = db or RuntimeDB()

    def record(
        self,
        session_id: str,
        tool_name: str,
        event_type: str,
        success: bool,
        result_ref: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ToolExecutionResult:
        rec = self.db.record_execution(
            session_id, tool_name, event_type, success,
            result_ref=result_ref, error_code=error_code, error_message=error_message,
        )
        return ToolExecutionResult(
            execution_id=rec["execution_id"],
            session_id=session_id,
            tool_name=tool_name,
            event_type=event_type,
            success=bool(rec["success"]),
            executed_at=rec["executed_at"],
            result_ref=rec["result_ref"],
            error_code=rec.get("error_code"),
            error_message=rec.get("error_message"),
            extra={"reused": rec.get("reused", False)},
        )