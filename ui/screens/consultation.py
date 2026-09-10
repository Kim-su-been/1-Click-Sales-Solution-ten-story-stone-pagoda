"""화면 2: 상담 진행 — Mock 전화·준비된 Transcript·STT Mock 처리."""
from __future__ import annotations

import unicodedata

import streamlit as st

import src.config as cfg
from src import demo_state
from src.data_loader import DataLoader
from ui.common import nfc, page_header, section_header


def render(loader: DataLoader) -> None:
    page_header("상담 진행", "STEP 2 / 3 · 통화 진행")

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
    section_header("상담 고객", first=True)
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

    # 상담 상태
    section_header("상담 진행 중")

    with st.container(border=True):
        col_status, col_stt = st.columns(2)
        with col_status:
            active = demo_state.is_call_active()
            st.markdown(
                '<span class="badge badge-warn">통화 연결됨</span>'
                if active else
                '<span class="badge badge-info">통화 연결 대기</span>',
                unsafe_allow_html=True,
            )
        with col_stt:
            loaded = demo_state.is_transcript_loaded()
            st.markdown(
                '<span class="badge badge-ok">녹취 분석 완료</span>'
                if loaded else
                '<span class="badge badge-warn">녹취 분석 대기</span>',
                unsafe_allow_html=True,
            )

        if not active:
            st.caption("전화 연결 후 이 화면으로 이동했습니다.")

    # 통화 녹취록 — 통화 연결 후 자동으로 텍스트 변환됨 (실제 상담 흐름과 동일하게 수동 클릭 없이 진행)
    section_header("통화 녹취록")
    if demo_state.is_call_active() and not demo_state.is_transcript_loaded():
        with st.spinner("통화 내용을 텍스트로 변환하는 중입니다..."):
            import time

            time.sleep(0.6)
            session_id = demo_state.get_session_id()
            from src.agents.orchestrator import process_mock_stt

            res = process_mock_stt(session_id)
            demo_state.set_tool_result("STT_COMPLETED", res.to_dict())
            if res.success:
                demo_state.set_transcript_loaded(True)
            else:
                st.error(f"녹취록을 불러올 수 없습니다: {res.error_message}")
        st.rerun()

    if demo_state.is_transcript_loaded():
        st.code(loader.utter_text(), language=None)
        st.caption(f"총 {len(loader.transcript)}개 발화가 텍스트로 변환되었습니다.")
    else:
        st.caption("통화가 연결되면 녹취록이 자동으로 텍스트로 변환됩니다.")

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

    st.caption("상담을 완료하면 통화 내용을 분석한 결과가 다음 화면에 표시됩니다.")