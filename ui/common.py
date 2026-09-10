"""UI 공통 유틸 — 사내 시스템 관리자 화면에 맞는 미니멀 스타일 헬퍼.

Apple Human Interface / Toss 디자인 언어를 참고해 단일 accent 컬러,
넉넉한 여백, 얇은 보더 대신 부드러운 elevation, 텍스트 위계 중심의
정리를 기본으로 한다. 브랜드 배너·이모지 없이 콘텐츠 자체로 구분한다.
"""
from __future__ import annotations

import unicodedata
from typing import Any


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


# 내부 상태 코드 → 화면 표시용 plain-language 라벨. 값 자체(테스트/Expected 비교 대상)는
# 건드리지 않고 화면에 보여줄 때만 사람이 읽기 쉬운 말로 바꾼다.
STATUS_LABELS: dict[str, str] = {
    "DRAFT": "초안",
    "FC_REVIEW": "FC 검토 대기",
    "SAVED": "저장 완료",
    "SUGGESTED": "제안됨",
    "PENDING_FC_CONFIRM": "FC 확인 대기",
    "COMPLIANT": "규정 준수 확인",
    "REJECTED": "반려",
}


def humanize(text: str) -> str:
    """내부 코드/태그성 텍스트를 화면에 읽기 쉽게 변환 (값 자체는 변경하지 않음).

    - 알려진 상태 코드는 한국어 라벨로 치환
    - '_' 로 이어진 태그성 텍스트는 공백으로 풀어서 자연스럽게 표시
    """
    t = nfc(str(text))
    if t in STATUS_LABELS:
        return STATUS_LABELS[t]
    return t.replace("_", " ")


