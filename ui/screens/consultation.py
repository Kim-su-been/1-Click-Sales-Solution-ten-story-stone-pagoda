"""화면 2: 상담 진행 — Mock 전화·준비된 Transcript·STT Mock 처리."""
from __future__ import annotations

import unicodedata

import streamlit as st

import src.config as cfg
from src import demo_state
from src.data_loader import DataLoader
from ui.common import nfc


def render(loader: DataLoader) -> None:
    st.title("상담 진행")

    # Runtime Customer Selection 결과로 1-Pick 고객 식별
    from src.agents.orchestrator import run_demo_pipeline

    rt = run_demo_pipeline()
    pick = rt.output.daily_pick
    cust = loader.get_customer(pick["customer_id"])

    st.markdown(
        f'<div class="notice">{nfc(cfg.NOTICE_TEXT)}</div>',
        unsafe_allow_html=True,
    )

    # 고객 정보
    st.markdown("### 상담 고객")
    st.markdown(
        f"""
        <div class="pick-card">
          <div class="title">{nfc(cust.name)} 고객님 ({cust.customer_id})</div>
          <div style="margin-top:6px">
            {nfc(cust.phone)} · {cust.birth_year}년생 · 담당 FC {nfc(cust.fc_id)} ·
            연락 채널 {', '.join(cust.consent_channels)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mock 상담 상태
    st.markdown("### Mock 상담 진행 중")
    st.warning("⚠️ 이 화면의 전화·녹취·STT는 모두 **Mock** 입니다. 실제 전화 발신·음성 인식은 없습니다.")

    col_status, col_stt = st.columns(2)
    with col_status:
        active = demo_state.is_call_active()
        st.markdown(
            '<span class="badge badge-warn">통화 연결됨 (Mock)</span>'
            if active else
            '<span class="badge badge-info">통화 대기 (Mock)</span>',
            unsafe_allow_html=True,
        )
    with col_stt:
        loaded = demo_state.is_transcript_loaded()
        st.markdown(
            '<span class="badge badge-ok">STT 완료 (Mock)</span>'
            if loaded else
            '<span class="badge badge-warn">STT 대기 (Mock)</span>',
            unsafe_allow_html=True,
        )

    if not active:
        st.caption('"전화하기"로 진입했습니다. (데모 상 통화 연결 상태로 가정)')

    # Transcript 불러오기 (Mock STT)
    st.markdown("### 준비된 상담 Transcript (Mock STT)")
    stt_res = demo_state.get_tool_results().get("STT_COMPLETED")
    if st.button("Mock STT 실행", use_container_width=True):
        session_id = demo_state.get_session_id()
        from src.agents.orchestrator import process_mock_stt

        res = process_mock_stt(session_id)
        demo_state.set_tool_result("STT_COMPLETED", res.to_dict())
        if res.success:
            demo_state.set_transcript_loaded(True)
        st.rerun()

    if stt_res is None and demo_state.is_transcript_loaded():
        # 이전 버전 호환: 이미 로드된 경우 STT 기록 재생성 없이 표시만
        stt_res = {"event_type": "STT_COMPLETED", "success": True, "execution_id": "(이전 세션)"}

    if demo_state.is_transcript_loaded():
        st.code(loader.utter_text(), language=None)
        st.caption(
            f"총 {len(loader.transcript)} 발화 · STT(Mock) 변환 완료 — "
            "data/demo/consultation-transcript.txt 에서 로딩"
        )
        if stt_res:
            st.markdown(
                f'<span class="badge badge-ok">STT_COMPLETED · exec {stt_res.get("execution_id","")}</span> '
                f'· chars {stt_res.get("chars", len(loader.utter_text()))}'
                if stt_res.get("success")
                else f'<span class="badge badge-warn">STT 실패 · {stt_res.get("error_message","")}</span>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("버튼을 누르면 준비된 Transcript(`data/demo/consultation-transcript.txt`)가 표시됩니다 (실제 음성 인식 없음).")

    # 상담 완료 및 분석하기
    st.markdown("---")
    if st.button("상담 완료 및 분석하기", type="primary", use_container_width=True):
        session_id = demo_state.get_session_id()
        from src.agents.orchestrator import complete_mock_call

        call_res = complete_mock_call(session_id, cust.customer_id)
        demo_state.set_tool_result("CALL_COMPLETED", call_res.to_dict())
        demo_state.set_transcript_loaded(True)
        demo_state.go_to(cfg.SCREEN_CLOSING)
        st.rerun()

    st.caption("※ '상담 완료 및 분석하기'는 Mock 전화 종료(CALL_COMPLETED) 후 Runtime Conversation Analysis 결과를 CLOSING 화면에 표시합니다.")