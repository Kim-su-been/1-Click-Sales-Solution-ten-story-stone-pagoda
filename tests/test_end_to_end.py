"""End-to-End 테스트 — 초기 파이프라인부터 FC 확인·Mock 저장·Feedback·Execution Log 까지."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.runtime_db import RuntimeDB


@pytest.fixture()
def e2e_db(tmp_path):
    db = RuntimeDB(tmp_path / "demo.db")
    yield db
    db.close()


def _run_full_flow(db: RuntimeDB) -> dict:
    """Customer Selection → Grounding/Safety → Mock 전화 → Mock STT → 분석 → FC 확인 → Mock 저장."""
    from src.agents.orchestrator import (
        _load_pipeline_input,
        run_pipeline,
        start_mock_call,
        process_mock_stt,
        complete_mock_call,
        confirm_and_execute,
    )

    root = Path(__file__).resolve().parents[1]
    inp = _load_pipeline_input(root / "data")
    transcript = (root / "data" / "demo" / "consultation-transcript.txt").read_text(encoding="utf-8")

    # 1) Agent 파이프라인 (DONE)
    result = run_pipeline(inp, saved_transcript=transcript)
    out = result.output
    assert out.workflow_state == "DONE"
    pick = out.daily_pick
    assert pick["customer_id"] == "CUST-001"
    assert pick["score"] == 90

    session_id = "e2e-session-1"

    # 2) Mock 전화 (COMPLIANT 스크립트)
    script = out.script_result["scripts"]["CALL_FIRST_OPENING"]["text"]
    call = start_mock_call(session_id, pick["customer_id"], script, db=db)
    assert call.success is True and call.event_type == "CALL_STARTED"

    # 3) Mock STT
    stt = process_mock_stt(session_id, db=db)
    assert stt.success is True and stt.event_type == "STT_COMPLETED"

    # 4) Mock 전화 종료
    done = complete_mock_call(session_id, pick["customer_id"], db=db)
    assert done.success is True and done.event_type == "CALL_COMPLETED"

    # 5) FC 확인 + Mock CRM + Mock Calendar + Feedback
    crm = out.crm_draft
    calendar = out.next_action_result["calendar_candidate"]
    exec_result = confirm_and_execute(
        session_id=session_id,
        customer_id=pick["customer_id"],
        fc_confirmed=True,
        crm_draft=crm,
        calendar_title=calendar.get("title", "재상담 (Mock)"),
        calendar_due_datetime=calendar.get("due_datetime", ""),
        fc_action="ACCEPTED",
        safety_result={"decision": "COMPLIANT"},
        db=db,
    )
    assert exec_result["success"] is True
    return {"session_id": session_id, "out": out, "exec_result": exec_result, "db": db}


def test_end_to_end_full_flow(e2e_db):
    data = _run_full_flow(e2e_db)
    db = data["db"]
    sid = data["session_id"]

    # CRM 1건
    crm_rec = db.get_crm_record(sid)
    assert crm_rec is not None
    assert crm_rec["status"] == "DRAFT"

    # Calendar 1건
    cal = db.get_calendar_event(sid)
    assert cal is not None
    assert cal["due_datetime"] == "2026-09-17T14:00:00"

    # Feedback 1건
    fb = db.get_feedback(sid)
    assert fb is not None and fb["fc_action"] == "ACCEPTED"

    # Execution Log 확인
    types = {e["event_type"] for e in db.get_executions(sid)}
    for expected in ("CALL_STARTED", "CALL_COMPLETED", "STT_COMPLETED", "FC_CONFIRMED",
                     "CRM_SAVED", "CALENDAR_SCHEDULED", "FEEDBACK_STORED"):
        assert expected in types, f"missing {expected}"


def test_end_to_end_not_confirmed_blocks_save(e2e_db):
    """FC 확인 없이 confirm_and_execute 를 호출하면 저장이 차단된다."""
    from src.agents.orchestrator import confirm_and_execute

    out = confirm_and_execute("e2e-nofc", "CUST-001", fc_confirmed=False)
    assert out["success"] is False
    assert out["reason"] == "FC_NOT_CONFIRMED"
    assert "crm" not in out["results"]
    assert e2e_db.get_crm_record("e2e-nofc") is None


def test_end_to_end_calendar_datetime_from_analysis(e2e_db):
    """Calendar 일시는 Conversation Analysis 결과에서 나온다 (하드코딩 금지)."""
    data = _run_full_flow(e2e_db)
    out = data["out"]
    cal = out.next_action_result["calendar_candidate"]
    # 반드시 Golden 과 같은 2026-09-17T14:00:00 (Transcript 도출)
    assert cal["due_datetime"] == "2026-09-17T14:00:00"