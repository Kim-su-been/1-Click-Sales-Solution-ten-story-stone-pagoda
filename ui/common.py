"""UI 공통 유틸 — 카드/배지/Evidence 펼치기 스타일 헬퍼."""
from __future__ import annotations

import unicodedata
from typing import Any


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def inject_css() -> None:
    """금융사 업무 화면 느낌의 최소 CSS."""
    import streamlit as st

    st.markdown(
        """
        <style>
        .pick-card { background: #f0f6ff; border: 1px solid #b3c9e8; border-radius: 10px;
                     padding: 18px 18px; }
        .pick-card .title { font-size: 1.15rem; font-weight: 700; color: #0b3a75; }
        .pick-card .score-badge { display: inline-block; background: #0b3a75; color: #ffffff;
                     font-weight: 700; padding: 6px 16px; border-radius: 20px; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 12px;
                 font-size: 0.8rem; }
        .badge-ok { background: #dff0e3; color: #1d6f2e; }
        .badge-warn { background: #fff3cf; color: #8a6d1a; }
        .badge-info { background: #e2edfb; color: #234b8f; }
        .notice { background: #fdf6e3; border: 1px solid #e5d4a3; border-radius: 8px;
                  padding: 10px 14px; font-size: 0.9rem; }
        .ev-block { border-left: 3px solid #b3c9e8; background: #f5f8fd;
                    padding: 8px 12px; margin: 4px 0; font-size: 0.88rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


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