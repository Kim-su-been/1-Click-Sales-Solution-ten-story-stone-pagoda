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
            --accent: #1792cd;
            --accent-strong: #12719f;
            --accent-weak: #e8f4fb;
            --ink: #16212e;
            --ink-secondary: #5b6b7c;
            --ink-tertiary: #85919d;
            --line: #dfe4e9;
            --surface: #ffffff;
            --surface-muted: #f5f7f9;
            --surface-page: #eef0f3;
            --ok: #146c47;
            --ok-bg: #e5f2ea;
            --warn: #9a5b0a;
            --warn-bg: #faf0dd;
            --radius-card: 10px;
            --radius-control: 8px;
            --radius-badge: 4px;
            --radius-pill: 999px;
        }

        /* 우리다움체 (우리금융그룹 공식 무료 서체) — 로드 실패 시 시스템 고딕 폰트로 자연스럽게 대체 */
        @font-face {
            font-family: "Wooridaum";
            src: url("https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2205@v1.0/WooridaumL.woff2") format("woff2");
            font-weight: 300; font-style: normal; font-display: swap;
        }
        @font-face {
            font-family: "Wooridaum";
            src: url("https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2205@v1.0/WooridaumR.woff2") format("woff2");
            font-weight: 400; font-style: normal; font-display: swap;
        }
        @font-face {
            font-family: "Wooridaum";
            src: url("https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2205@v1.0/WooridaumB.woff2") format("woff2");
            font-weight: 700; font-style: normal; font-display: swap;
        }

        /* --- 관리자 화면 프레임: 회색 캔버스 위에 흰색 패널이 떠 있는 ERP 레이아웃 --- */
        [data-testid="stMain"] { background: var(--surface-page); }
        [data-testid="stAppViewContainer"] .block-container {
            max-width: 1120px;
            margin-top: 4.5rem; margin-bottom: 32px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius-card);
            padding: 28px 40px 40px;
        }
        html, body, [class*="css"] {
            color: var(--ink);
            font-family: "Wooridaum", "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
                "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
        }

        h1 { font-size: 1.3rem !important; }

        /* --- 상단 유틸리티 바: 좌측 breadcrumb(시스템 내 위치) · 우측 로고 --- */
        .top-bar { display: flex; justify-content: space-between; align-items: center;
            padding: 0 0 14px 0; margin-bottom: 22px; border-bottom: 1px solid var(--line); }
        .top-bar .breadcrumb { font-size: 0.78rem; color: var(--ink-tertiary); font-weight: 500; }
        .top-bar .breadcrumb b { color: var(--ink-secondary); font-weight: 700; }
        .top-bar img { height: 20px; display: block; }

        /* --- 사이드바 --- */
        [data-testid="stSidebarContent"] { padding-top: 0.75rem; }
        /* 펼쳐진 상태에서만 폭을 좁히고, 접힌 상태(aria-expanded="false")는 강제하지 않는다.
           그래야 사이드바를 접었을 때 본문이 그만큼 다시 채워진다. */
        [data-testid="stSidebar"][aria-expanded="true"] { min-width: 230px !important; width: 230px !important; }
        [data-testid="stSidebar"][aria-expanded="true"] > div { width: 230px !important; }
        [data-testid="stSidebar"][aria-expanded="false"] { min-width: 0 !important; width: 0 !important; }
        .sidebar-eyebrow { font-size: 0.74rem; font-weight: 700; letter-spacing: .05em;
            color: var(--ink-tertiary); text-transform: uppercase; margin: 0 0 10px 1px; }

        /* --- 페이지 헤더 --- */
        .page-eyebrow { font-size: 0.76rem; font-weight: 700; color: var(--accent);
            letter-spacing: .03em; margin: 0 0 6px 1px; }
        .page-title { font-size: 1.6rem; font-weight: 700; color: var(--ink); letter-spacing: -.015em;
            margin: 0 0 32px 0; }

        /* --- 섹션 헤더: 하단 보더로 구획을 명확히 구분 --- */
        .section-header { font-size: 1rem; font-weight: 700; color: var(--ink);
            margin: 32px 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid var(--line); }
        .section-header.first { margin-top: 4px; }

        /* --- 카드: 좌측 accent 보더로 강조. Apple 시스템처럼 그림자 없이 보더만으로 구분 --- */
        .pick-card { background: var(--surface); border: 1px solid var(--line); border-left: 3px solid var(--accent);
            border-radius: var(--radius-card); padding: 24px; }
        .pick-card .title { font-size: 1.1rem; font-weight: 700; color: var(--ink); margin-top: 10px; }
        .pick-card .score-badge { display: inline-block; background: var(--accent); color: #ffffff;
            font-weight: 700; padding: 5px 14px; border-radius: var(--radius-badge); font-size: 0.88rem;
            letter-spacing: .01em; }

        /* --- 상태 태그 (배지): 각진 라벨 형태, 소프트 컬러 --- */
        .badge { display: inline-block; padding: 3px 10px; border-radius: var(--radius-badge);
            font-size: 0.75rem; font-weight: 600; }
        .badge-ok { background: var(--ok-bg); color: var(--ok); }
        .badge-warn { background: var(--warn-bg); color: var(--warn); }
        .badge-info { background: var(--accent-weak); color: var(--accent); }

        /* --- 근거 블록 --- */
        .ev-block { background: var(--surface-muted); border-radius: var(--radius-control);
            padding: 10px 14px; margin: 6px 0; font-size: 0.86rem; color: var(--ink); }

        /* --- 레코드 헤더: 라벨/값 필드 그리드 (ERP 상세화면 정보 블록 스타일) --- */
        .field-row { display: flex; gap: 32px; flex-wrap: wrap; margin-top: 16px; }
        .field-row .field { display: flex; flex-direction: column; gap: 4px; }
        .field-row .field-label { font-size: 0.68rem; font-weight: 700; color: var(--ink-tertiary);
            text-transform: uppercase; letter-spacing: .04em; }
        .field-row .field-value { font-size: 0.92rem; font-weight: 600; color: var(--ink); }

        /* --- 데이터 테이블: 업무 시스템 그리드 스타일 (헤더 행 + 줄무늬 행) --- */
        .data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .data-table th { text-align: left; font-size: 0.7rem; font-weight: 700; color: var(--ink-tertiary);
            text-transform: uppercase; letter-spacing: .03em; padding: 9px 12px;
            border-bottom: 1px solid var(--line); background: var(--surface-muted); }
        .data-table td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--ink); }
        .data-table tbody tr:last-child td { border-bottom: none; }
        .data-table tbody tr:nth-child(even) { background: var(--surface-muted); }
        .data-table td.num { text-align: right; font-weight: 700; color: var(--accent); white-space: nowrap; }
        .data-table td.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.76rem; color: var(--ink-tertiary); }

        /* --- 사이드바 진행 스테퍼 --- */
        .stepper { margin: 4px 0 20px 0; }
        .step { display: flex; align-items: center; gap: 12px; position: relative; padding: 7px 0; }
        .step:not(:last-child)::after {
            content: ""; position: absolute; left: 13px; top: 32px; width: 2px; height: 18px;
            background: var(--line);
        }
        .step-dot { flex: 0 0 auto; width: 24px; height: 24px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.7rem; font-weight: 700; background: var(--surface); color: var(--ink-tertiary);
            border: 1.5px solid var(--line); }
        .step-label { font-size: 0.85rem; color: var(--ink-tertiary); }
        .step-done .step-dot { background: var(--ok-bg); border-color: var(--ok-bg); color: var(--ok); }
        .step-done .step-label { color: var(--ink-secondary); }
        .step-current .step-dot { background: var(--accent); border-color: var(--accent); color: #fff; }
        .step-current .step-label { color: var(--ink); font-weight: 700; }

        /* --- 버튼: 단일 accent, 각진 radius, 툴바에 가까운 높이감 --- */
        div[data-testid="stButton"] button {
            border-radius: var(--radius-control) !important;
            padding-top: 0.42rem !important; padding-bottom: 0.42rem !important;
        }
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stButton"] button[kind="primaryFormSubmit"] {
            background-color: var(--accent); border-color: var(--accent);
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background-color: var(--accent-strong); border-color: var(--accent-strong);
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


def render_top_bar(module_label: str, app_title: str) -> None:
    """상단 유틸리티 바 — 좌측에 현재 위치(breadcrumb), 우측에 로고.

    사내 시스템에 로그인해 특정 화면에 들어와 있다는 맥락을 주는 최소한의
    wayfinding 요소. 과거에 있었던 큰 텍스트 배너와 달리 얇고 절제된 형태다.
    """
    import base64
    from pathlib import Path

    import streamlit as st

    logo_path = Path(__file__).parent / "assets" / "dongyang_logo.png"
    logo_html = ""
    if logo_path.exists():
        b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        logo_html = f'<img src="data:image/png;base64,{b64}" alt="동양생명" />'

    st.markdown(
        f'<div class="top-bar">'
        f'<span class="breadcrumb">{nfc(app_title)} <b>·</b> {nfc(module_label)}</span>'
        f"{logo_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_field_row(fields: list[tuple[str, str]]) -> None:
    """라벨/값 필드를 가로로 나열 — 레코드 상세 화면의 정보 블록 스타일."""
    import streamlit as st

    cells = "".join(
        f'<div class="field"><span class="field-label">{nfc(label)}</span>'
        f'<span class="field-value">{nfc(value)}</span></div>'
        for label, value in fields
    )
    st.markdown(f'<div class="field-row">{cells}</div>', unsafe_allow_html=True)


def render_data_table(headers: list[str], rows: list[list[str]], num_col: int | None = None, mono_col: int | None = None) -> None:
    """헤더 행 + 줄무늬 행을 가진 데이터 테이블 렌더링 (업무 시스템 그리드 스타일)."""
    import streamlit as st

    thead = "".join(f"<th>{nfc(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = []
        for i, val in enumerate(row):
            cls = ""
            if num_col is not None and i == num_col:
                cls = ' class="num"'
            elif mono_col is not None and i == mono_col:
                cls = ' class="mono"'
            cells.append(f"<td{cls}>{nfc(str(val))}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    st.markdown(
        f'<table class="data-table"><thead><tr>{thead}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table>',
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
