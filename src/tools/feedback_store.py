"""Feedback Store — FC 검토 결과와 최종 실행 결과를 저장한다.

- FC 가 제안을 그대로 승인했는지 / 수정 후 승인했는지 / 거절했는지
- 원본 CRM Draft · FC 수정본 · Safety 결과 · 최종 실행 결과
실제 모델 재학습은 수행하지 않는다.
"""
from __future__ import annotations

from src.runtime_db import RuntimeDB
from src.tools.interfaces import FEEDBACK_STORED, FeedbackStore, ToolExecutionResult

# FC 액션 상수
FC_ACCEPTED = "ACCEPTED"
FC_EDITED = "EDITED"
FC_REJECTED = "REJECTED"


class MockFeedbackStore(FeedbackStore):
    """Feedback Mock Adapter."""

    def __init__(self, db: RuntimeDB | None = None) -> None:
        self.db = db or RuntimeDB()

    def store(
        self,
        session_id: str,
        fc_action: str,
        original_draft: dict | None,
        revised_draft: dict | None,
        safety_result: dict | None,
        final_execution: dict | None,
    ) -> ToolExecutionResult:
        saved = self.db.save_feedback(
            session_id, fc_action, original_draft, revised_draft, safety_result, final_execution,
        )
        record = self.db.record_execution(
            session_id, "feedback_store", FEEDBACK_STORED, True,
            result_ref=saved.get("event_id"),
        )
        return ToolExecutionResult(
            execution_id=record["execution_id"],
            session_id=session_id,
            tool_name="feedback_store",
            event_type=FEEDBACK_STORED,
            success=True,
            executed_at=record["executed_at"],
            result_ref=saved.get("event_id"),
            extra={
                "fc_action": fc_action,
                "reused": saved.get("reused", False) or record.get("reused", False),
            },
        )