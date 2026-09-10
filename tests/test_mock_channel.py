"""Mock Channel Gateway 테스트 — 전화 시작/완료, 문자·카톡 발송, Safety Gate."""
from __future__ import annotations

from src.tools.mock_channel import MockChannelGateway


def test_start_call(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    res = gw.start_call("CUST-001", "sess-call", "갱신 예정일이 다가와 갱신 조건을 미리 안내드립니다.")
    assert res.event_type == "CALL_STARTED"
    assert res.success is True
    assert res.result_ref


def test_complete_call(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    res = gw.complete_call("CUST-001", "sess-call")
    assert res.event_type == "CALL_COMPLETED"
    assert res.success is True


def test_send_sms(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    res = gw.send_sms("CUST-001", "sess-sms", "갱신 예정일이 다가와 갱신 조건을 미리 안내드립니다.")
    assert res.event_type == "SMS_SENT"
    assert res.success is True
    assert res.result_ref


def test_send_kakao(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    res = gw.send_kakao("CUST-001", "sess-kakao", "갱신 예정일이 다가와 갱신 조건을 미리 안내드립니다.")
    assert res.event_type == "KAKAO_SENT"
    assert res.success is True
    assert res.result_ref


# --- Safety Gate ---
def test_rejected_script_blocked_for_call(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    res = gw.start_call("CUST-001", "sess-rej", REJECTED)
    assert res.success is False
    assert res.error_code == "SAFETY_BLOCKED"


def test_rejected_script_blocked_for_sms(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    res = gw.send_sms("CUST-001", "sess-rej2", REJECTED)
    assert res.success is False
    assert res.error_code == "SAFETY_BLOCKED"


def test_blocked_tool_not_recorded(tmp_db, safety_rules):
    gw = MockChannelGateway(tmp_db, safety_rules)
    gw.start_call("CUST-001", "sess-rej3", REJECTED)
    gw.send_kakao("CUST-001", "sess-rej4", REJECTED)
    # SAFETY_BLOCKED 는 실행 로그에 남지 않아야 함 (CRM/Calendar 호출 없음)
    assert tmp_db.get_executions("sess-rej3") == []
    assert tmp_db.get_executions("sess-rej4") == []


REJECTED = (
    "지금 바꾸지 않으면 보장이 크게 줄어듭니다. "
    "이 상품은 보험료가 절대 오르지 않습니다. "
    "세상에서 가장 좋은 보장입니다."
)