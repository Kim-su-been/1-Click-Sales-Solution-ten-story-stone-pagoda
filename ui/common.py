"""UI 공통 유틸 — 금융권 영업지원시스템에 맞는 절제된 타이포/컬러 스타일 헬퍼.

보험사 내부 업무 화면을 기준으로 삼아 장식적 이모지·원색 배지 대신
네이비 계열 단일 톤·얇은 보더·명확한 타이포 위계로 통일한다.
"""
from __future__ import annotations

import unicodedata
from typing import Any


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def inject_css() -> None:
    """금융권 업무 화면 톤의 CSS — 절제된 컬러·명확한 위계·얇은 보더."""
    import streamlit as st

    st.markdown(
        """
        <style>
        :root {
            --navy-900: #0f2440;
            --navy-800: #16345c;
            --navy-700: #1e4470;
            --navy-100: #eef2f8;
            --line: #dfe6ee;
            --text-primary: #1c2b3a;
            --text-muted: #64748b;
            --bg-subtle: #f7f9fb;
            --ok: #1d6f42;
            --ok-bg: #e7f3ec;
            --warn: #92661a;
            --warn-bg: #fbf1de;
        }

        [data-testid="stAppViewContainer"] .block-container { padding-top: 3rem; }
        html, body, [class*="css"] { color: var(--text-primary); }

        /* --- 상단 시스템 바 --- */
        .app-topbar { display: flex; align-items: baseline; justify-content: space-between;
            border-bottom: 2px solid var(--navy-900); padding-bottom: 10px; margin-bottom: 18px; }
        .app-topbar .name { font-size: 1.05rem; font-weight: 700; color: var(--navy-900); letter-spacing: -.01em; }
        .app-topbar .name .divider { color: var(--line); margin: 0 8px; font-weight: 400; }
        .app-topbar .name .sub { font-size: 0.82rem; font-weight: 400; color: var(--text-muted); }
        .app-topbar .tag { font-size: 0.68rem; font-weight: 700; letter-spacing: .06em;
            color: var(--navy-700); border: 1px solid var(--navy-700); border-radius: 3px;
            padding: 2px 8px; text-transform: uppercase; }

        h1 { font-size: 1.3rem !important; }

        /* --- 페이지 헤더 --- */
        .page-eyebrow { font-size: 0.74rem; font-weight: 600; letter-spacing: .05em;
            color: var(--text-muted); text-transform: uppercase; margin: 0 0 4px 1px; }
        .page-title { font-size: 1.45rem; font-weight: 700; color: var(--navy-900); margin: 0 0 16px 0;
            padding-bottom: 12px; border-bottom: 1px solid var(--line); }

        /* --- 섹션 헤더 --- */
        .section-header { font-size: 0.95rem; font-weight: 700; color: var(--navy-800);
            margin: 24px 0 10px 0; padding: 2px 0 8px 10px; border-bottom: 1px solid var(--line);
            border-left: 3px solid var(--navy-700); }
        .section-header.first { margin-top: 4px; }

        /* --- 카드 --- */
        .pick-card { background: var(--bg-subtle); border: 1px solid var(--line); border-radius: 4px;
            padding: 18px 20px; }
        .pick-card .title { font-size: 1.1rem; font-weight: 700; color: var(--navy-900); margin-top: 8px; }
        .pick-card .score-badge { display: inline-block; background: var(--navy-900); color: #ffffff;
            font-weight: 700; padding: 5px 14px; border-radius: 3px; font-size: 0.9rem; letter-spacing: .01em; }

        /* --- 상태 태그 (배지) --- */
        .badge { display: inline-block; padding: 2px 10px; border-radius: 3px;
            font-size: 0.76rem; font-weight: 600; letter-spacing: .01em; border: 1px solid transparent; }
        .badge-ok { background: var(--ok-bg); color: var(--ok); border-color: #c7e4d2; }
        .badge-warn { background: var(--warn-bg); color: var(--warn); border-color: #f0dfb4; }
        .badge-info { background: var(--navy-100); color: var(--navy-700); border-color: #d3e0ee; }

        /* --- 고지/안내 문구 --- */
        .notice { background: var(--bg-subtle); border: 1px solid var(--line); border-left: 3px solid var(--navy-700);
            border-radius: 2px; padding: 9px 14px; font-size: 0.82rem; color: var(--text-muted); }

        /* --- 근거 블록 --- */
        .ev-block { border-left: 2px solid var(--navy-700); background: var(--bg-subtle);
            padding: 8px 12px; margin: 4px 0; font-size: 0.86rem; color: var(--text-primary); }

        /* --- 사이드바 진행 스테퍼 --- */
        .stepper { margin: 4px 0 18px 0; }
        .step { display: flex; align-items: center; gap: 10px; position: relative; padding: 6px 0; }
        .step:not(:last-child)::after {
            content: ""; position: absolute; left: 11px; top: 30px; width: 1px; height: 18px;
            background: var(--line);
        }
        .step-dot { flex: 0 0 auto; width: 23px; height: 23px; border-radius: 3px;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.7rem; font-weight: 700; background: #fff; color: var(--text-muted);
            border: 1px solid var(--line); }
        .step-label { font-size: 0.84rem; color: var(--text-muted); }
        .step-done .step-dot { background: var(--ok-bg); border-color: #c7e4d2; color: var(--ok); }
        .step-done .step-label { color: var(--text-primary); }
        .step-current .step-dot { background: var(--navy-900); border-color: var(--navy-900); color: #fff; }
        .step-current .step-label { color: var(--navy-900); font-weight: 700; }

        /* --- 버튼: 금융권 톤(네이비) --- */
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stButton"] button[kind="primaryFormSubmit"] {
            background-color: var(--navy-900); border-color: var(--navy-900);
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: var(--navy-700); border-color: var(--navy-700);
        }
        div[data-testid="stButton"] button[kind="secondary"] { border-color: var(--line); color: var(--text-primary); }

        /* --- Expander (검증/보조 정보) --- */
        div[data-testid="stExpander"] details { border-color: var(--line) !important; border-radius: 4px !important; }
        div[data-testid="stExpander"] summary { font-size: 0.86rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def app_topbar(system_name: str, sub_label: str, tag: str = "DEMO") -> None:
    """앱 최상단 시스템 바 — 회사 내부 업무 시스템 톤의 헤더."""
    import streamlit as st

    st.markdown(
        f'<div class="app-topbar">'
        f'<div class="name">{nfc(system_name)}<span class="divider">|</span>'
        f'<span class="sub">{nfc(sub_label)}</span></div>'
        f'<div class="tag">{nfc(tag)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def page_header(title: str, step_label: str) -> None:
    """화면 최상단 제목 — 스테퍼 라벨(eyebrow) + 제목 조합으로 통일."""
    import streamlit as st

    st.markdown(
        f'<div class="page-eyebrow">{nfc(step_label)}</div>'
        f'<div class="page-title">{nfc(title)}</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, first: bool = False) -> None:
    """화면 내부 섹션 제목 — 페이지 제목과 구분되는 축소된 위계로 통일."""
    import streamlit as st

    cls = "section-header first" if first else "section-header"
    st.markdown(f'<div class="{cls}">{nfc(title)}</div>', unsafe_allow_html=True)


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