def inject_css() -> None:
    """관리자 화면 톤의 CSS — 단일 accent·넓은 여백·부드러운 카드 elevation."""
    import streamlit as st

    st.markdown(
        """
        <style>
        :root {
            --accent: #3182f6;
            --accent-weak: #eaf2fe;
            --ink: #191f28;
            --ink-secondary: #6b7684;
            --ink-tertiary: #8b95a1;
            --line: #f2f4f6;
            --surface: #ffffff;
            --surface-muted: #f9fafb;
            --ok: #12805c;
            --ok-bg: #e3f6ec;
            --warn: #b25e09;
            --warn-bg: #fdf1df;
            --radius-card: 16px;
            --radius-control: 12px;
            --radius-pill: 999px;
            --shadow-card: 0 1px 2px rgba(15,23,42,0.04), 0 6px 20px rgba(15,23,42,0.06);
        }

        [data-testid="stAppViewContainer"] .block-container { padding-top: 4rem; max-width: 1120px; }
        html, body, [class*="css"] { color: var(--ink); }

        h1 { font-size: 1.3rem !important; }

        /* --- 상단 로고 배너 (우측 정렬) --- */
        .logo-banner { display: flex; justify-content: flex-end;
            padding: 2px 0 16px 0; margin-bottom: 12px; border-bottom: 1px solid var(--line); }
        .logo-banner img { height: 26px; display: block; }

        /* --- 사이드바 --- */
        [data-testid="stSidebarContent"] { padding-top: 0.75rem; }
        .sidebar-eyebrow { font-size: 0.74rem; font-weight: 700; letter-spacing: .05em;
            color: var(--ink-tertiary); text-transform: uppercase; margin: 0 0 10px 1px; }

        /* --- 페이지 헤더 --- */
        .page-eyebrow { font-size: 0.78rem; font-weight: 600; color: var(--accent);
            margin: 0 0 6px 1px; }
        .page-title { font-size: 1.7rem; font-weight: 800; color: var(--ink); letter-spacing: -.01em;
            margin: 0 0 28px 0; }

        /* --- 섹션 헤더: 라인/아이콘 없이 타이포 위계만으로 구분 --- */
        .section-header { font-size: 1.02rem; font-weight: 700; color: var(--ink);
            margin: 32px 0 12px 0; }
        .section-header.first { margin-top: 4px; }

        /* --- 카드 --- */
        .pick-card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-card);
            box-shadow: var(--shadow-card); padding: 22px 24px; }
        .pick-card .title { font-size: 1.15rem; font-weight: 700; color: var(--ink); margin-top: 10px; }
        .pick-card .score-badge { display: inline-block; background: var(--accent); color: #ffffff;
            font-weight: 700; padding: 6px 16px; border-radius: var(--radius-pill); font-size: 0.9rem; }

        /* --- 상태 태그 (배지): pill, 보더 없이 소프트 컬러 --- */
        .badge { display: inline-block; padding: 4px 12px; border-radius: var(--radius-pill);
            font-size: 0.76rem; font-weight: 600; }
        .badge-ok { background: var(--ok-bg); color: var(--ok); }
        .badge-warn { background: var(--warn-bg); color: var(--warn); }
        .badge-info { background: var(--accent-weak); color: var(--accent); }

        /* --- 고지/안내 문구 --- */
        .notice { background: var(--surface-muted); border-radius: var(--radius-control);
            padding: 12px 16px; font-size: 0.82rem; color: var(--ink-secondary); }

        /* --- 근거 블록 --- */
        .ev-block { background: var(--surface-muted); border-radius: var(--radius-control);
            padding: 10px 14px; margin: 6px 0; font-size: 0.86rem; color: var(--ink); }

        /* --- 사이드바 진행 스테퍼 --- */
        .stepper { margin: 4px 0 20px 0; }
        .step { display: flex; align-items: center; gap: 12px; position: relative; padding: 7px 0; }
        .step:not(:last-child)::after {
            content: ""; position: absolute; left: 13px; top: 32px; width: 2px; height: 18px;
            background: var(--line);
        }
        .step-dot { flex: 0 0 auto; width: 26px; height: 26px; border-radius: var(--radius-pill);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.72rem; font-weight: 700; background: var(--surface); color: var(--ink-tertiary);
            border: 1.5px solid var(--line); }
        .step-label { font-size: 0.86rem; color: var(--ink-tertiary); }
        .step-done .step-dot { background: var(--ok-bg); border-color: var(--ok-bg); color: var(--ok); }
        .step-done .step-label { color: var(--ink-secondary); }
        .step-current .step-dot { background: var(--accent); border-color: var(--accent); color: #fff; }
        .step-current .step-label { color: var(--ink); font-weight: 700; }

        /* --- 버튼: 단일 accent, 넉넉한 radius --- */
        div[data-testid="stButton"] button {
            border-radius: var(--radius-control) !important;
        }
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stButton"] button[kind="primaryFormSubmit"] {
            background-color: var(--accent); border-color: var(--accent);
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: #1b64da; border-color: #1b64da;
        }
        div[data-testid="stButton"] button[kind="secondary"] {
            border-color: var(--line); color: var(--ink);
        }

        /* --- st.container(border=True): Streamlit 기본 보더 색/라운드만 정리 --- */
        div[data-testid="stVerticalBlock"] {
            border-radius: var(--radius-card);
            border-color: var(--line);
        }

        /* --- Expander (보조/검증 정보) --- */
        div[data-testid="stExpander"] details { border-color: var(--line) !important; border-radius: var(--radius-control) !important; }
        div[data-testid="stExpander"] summary { font-size: 0.86rem; color: var(--ink-secondary); }

        /* --- 코드 블록 --- */
        div[data-testid="stCodeBlock"] { border-radius: var(--radius-control); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_logo_banner() -> None:
    """상단 로고 배너 — 사내 시스템 화면임을 나타내는 최소한의 브랜드 마크만 표시."""
    import base64
    from pathlib import Path

    import streamlit as st

    logo_path = Path(__file__).parent / "assets" / "dongyang_logo.png"
    if not logo_path.exists():
        return
    b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    st.markdown(
        f'<div class="logo-banner"><img src="data:image/png;base64,{b64}" alt="동양생명" /></div>',
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
