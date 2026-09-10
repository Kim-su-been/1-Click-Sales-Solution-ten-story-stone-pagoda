"""1-Pick Rescue Agent — Streamlit 앱 엔트리포인트 (Walking Skeleton).

단계: 오늘의 1-Pick → 상담 진행 → 상담 완료
모든 데이터는 Data Loader를 통해 시드/Expected 파일에서 로딩한다.
Runtime Product Agent(LLM)는 아직 포함하지 않는다.
"""
from __future__ import annotations

import streamlit as st

import src.config as cfg
import src.demo_state as demo_state
from src.data_loader import DataLoadingError, get_loader
from ui.common import inject_css


def main() -> None:
    st.set_page_config(page_title=cfg.APP_TITLE, page_icon="🛟", layout="wide")
    inject_css()

    # 헤더
    st.markdown("## 🛟 1-Pick Rescue Agent — Demo (Walking Skeleton)")

    try:
        loader = get_loader()
    except DataLoadingError as exc:
        st.error(f"데이터 로딩 실패: {exc}")
        st.stop()

    # 좌측 진행 단계 표시
    screen = demo_state.get_screen()
    steps = {
        cfg.SCREEN_DAILY_PICK: "1. 오늘의 1-Pick",
        cfg.SCREEN_CONSULTATION: "2. 상담 진행",
        cfg.SCREEN_CLOSING: "3. 상담 완료",
    }
    with st.sidebar:
        st.markdown("**진행 단계**")
        for key, label in steps.items():
            mark = "✅" if key == screen else "·"
            st.markdown(f"{mark} {label}")
        st.markdown("---")
        st.caption(f"데모 기준일: **{cfg.DEMO_AS_OF_DATE}**")
        st.caption("모든 데이터는 가상 Mock 데이터입니다.")

    # 화면 라우팅
    if screen == cfg.SCREEN_CONSULTATION:
        from ui.screens.consultation import render as render_consultation

        render_consultation(loader)
    elif screen == cfg.SCREEN_CLOSING:
        from ui.screens.closing import render as render_closing

        render_closing(loader)
    else:
        from ui.screens.daily_pick import render as render_daily_pick

        render_daily_pick(loader)


if __name__ == "__main__":
    main()