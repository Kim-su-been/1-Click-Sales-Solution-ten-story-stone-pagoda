"""Mock CRM 테스트 — FC 확인 전 거부 / 후 저장 / 중복 방지."""
from __future__ import annotations

from src.tools.mock_crm import MockCrmTool

DRAFT = {"status": "DRAFT", "phase": "FC_REVIEW", "note": "초안"}


def test_save_rejected_without_fc(tmp_db):
    crm = MockCrmTool(tmp_db)
    res = crm.save_confirmed_draft("sess", "CUST-001", DRAFT, fc_confirmed=False)
    assert res.success is False
    assert res.error_code == "FC_NOT_CONFIRMED"
    assert tmp_db.get_crm_record("sess") is None


def test_save_success_after_fc(tmp_db):
    crm = MockCrmTool(tmp_db)
    res = crm.save_confirmed_draft("sess2", "CUST-001", DRAFT, fc_confirmed=True)
    assert res.success is True
    assert res.event_type == "CRM_SAVED"
    assert res.result_ref
    rec = tmp_db.get_crm_record("sess2")
    assert rec["status"] == "DRAFT" and rec["phase"] == "FC_REVIEW"


def test_duplicate_save_returns_same_record(tmp_db):
    crm = MockCrmTool(tmp_db)
    r1 = crm.save_confirmed_draft("sess3", "CUST-001", DRAFT, True)
    r2 = crm.save_confirmed_draft("sess3", "CUST-001", DRAFT, True)
    assert r1.result_ref == r2.result_ref
    assert r2.extra.get("reused") is True
    assert len(tmp_db.get_executions("sess3")) == 1  # CRM_SAVED 는 1건만