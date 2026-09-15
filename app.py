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
from ui.common import inject_css, render_sidebar_logo, render_stepper, render_top_bar


def main() -> None:
    st.set_page_config(page_title=cfg.APP_TITLE, layout="wide")
    inject_css()

    try:
        loader = get_loader()
    except DataLoadingError as exc:
        st.error(f"데이터 로딩 실패: {exc}")
        st.stop()

    # 좌측 진행 단계 표시
    screen = demo_state.get_screen()
    steps = {
        cfg.SCREEN_DAILY_PICK: "오늘의 1-Pick",
        cfg.SCREEN_CONSULTATION: "상담 진행",
        cfg.SCREEN_CLOSING: "상담 완료",
    }
    fc_id = next(iter(loader.customers.values())).fc_id if loader.customers else ""
    step_keys = list(steps.keys())
    step_idx = step_keys.index(screen) if screen in step_keys else 0
    render_top_bar(f"STEP {step_idx + 1}/3 · {steps[step_keys[step_idx]]}", fc_id)

    with st.sidebar:
        render_sidebar_logo()
        st.markdown('<div class="sidebar-eyebrow">진행 단계</div>', unsafe_allow_html=True)
        render_stepper(steps, screen)

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