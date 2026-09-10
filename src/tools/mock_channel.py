"""Mock Channel Gateway — Safety COMPLIANT 스크립트만 전화·문자·카카오톡 실행.

실제 전화 발신·문자/카톡 발송은 하지 않는다. 실행 기록만 RuntimeDB 에 남긴다.
Safety 판정(COMPLIANT)을 통과하지 않은 스크립트는 발송·전화 시작이 불가능하다.
"""
from __future__ import annotations

from src.tools.interfaces import (
    CALL_COMPLETED,
    CALL_STARTED,
    ChannelGateway,
    ERR_SAFETY_BLOCKED,
    KAKAO_SENT,
    POSTPONED,
    SMS_SENT,
    ToolExecutionResult,
)
from src.runtime_db import RuntimeDB


def _load_safety_rules() -> list[dict]:
    """config/safety_rules.json 에서 Safety 규칙을 로딩한다. 없으면 빈 규칙."""
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "config" / "safety_rules.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("safety_rules", []) if isinstance(raw, dict) else raw


class MockChannelGateway(ChannelGateway):
    """전화·문자·카카오톡 Mock Adapter."""

    def __init__(self, db: RuntimeDB | None = None, safety_rules: list[dict] | None = None) -> None:
        self.db = db or RuntimeDB()
        # Safety 규칙 없으면 config/safety_rules.json 로딩 (없으면 절대 차단하지 않는 빈 규칙)
        if safety_rules is None:
            safety_rules = _load_safety_rules()
        self.safety_rules = safety_rules

    def _guard_approved(self, approved_script: str) -> tuple[str | None, str | None]:
        """(error_code, error_message). COMPLIANT 가 아니면 SAFETY_BLOCKED 반환."""
        if not approved_script or not approved_script.strip():
            return "empty_script", "빈 스크립트는 발송할 수 없습니다."
        from src.safety_rules import check_safety

        result = check_safety(approved_script, self.safety_rules, evidence_refs=[])
        if result.decision != "COMPLIANT":
            kinds = [v.violation_type for v in result.violations]
            return ERR_SAFETY_BLOCKED, f"Safety REJECTED: {kinds}"
        return None, None

    def _result_from_record(
        self, customer_id: str, session_id: str, event_type: str,
        script: str, record: dict,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            execution_id=record.get("execution_id", ""),
            session_id=session_id,
            tool_name="channel_gateway",
            event_type=event_type,
            success=True,
            executed_at=record.get("executed_at", ""),
            result_ref=record.get("result_ref"),
            extra={
                "customer_id": customer_id,
                "channel": record.get("channel") or event_type.split("_")[0].lower(),
                "script_text": script,
                "reused": record.get("reused", False),
            },
        )

    def start_call(self, customer_id: str, session_id: str, approved_script: str) -> ToolExecutionResult:
        code, msg = self._guard_approved(approved_script)
        if code:
            return ToolExecutionResult(
                execution_id="", session_id=session_id, tool_name="channel_gateway",
                event_type=CALL_STARTED, success=False, executed_at="",
                error_code=code, error_message=msg,
            )
        attempt = self.db.save_contact_attempt(
            session_id, customer_id, "CALL", CALL_STARTED, approved_script,
        )
        record = self.db.record_execution(
            session_id, "channel_gateway", CALL_STARTED, True,
            result_ref=attempt.get("attempt_id"),
        )
        return self._result_from_record(customer_id, session_id, CALL_STARTED, approved_script, record)

    def complete_call(self, customer_id: str, session_id: str) -> ToolExecutionResult:
        record = self.db.record_execution(
            session_id, "channel_gateway", CALL_COMPLETED, True,
        )
        return self._result_from_record(customer_id, session_id, CALL_COMPLETED, "", record)

    def send_sms(self, customer_id: str, session_id: str, approved_script: str) -> ToolExecutionResult:
        code, msg = self._guard_approved(approved_script)
        if code:
            return ToolExecutionResult(
                execution_id="", session_id=session_id, tool_name="channel_gateway",
                event_type=SMS_SENT, success=False, executed_at="",
                error_code=code, error_message=msg,
            )
        attempt = self.db.save_contact_attempt(
            session_id, customer_id, "SMS", SMS_SENT, approved_script,
        )
        record = self.db.record_execution(
            session_id, "channel_gateway", SMS_SENT, True,
            result_ref=attempt.get("attempt_id"),
        )
        return self._result_from_record(customer_id, session_id, SMS_SENT, approved_script, record)

    def send_kakao(self, customer_id: str, session_id: str, approved_script: str) -> ToolExecutionResult:
        code, msg = self._guard_approved(approved_script)
        if code:
            return ToolExecutionResult(
                execution_id="", session_id=session_id, tool_name="channel_gateway",
                event_type=KAKAO_SENT, success=False, executed_at="",
                error_code=code, error_message=msg,
            )
        attempt = self.db.save_contact_attempt(
            session_id, customer_id, "KAKAO", KAKAO_SENT, approved_script,
        )
        record = self.db.record_execution(
            session_id, "channel_gateway", KAKAO_SENT, True,
            result_ref=attempt.get("attempt_id"),
        )
        return self._result_from_record(customer_id, session_id, KAKAO_SENT, approved_script, record)

    def postpone(self, customer_id: str, session_id: str) -> ToolExecutionResult:
        """오늘의 1-Pick 연락 보류(나중에). Safety Gate 없이 보류 사실만 기록."""
        record = self.db.record_execution(
            session_id, "channel_gateway", POSTPONED, True,
        )
        return self._result_from_record(customer_id, session_id, POSTPONED, "", record)