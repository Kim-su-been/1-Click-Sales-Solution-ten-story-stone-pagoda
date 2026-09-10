"""Mock CRM Tool — FC 확인된 Draft 만 Mock 저장.

FC 확인(fc_confirmed=true) 전에는 저장을 거부한다.
CRM Draft 객체의 기존 상태 계약(DRAFT/FC_REVIEW)은 변경하지 않는다.
"""
from __future__ import annotations

from src.runtime_db import RuntimeDB
from src.tools.interfaces import CRM_SAVED, CrmTool, ERR_FC_NOT_CONFIRMED, ToolExecutionResult


class MockCrmTool(CrmTool):
    """CRM Mock Adapter."""

    def __init__(self, db: RuntimeDB | None = None) -> None:
        self.db = db or RuntimeDB()

    def save_confirmed_draft(
        self,
        session_id: str,
        customer_id: str,
        crm_draft: dict,
        fc_confirmed: bool,
    ) -> ToolExecutionResult:
        if not fc_confirmed:
            return ToolExecutionResult(
                execution_id="", session_id=session_id, tool_name="crm",
                event_type=CRM_SAVED, success=False, executed_at="",
                error_code=ERR_FC_NOT_CONFIRMED,
                error_message="FC 확인 전에는 CRM 저장을 거부합니다.",
            )
        saved = self.db.save_crm_record(
            session_id,
            customer_id,
            status=crm_draft.get("status", "DRAFT"),
            phase=crm_draft.get("phase", "FC_REVIEW"),
            payload=crm_draft,
        )
        record = self.db.record_execution(
            session_id, "crm", CRM_SAVED, True,
            result_ref=saved.get("record_id"),
        )
        return ToolExecutionResult(
            execution_id=record["execution_id"],
            session_id=session_id,
            tool_name="crm",
            event_type=CRM_SAVED,
            success=True,
            executed_at=record["executed_at"],
            result_ref=saved.get("record_id"),
            extra={"reused": saved.get("reused", False) or record.get("reused", False)},
        )