"""Execution Log 테스트 — EXECUTION_LOG Runtime 근거 생성·재사용."""
from __future__ import annotations

from src.tools.execution_log import MockExecutionLog


def test_record_creates_execution_log(tmp_db):
    log = MockExecutionLog(tmp_db)
    res = log.record("sess-log", "stt", "STT_COMPLETED", True, result_ref="rec-1")
    assert res.success is True
    assert res.event_type == "STT_COMPLETED"
    rows = tmp_db.get_executions("sess-log")
    assert len(rows) == 1
    assert rows[0]["result_ref"] == "rec-1"


def test_record_reuses_on_duplicate(tmp_db):
    log = MockExecutionLog(tmp_db)
    r1 = log.record("sess-log2", "crm", "CRM_SAVED", True, result_ref="rec-crm")
    r2 = log.record("sess-log2", "crm", "CRM_SAVED", True, result_ref="rec-crm")
    assert r1.execution_id == r2.execution_id
    assert r2.extra.get("reused") is True


def test_record_error_case(tmp_db):
    log = MockExecutionLog(tmp_db)
    res = log.record("sess-log3", "crm", "CRM_SAVED", False,
                     error_code="FC_NOT_CONFIRMED", error_message="확인 필요")
    assert res.success is False
    assert res.error_code == "FC_NOT_CONFIRMED"