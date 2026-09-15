"""화면 2: 상담 진행 — Mock 전화·준비된 Transcript·STT Mock 처리."""
from __future__ import annotations

import unicodedata

import streamlit as st

import src.config as cfg
from src import demo_state
from src.data_loader import DataLoader
from ui.common import humanize, nfc, render_transcript, section_header


def render(loader: DataLoader) -> None:
    # Runtime Customer Selection 결과로 1-Pick 고객 식별
    from src.agents.orchestrator import run_demo_pipeline

    rt = run_demo_pipeline()
    pick = rt.output.daily_pick
    cust = loader.get_customer(pick["customer_id"])

    # 고객 정보
    section_header("상담 고객", first=True)
    field_cells = "".join(
        f'<div class="field"><span class="field-label">{label}</span>'
        f'<span class="field-value">{value}</span></div>'
        for label, value in [
            ("연락처", nfc(cust.phone)),
            ("생년", f"{cust.birth_year}년생"),
            ("담당 FC", nfc(cust.fc_id)),
            ("연락 채널", ", ".join(humanize(c) for c in cust.consent_channels)),
        ]
    )
    st.markdown(
        f"""
        <div class="pick-card">
          <div class="title">{nfc(cust.name)} 고객님 ({cust.customer_id})</div>
          <div class="field-row">{field_cells}</div>
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
                '<span class="badge badge-ok">통화 연결됨</span>'
                if active else
                '<span class="badge badge-warn">통화 연결 대기</span>',
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

    # 통화 녹취록 — FC가 상담 내용을 직접 불러와 음성 인식(STT) 처리
    section_header("통화 녹취록")
    if not demo_state.is_transcript_loaded():
        st.caption("상담 내용을 불러오면 음성 인식(STT) 처리를 거쳐 녹취록이 텍스트로 변환됩니다.")
        if st.button("상담 내용 불러오기", type="primary", use_container_width=True):
            with st.spinner("음성 인식(STT) 처리 중입니다..."):
                import time

                time.sleep(1.0)
                session_id = demo_state.get_session_id()
                from src.agents.orchestrator import process_mock_stt

                res = process_mock_stt(session_id)
                demo_state.set_tool_result("STT_COMPLETED", res.to_dict())
                if res.success:
                    demo_state.set_transcript_loaded(True)
                else:
                    st.error(f"녹취록을 불러올 수 없습니다: {res.error_message}")
            st.rerun()
        return

    render_transcript(loader.utter_text())
    st.caption(f"총 {len(loader.transcript)}개 발화가 텍스트로 변환되었습니다.")

    # 상담 종료 → DB 반영 → 완료 및 분석 (녹취록이 준비된 뒤에만 다음 단계 버튼을 보여준다)
    st.markdown("---")
    if not demo_state.is_consultation_ended():
        if st.button("상담 종료하기", type="primary", use_container_width=True):
            with st.spinner("DB 반영 중입니다..."):
                import time

                time.sleep(1.0)
                session_id = demo_state.get_session_id()
                from src.agents.orchestrator import complete_mock_call

                call_res = complete_mock_call(session_id, cust.customer_id)
                demo_state.set_tool_result("CALL_COMPLETED", call_res.to_dict())
                demo_state.set_consultation_ended(True)
            st.rerun()
    else:
        st.markdown('<span class="badge badge-ok">상담 내용 저장 완료</span>', unsafe_allow_html=True)
        if st.button("상담 완료 및 분석하기", type="primary", use_container_width=True):
            demo_state.go_to(cfg.SCREEN_CLOSING)
            st.rerun()
        st.caption("다음 화면에서 통화 내용을 분석한 결과를 확인할 수 있습니다.")