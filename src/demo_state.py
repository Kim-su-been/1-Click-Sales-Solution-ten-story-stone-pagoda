"""1-Pick Rescue Agent — 데모 화면 상태 관리.

Streamlit session_state 를 사용해 화면 이동(DAILY_PICK → CONSULTATION → CLOSING)과
상담/CRM 확인 상태를 관리한다. Mock Tool 실행 결과는 RuntimeDB 에 저장되며
session_id 로 구분된다.
"""
import uuid

from src.config import SCREEN_DAILY_PICK

# session_state 기본 키
_STATE_KEY = "demo_screen"
_TRANSCRIPT_LOADED_KEY = "transcript_loaded"
_CALL_ACTIVE_KEY = "call_active"
_CRM_CONFIRMED_KEY = "crm_fc_confirmed"
_SESSION_ID_KEY = "demo_session_id"
_DRAFT_TEXT_KEY = "fc_draft_text"
_TOOL_RESULTS_KEY = "tool_execution_results"


def _ensure_state():
    """앱 시작 시 기본 상태를 보장한다. 새로 실행하면 DAILY_PICK 부터 시작."""
    import streamlit as st

    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = SCREEN_DAILY_PICK
    if _TRANSCRIPT_LOADED_KEY not in st.session_state:
        st.session_state[_TRANSCRIPT_LOADED_KEY] = False
    if _CALL_ACTIVE_KEY not in st.session_state:
        st.session_state[_CALL_ACTIVE_KEY] = False
    if _CRM_CONFIRMED_KEY not in st.session_state:
        st.session_state[_CRM_CONFIRMED_KEY] = False
    if _SESSION_ID_KEY not in st.session_state:
        st.session_state[_SESSION_ID_KEY] = "session-" + uuid.uuid4().hex[:8]
    if _DRAFT_TEXT_KEY not in st.session_state:
        st.session_state[_DRAFT_TEXT_KEY] = ""
    if _TOOL_RESULTS_KEY not in st.session_state:
        st.session_state[_TOOL_RESULTS_KEY] = {}


def get_screen() -> str:
    """현재 화면 이름을 반환한다."""
    import streamlit as st

    _ensure_state()
    return st.session_state[_STATE_KEY]


def go_to(screen: str) -> None:
    """지정한 화면으로 이동한다."""
    import streamlit as st

    _ensure_state()
    st.session_state[_STATE_KEY] = screen


def reset_to_daily_pick() -> None:
    """처음으로 돌아가기: DAILY_PICK 으로 이동하고 상태를 초기화한다."""
    import streamlit as st

    st.session_state[_STATE_KEY] = SCREEN_DAILY_PICK
    st.session_state[_TRANSCRIPT_LOADED_KEY] = False
    st.session_state[_CALL_ACTIVE_KEY] = False
    st.session_state[_CRM_CONFIRMED_KEY] = False


# --- Transcript / 통화 상태 ---
def is_transcript_loaded() -> bool:
    import streamlit as st

    _ensure_state()
    return st.session_state[_TRANSCRIPT_LOADED_KEY]


def set_transcript_loaded(loaded: bool) -> None:
    import streamlit as st

    st.session_state[_TRANSCRIPT_LOADED_KEY] = loaded


def is_call_active() -> bool:
    import streamlit as st

    _ensure_state()
    return st.session_state[_CALL_ACTIVE_KEY]


def set_call_active(active: bool) -> None:
    import streamlit as st

    st.session_state[_CALL_ACTIVE_KEY] = active


# --- CRM 확인 상태 (Mock) ---
def is_crm_confirmed() -> bool:
    import streamlit as st

    _ensure_state()
    return st.session_state[_CRM_CONFIRMED_KEY]


def set_crm_confirmed(confirmed: bool) -> None:
    import streamlit as st

    st.session_state[_CRM_CONFIRMED_KEY] = confirmed


# --- Demo Session ID (Mock Tool 실행 단위) ---
def get_session_id() -> str:
    """현재 데모 세션 ID. Mock Tool 실행 데이터를 session 단위로 구분·초기화할 때 사용."""
    import streamlit as st

    _ensure_state()
    return st.session_state[_SESSION_ID_KEY]


def set_session_id(session_id: str) -> None:
    import streamlit as st

    _ensure_state()
    st.session_state[_SESSION_ID_KEY] = session_id


# --- FC 수정 Draft 텍스트 ---
def get_fc_draft_text() -> str:
    import streamlit as st

    _ensure_state()
    return st.session_state[_DRAFT_TEXT_KEY]


def set_fc_draft_text(text: str) -> None:
    import streamlit as st

    _ensure_state()
    st.session_state[_DRAFT_TEXT_KEY] = text


# --- Tool 실행 결과 캐시 (session_state) ---
def get_tool_results() -> dict:
    import streamlit as st

    _ensure_state()
    return st.session_state[_TOOL_RESULTS_KEY]


def set_tool_result(name: str, value: dict) -> None:
    """Tool 실행 결과를 session_state 에 저장 (UI 재표시용). value 는 dict 로 직렬화."""
    import streamlit as st

    _ensure_state()
    st.session_state[_TOOL_RESULTS_KEY][name] = value


def reset_demo(all_data: bool = False) -> None:
    """데모 초기화.

    기본: 현재 session_id 의 Mock 실행 데이터만 초기화하고 화면 상태를 원점으로 되돌린다.
    all_data=True: session_id 도 새로 발급 (전체 데모 재시작).
    고객 Seed·Expected·Knowledge 문서는 건드리지 않는다.
    """
    import streamlit as st

    if not all_data:
        from src.agents.orchestrator import reset_demo_session

        reset_demo_session(get_session_id())
    st.session_state[_STATE_KEY] = SCREEN_DAILY_PICK
    st.session_state[_TRANSCRIPT_LOADED_KEY] = False
    st.session_state[_CALL_ACTIVE_KEY] = False
    st.session_state[_CRM_CONFIRMED_KEY] = False
    st.session_state[_DRAFT_TEXT_KEY] = ""
    st.session_state[_TOOL_RESULTS_KEY] = {}
    if all_data:
        st.session_state[_SESSION_ID_KEY] = "session-" + uuid.uuid4().hex[:8]