"""Feedback Store 테스트 — FC 액션·원본/수정 Draft·Safety·최종 실행 저장."""
from __future__ import annotations

from src.tools.feedback_store import MockFeedbackStore


def test_store_feedback(tmp_db):
    fb = MockFeedbackStore(tmp_db)
    res = fb.store(
        "sess-fb", fc_action="ACCEPTED",
        original_draft={"note": "원본"}, revised_draft=None,
        safety_result={"decision": "COMPLIANT"},
        final_execution={"CRM_SAVED": {"success": True}},
    )
    assert res.success is True
    assert res.event_type == "FEEDBACK_STORED"
    rec = tmp_db.get_feedback("sess-fb")
    assert rec["fc_action"] == "ACCEPTED"
    assert rec["original_draft"] == {"note": "원본"}


def test_store_rejected_action(tmp_db):
    fb = MockFeedbackStore(tmp_db)
    res = fb.store("sess-fb2", fc_action="REJECTED", original_draft={"note": "x"},
                   revised_draft=None, safety_result={"decision": "COMPLIANT"},
                   final_execution={})
    assert res.success is True
    assert tmp_db.get_feedback("sess-fb2")["fc_action"] == "REJECTED"


def test_duplicate_feedback_reused(tmp_db):
    fb = MockFeedbackStore(tmp_db)
    r1 = fb.store("sess-fb3", fc_action="EDITED", original_draft={}, revised_draft={"note": "수정"},
                  safety_result=None, final_execution={})
    r2 = fb.store("sess-fb3", fc_action="EDITED", original_draft={}, revised_draft={"note": "수정"},
                  safety_result=None, final_execution={})
    assert r1.result_ref == r2.result_ref