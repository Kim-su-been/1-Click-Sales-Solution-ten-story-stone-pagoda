"""Tool Interface 정의 — Runtime Product Agent 는 Tool 을 직접 구현하지 않고 Interface 로 호출한다.

각 Tool 은 Interface(추상 계약)와 Mock Adapter(구현)로 분리한다.
실제 외부 API(전화·문자·카톡·STT·CRM·Calendar)는 호출하지 않는다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# event_type 한정 목록 (docs/data-contracts.md 9.2)
CALL_STARTED = "CALL_STARTED"
CALL_COMPLETED = "CALL_COMPLETED"
SMS_SENT = "SMS_SENT"
KAKAO_SENT = "KAKAO_SENT"
STT_COMPLETED = "STT_COMPLETED"
FC_CONFIRMED = "FC_CONFIRMED"
CRM_SAVED = "CRM_SAVED"
CALENDAR_SCHEDULED = "CALENDAR_SCHEDULED"
FEEDBACK_STORED = "FEEDBACK_STORED"

EVENT_TYPES = frozenset({
    CALL_STARTED, CALL_COMPLETED, SMS_SENT, KAKAO_SENT, STT_COMPLETED,
    FC_CONFIRMED, CRM_SAVED, CALENDAR_SCHEDULED, FEEDBACK_STORED,
})

# 오류 코드
ERR_SAFETY_BLOCKED = "SAFETY_BLOCKED"
ERR_FC_NOT_CONFIRMED = "FC_NOT_CONFIRMED"
ERR_DUPLICATE = "DUPLICATE"


@dataclass
class ToolExecutionResult:
    """Tool 실행 결과 (Runtime Tool Contract 9.1 최소 공통 구조)."""
    execution_id: str
    session_id: str
    tool_name: str
    event_type: str
    success: bool
    executed_at: str
    result_ref: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "event_type": self.event_type,
            "success": self.success,
            "executed_at": self.executed_at,
            "result_ref": self.result_ref,
            "error_code": self.error_code,
            "error_message": self.error_message,
            **self.extra,
        }


class ChannelGateway(ABC):
    """전화·문자·카카오톡 Mock 발신 게이트웨이."""

    @abstractmethod
    def start_call(self, customer_id: str, session_id: str, approved_script: str) -> ToolExecutionResult:
        """Safety COMPLIANT 스크립트로 Mock 전화 시작."""

    @abstractmethod
    def complete_call(self, customer_id: str, session_id: str) -> ToolExecutionResult:
        """Mock 전화 종료."""

    @abstractmethod
    def send_sms(self, customer_id: str, session_id: str, approved_script: str) -> ToolExecutionResult:
        """Safety COMPLIANT 스크립트로 Mock 문자 발송."""

    @abstractmethod
    def send_kakao(self, customer_id: str, session_id: str, approved_script: str) -> ToolExecutionResult:
        """Safety COMPLIANT 스크립트로 Mock 카카오톡 발송."""


class SttTool(ABC):
    @abstractmethod
    def transcribe(self, session_id: str) -> ToolExecutionResult:
        """Mock STT: 실제 음성 대신 data/demo/consultation-transcript.txt 를 반환."""


class CrmTool(ABC):
    @abstractmethod
    def save_confirmed_draft(
        self,
        session_id: str,
        customer_id: str,
        crm_draft: dict[str, Any],
        fc_confirmed: bool,
    ) -> ToolExecutionResult:
        """FC 확인된 CRM Draft 만 Mock 저장. 확인 없으면 거부."""


class CalendarTool(ABC):
    @abstractmethod
    def schedule_confirmed_action(
        self,
        session_id: str,
        customer_id: str,
        title: str,
        due_datetime: str,
        fc_confirmed: bool,
    ) -> ToolExecutionResult:
        """FC 확인된 Calendar 후보만 Mock 등록. 확인 없으면 거부."""


class FeedbackStore(ABC):
    @abstractmethod
    def store(
        self,
        session_id: str,
        fc_action: str,
        original_draft: dict[str, Any] | None,
        revised_draft: dict[str, Any] | None,
        safety_result: dict[str, Any] | None,
        final_execution: dict[str, Any] | None,
    ) -> ToolExecutionResult:
        """FC 검토 결과와 최종 실행 결과 저장 (모델 재학습 없음)."""


class ExecutionLog(ABC):
    @abstractmethod
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
        """Runtime 실행 기록을 남긴다 (EXECUTION_LOG)."""