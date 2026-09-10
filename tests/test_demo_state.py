"""demo_state 테스트 — 화면 전이·session_state 기반 상태 관리."""
from __future__ import annotations


def _fresh_state():
    """테스트 격리를 위해 session_state 를 비운다."""
    import streamlit as st

    for k in list(st.session_state.keys()):
        del st.session_state[k]


def test_initial_screen_is_daily_pick():
    _fresh_state()
    from src import demo_state

    assert demo_state.get_screen() == "DAILY_PICK"


def test_navigation_flow():
    _fresh_state()
    from src import demo_state

    demo_state.go_to("CONSULTATION")
    assert demo_state.get_screen() == "CONSULTATION"

    # CONSULTATION -> CLOSING
    demo_state.go_to("CLOSING")
    assert demo_state.get_screen() == "CLOSING"

    # CLOSING -> DAILY_PICK (reset)
    demo_state.reset_to_daily_pick()
    assert demo_state.get_screen() == "DAILY_PICK"


def test_call_and_transcript_flags():
    _fresh_state()
    from src import demo_state

    assert demo_state.is_call_active() is False
    demo_state.set_call_active(True)
    assert demo_state.is_call_active() is True

    assert demo_state.is_transcript_loaded() is False
    demo_state.set_transcript_loaded(True)
    assert demo_state.is_transcript_loaded() is True


def test_crm_confirmed_flag():
    _fresh_state()
    from src import demo_state

    assert demo_state.is_crm_confirmed() is False
    demo_state.set_crm_confirmed(True)
    assert demo_state.is_crm_confirmed() is True


def test_reset_clears_flags():
    _fresh_state()
    from src import demo_state

    demo_state.set_call_active(True)
    demo_state.set_transcript_loaded(True)
    demo_state.set_crm_confirmed(True)
    demo_state.reset_to_daily_pick()
    assert demo_state.is_call_active() is False
    assert demo_state.is_transcript_loaded() is False
    assert demo_state.is_crm_confirmed() is False