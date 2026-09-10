"""UI 공통 유틸 — 타이포 스케일, 스테퍼, 카드/배지/Evidence 펼치기 스타일 헬퍼.

기존에는 모든 섹션 제목을 `st.markdown("### ...")`로 작성해 st.title 과 동일한
굵기/크기의 헤더가 화면 전체에 반복되어 시각적 위계가 사라지는 문제가 있었다.
이 모듈은 페이지 제목(page_header) · 섹션 제목(section_header) · 진행 스테퍼
(render_stepper)를 별도 스타일로 분리해 화면을 한눈에 훑어볼 수 있게 한다.
"""
from __future__ import annotations

import unicodedata
from typing import Any


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def inject_css() -> None:
    """금융사 업무 화면 느낌의 CSS — 타이포 위계·간격·카드 스타일 정리."""
    import streamlit as st

    st.markdown(
        """
        <style>
        /* --- 전역 타이포 위계 정리: st.title 은 페이지 제목으로만 사용 --- */
        h1 { font-size: 1.4rem !important; }
        [data-testid="stAppViewContainer"] .block-container { padding-top: 2.2rem; }

        /* --- 페이지 헤더 (화면당 1회) --- */
        .page-eyebrow { font-size: 0.76rem; font-weight: 700; letter-spacing: .06em;
                     color: #5b7aa8; text-transform: uppercase; margin: 0 0 4px 2px; }
        .page-title { font-size: 1.6rem; font-weight: 800; color: #0f2440; margin: 0 0 16px 0;
                     padding-bottom: 12px; border-bottom: 1px solid #e3ecf7; }

        /* --- 섹션 헤더 (화면 내 다수) --- */
        .section-header { font-size: 1.0rem; font-weight: 700; color: #16345c;
                     margin: 26px 0 10px 0; padding-bottom: 6px;
                     border-bottom: 2px solid #e3ecf7; display: flex; align-items: center; gap: 6px; }
        .section-header.first { margin-top: 6px; }

        /* --- 카드/배지/근거 블록 --- */
        .pick-card { background: #f0f6ff; border: 1px solid #b3c9e8; border-radius: 10px;
                     padding: 18px 18px; }
        .pick-card .title { font-size: 1.15rem; font-weight: 700; color: #0b3a75; margin-top: 8px; }
        .pick-card .score-badge { display: inline-block; background: #0b3a75; color: #ffffff;
                     font-weight: 700; padding: 6px 16px; border-radius: 20px; font-size: 0.95rem; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 12px;
                 font-size: 0.8rem; font-weight: 600; }
        .badge-ok { background: #dff0e3; color: #1d6f2e; }
        .badge-warn { background: #fff3cf; color: #8a6d1a; }
        .badge-info { background: #e2edfb; color: #234b8f; }
        .notice { background: #fdf6e3; border: 1px solid #e5d4a3; border-radius: 8px;
                  padding: 10px 14px; font-size: 0.85rem; color: #6b5a1e; }
        .ev-block { border-left: 3px solid #b3c9e8; background: #f5f8fd;
                    padding: 8px 12px; margin: 4px 0; border-radius: 0 6px 6px 0; font-size: 0.88rem; }

        /* --- 사이드바 진행 스테퍼 --- */
        .stepper { margin: 4px 0 18px 0; }
        .step { display: flex; align-items: center; gap: 10px; position: relative; padding: 6px 0; }
        .step:not(:last-child)::after {
            content: ""; position: absolute; left: 12px; top: 30px; width: 2px; height: 18px;
            background: #d7e1ee;
        }
        .step-dot { flex: 0 0 auto; width: 25px; height: 25px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.72rem; font-weight: 700; background: #eef2f8; color: #8296b3;
            border: 2px solid #d7e1ee; }
        .step-label { font-size: 0.86rem; color: #7c8aa0; }
        .step-done .step-dot { background: #1d6f2e; border-color: #1d6f2e; color: #fff; }
        .step-done .step-label { color: #1d6f2e; }
        .step-current .step-dot { background: #0b3a75; border-color: #0b3a75; color: #fff; }
        .step-current .step-label { color: #0b3a75; font-weight: 700; }
        .step-upcoming .step-dot { background: #fff; }

        /* --- 개발/검증 패널: 본문 플로우와 시각적으로 분리 --- */
        .dev-panel-note { font-size: 0.8rem; color: #8296b3; margin: -4px 0 10px 2px; }
        div[data-testid="stExpander"] details { border-color: #e3ecf7 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, step_label: str) -> None:
    """화면 최상단 제목 — '스테퍼 라벨(eyebrow) + 아이콘 제목' 조합으로 통일."""
    import streamlit as st

    st.markdown(
        f'<div class="page-eyebrow">{nfc(step_label)}</div>'
        f'<div class="page-title">{icon} {nfc(title)}</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, icon: str = "", first: bool = False) -> None:
    """화면 내부 섹션 제목 — st.title 과 구분되는 축소된 위계로 통일."""
    import streamlit as st

    label = f"{icon} {nfc(title)}".strip()
    cls = "section-header first" if first else "section-header"
    st.markdown(f'<div class="{cls}">{label}</div>', unsafe_allow_html=True)


def render_stepper(steps: dict[str, str], current: str) -> None:
    """진행 단계를 3-state(완료/진행중/예정) 스테퍼로 렌더링."""
    import streamlit as st

    keys = list(steps.keys())
    current_idx = keys.index(current) if current in keys else 0

    rows = []
    for i, key in enumerate(keys):
        label = nfc(steps[key])
        if i < current_idx:
            state, icon = "done", "✓"
        elif i == current_idx:
            state, icon = "current", str(i + 1)
        else:
            state, icon = "upcoming", str(i + 1)
        rows.append(
            f'<div class="step step-{state}">'
            f'<span class="step-dot">{icon}</span>'
            f'<span class="step-label">{label}</span>'
            f"</div>"
        )
    st.markdown(f'<div class="stepper">{"".join(rows)}</div>', unsafe_allow_html=True)


def render_evidence(evidence: Any, label: str | None = None, key_prefix: str = "ev") -> None:
    """single evidence dict 또는 evidence 목록을 펼치기 영역으로 렌더링."""
    import streamlit as st

    items: list[dict[str, Any]] = []
    if isinstance(evidence, dict) and ("evidenceType" in evidence or "evidenceText" in evidence):
        items = [evidence]
    elif isinstance(evidence, list):
        items = [e for e in evidence if isinstance(e, dict)]
    elif isinstance(evidence, dict):
        # {필드: evidence} 스타일
        for v in evidence.values():
            if isinstance(v, dict) and "evidenceText" in v:
                items.append(v)

    if not items:
        st.caption("(근거 없음)")
        return

    title = label or f"근거 확인 {key_prefix}"
    with st.expander(title):
        for ev in items:
            etype = nfc(str(ev.get("evidenceType", "")))
            eref = nfc(str(ev.get("evidenceRef", "")))
            etext = nfc(str(ev.get("evidenceText", "")))
            st.markdown(
                f"""
                <div class="ev-block">
                <b>{etype}</b> · <code>{eref}</code><br/>
                {etext}
                </div>
                """,
                unsafe_allow_html=True,
            )
