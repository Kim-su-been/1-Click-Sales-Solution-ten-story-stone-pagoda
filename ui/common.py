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
            --radius-card: 4px;
            --radius-control: 4px;
            --radius-badge: 2px;
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
            margin-top: 1.75rem; margin-bottom: 32px;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: var(--radius-card);
            padding: 22px 32px 32px;
        }
        html, body, [class*="css"] {
            color: var(--ink);
            font-family: "Wooridaum", "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
                "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif;
        }

        h1 { font-size: 1.3rem !important; }

        /* --- 상단 유틸리티 바: 좌측 breadcrumb(시스템 내 위치) · 우측 사용자 정보 --- */
        .top-bar { display: flex; justify-content: space-between; align-items: center;
            padding: 0 0 10px 0; margin-bottom: 16px; border-bottom: 1px solid var(--line); }
        .top-bar .breadcrumb { font-size: 1.05rem; color: var(--ink); font-weight: 700; letter-spacing: -.01em; }

        /* --- 사용자 정보 칩 (상단바 우측) --- */
        .user-chip { display: flex; align-items: center; gap: 10px; }
        .user-chip .avatar { width: 30px; height: 30px; border-radius: 50%; flex: 0 0 auto;
            background: var(--accent); color: #ffffff; font-size: 0.72rem; font-weight: 700;
            display: flex; align-items: center; justify-content: center; }
        .user-chip .info { display: flex; flex-direction: column; line-height: 1.3; }
        .user-chip .info .name { font-size: 0.82rem; font-weight: 700; color: var(--ink);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
        .user-chip .info .role { font-size: 0.72rem; color: var(--ink-tertiary); }

        /* --- 사이드바 로고: 사이드바 상단, 가운데 정렬.
           음수 마진으로 가장자리까지 "빼내는" 방식 대신, 사이드바 자체의 좌우 padding을
           작은 값으로 직접 고정해 불필요한 여백을 없앤다 (아래 참고). --- */
        .sidebar-logo { display: flex; justify-content: center; align-items: center;
            padding: 8px 0; margin-top: -12px; margin-bottom: 14px; }
        .sidebar-logo img { height: 24px; display: block; }

        /* --- Streamlit 기본 헤더 툴바(Deploy/메뉴) 숨김 — 우리 상단 바와 중복되는 흰 띠 제거 --- */
        [data-testid="stHeader"] { display: none; }

        /* --- 사이드바: 좌우 padding을 직접 작은 값으로 고정해 왼쪽 여백을 줄인다.
           (이전에는 Streamlit 기본 padding을 음수 마진으로 "상쇄"하는 방식이었는데,
           그 기본값이 환경마다 달라 보더가 안 보이거나 여백이 크게 남는 문제가 있었다.
           이제 모든 사이드바 요소가 padding만으로 일관되게 정렬된다.) --- */
        [data-testid="stSidebarContent"] {
            padding-top: 0.75rem;
            padding-left: 10px !important;
            padding-right: 10px !important;
        }
        [data-testid="stSidebarHeader"] { height: 30px !important; min-height: 30px !important; }
        [data-testid="stSidebarUserContent"] { padding-bottom: 12px !important; }
        /* 펼쳐진 상태에서만 폭을 좁히고, 접힌 상태(aria-expanded="false")는 강제하지 않는다.
           그래야 사이드바를 접었을 때 본문이 그만큼 다시 채워진다. */
        [data-testid="stSidebar"][aria-expanded="true"] { min-width: 230px !important; width: 230px !important; }
        [data-testid="stSidebar"][aria-expanded="true"] > div { width: 230px !important; }
        [data-testid="stSidebar"][aria-expanded="false"] { min-width: 0 !important; width: 0 !important; }
        /* --- 섹션 헤더: 하단 보더로 구획을 명확히 구분 --- */
        .section-header { display: flex; align-items: center; gap: 10px;
            font-size: 1rem; font-weight: 700; color: var(--ink); margin: 22px 0 10px 0; }
        .section-header .bar { width: 3px; height: 15px; background: var(--accent);
            border-radius: 2px; flex: 0 0 auto; }
        .section-header .label { white-space: nowrap; }
        .section-header .rule { flex: 1 1 auto; height: 1px; background: var(--line); }
        .section-header.first { margin-top: 4px; }

        /* --- 카드: 좌측 accent 보더로 강조. Apple 시스템처럼 그림자 없이 보더만으로 구분 --- */
        .pick-card { background: var(--surface); border: 1px solid var(--line); border-left: 3px solid var(--accent);
            border-radius: var(--radius-card); padding: 18px 20px; }
        .pick-card .title { font-size: 1.1rem; font-weight: 700; color: var(--ink); margin-top: 10px; }
        .pick-card .score-badge { display: inline-block; background: var(--accent); color: #ffffff;
            font-weight: 700; padding: 5px 14px; border-radius: var(--radius-badge); font-size: 0.88rem;
            letter-spacing: .01em; font-variant-numeric: tabular-nums; }

        /* --- 상태 태그 (배지): 각진 라벨 형태, 소프트 컬러 --- */
        .badge { display: inline-block; padding: 3px 10px; border-radius: var(--radius-badge);
            font-size: 0.75rem; font-weight: 600; }
        .badge-ok { background: var(--ok-bg); color: var(--ok); }
        .badge-warn { background: var(--warn-bg); color: var(--warn); }
        .badge-info { background: var(--accent-weak); color: var(--accent); }

        /* --- 근거 블록: 근거 코드(evidenceRef)는 기술적 식별자이므로 모노스페이스로 구분 --- */
        .ev-block { background: var(--surface-muted); border-radius: var(--radius-control);
            padding: 10px 14px; margin: 6px 0; font-size: 0.86rem; color: var(--ink); }
        .ev-block code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.82em; background: none; padding: 0; }

        /* --- 레코드 헤더: 라벨/값 필드 그리드 (ERP 상세화면 정보 블록 스타일) --- */
        .field-row { display: flex; gap: 28px; flex-wrap: wrap; margin-top: 12px; }
        .field-row .field { display: flex; flex-direction: column; gap: 4px; }
        .field-row .field-label { font-size: 0.68rem; font-weight: 700; color: var(--ink-tertiary);
            text-transform: uppercase; letter-spacing: .07em; }
        .field-row .field-value { font-size: 0.92rem; font-weight: 600; color: var(--ink);
            font-variant-numeric: tabular-nums; }

        /* --- 데이터 테이블: 업무 시스템 그리드 스타일 (헤더 행 + 줄무늬 행) --- */
        .data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .data-table th { text-align: left; font-size: 0.7rem; font-weight: 700; color: var(--ink-tertiary);
            text-transform: uppercase; letter-spacing: .06em; padding: 7px 12px;
            border-bottom: 1px solid var(--line); background: var(--surface-muted); }
        .data-table td { padding: 8px 12px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--ink); }
        .data-table tbody tr:last-child td { border-bottom: none; }
        .data-table tbody tr:nth-child(even) { background: var(--surface-muted); }
        .data-table td.num { text-align: right; font-weight: 700; color: var(--accent); white-space: nowrap;
            font-variant-numeric: tabular-nums; }
        .data-table td.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.76rem; color: var(--ink-tertiary); }

        /* --- 사이드바 진행 스테퍼: 업무 시스템 좌측 메뉴처럼 STEP 번호 + 라벨,
           원형 도트 대신 좌측 보더로 현재 위치를 표시 --- */
        .stepper { margin: 4px 0 20px 0; }
        .step { padding: 7px 0 7px 10px; margin: 0 0 1px 0; border-left: 3px solid transparent; }
        .step-eyebrow { font-size: 0.66rem; font-weight: 700; color: var(--ink-tertiary);
            letter-spacing: .07em; margin-bottom: 2px; }
        .step-label { font-size: 0.86rem; color: var(--ink-tertiary); }
        .step-done .step-eyebrow { color: var(--ok); }
        .step-done .step-label { color: var(--ink-secondary); }
        /* 현재 단계에서만 좌측 컬러 보더를 표시한다 (완료/예정 단계는 보더 없음) */
        .step-current { border-left-color: var(--accent); }
        .step-current .step-eyebrow { color: var(--accent); }
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

        /* --- st.container(border=True): Streamlit 기본 보더 색/라운드 정리.
           기본 요소 간 gap(16px)도 줄여서 화면 전체 스크롤 길이를 줄인다. --- */
        div[data-testid="stVerticalBlock"] {
            border-radius: var(--radius-card);
            border-color: var(--line);
            gap: 10px;
        }

        /* --- Expander (보조/검증 정보) --- */
        div[data-testid="stExpander"] details { border-color: var(--line) !important; border-radius: var(--radius-control) !important; }
        div[data-testid="stExpander"] summary { font-size: 0.86rem; color: var(--ink-secondary); }

        /* --- 코드 블록 --- */
        div[data-testid="stCodeBlock"] { border-radius: var(--radius-control); }

        /* --- 구분선(st.markdown("---")): 기본 32px 여백은 과해서 축소 --- */
        hr { margin: 14px 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_bar(title_text: str, fc_id: str = "") -> None:
    """상단 유틸리티 바 — 좌측에 현재 단계/화면명, 우측에 로그인한 FC 정보.

    화면마다 반복되던 큰 페이지 제목(page_header)을 없애고 이 한 줄로
    대체해 스크롤 길이를 줄인다. 로고는 사이드바 상단에 있고
    (render_sidebar_logo), 여기엔 실제 데이터에 있는 담당 FC ID만
    표시한다(가상 인물명은 만들지 않음).
    """
    import streamlit as st

    initials = nfc(fc_id).split("-")[0] if fc_id else "FC"
    user_html = ""
    if fc_id:
        user_html = (
            '<div class="user-chip">'
            f'<span class="avatar">{initials}</span>'
            '<span class="info">'
            f'<span class="name">{nfc(fc_id)}</span>'
            '<span class="role">담당 컨설턴트</span>'
            "</span>"
            "</div>"
        )

    st.markdown(
        f'<div class="top-bar">'
        f'<span class="breadcrumb">{nfc(title_text)}</span>'
        f"{user_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_sidebar_logo() -> None:
    """사이드바 최상단 로고 스트립 — 사내 시스템 소속을 나타내는 브랜드 마크."""
    import base64
    from pathlib import Path

    import streamlit as st

    logo_path = Path(__file__).parent / "assets" / "dongyang_logo.png"
    if not logo_path.exists():
        return
    b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    st.markdown(
        f'<div class="sidebar-logo"><img src="data:image/png;base64,{b64}" alt="동양생명" /></div>',
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


def section_header(title: str, first: bool = False) -> None:
    """화면 내부 섹션 제목 — 좌측 accent bar + 텍스트 + 우측으로 이어지는 얇은 선."""
    import streamlit as st

    cls = "section-header first" if first else "section-header"
    st.markdown(
        f'<div class="{cls}"><span class="bar"></span>'
        f'<span class="label">{nfc(title)}</span><span class="rule"></span></div>',
        unsafe_allow_html=True,
    )


def render_stepper(steps: dict[str, str], current: str) -> None:
    """진행 단계를 3-state(완료/진행중/예정) 스테퍼로 렌더링."""
    import streamlit as st

    keys = list(steps.keys())
    current_idx = keys.index(current) if current in keys else 0

    rows = []
    for i, key in enumerate(keys):
        label = nfc(steps[key])
        if i < current_idx:
            state = "done"
        elif i == current_idx:
            state = "current"
        else:
            state = "upcoming"
        rows.append(
            f'<div class="step step-{state}">'
            f'<div class="step-eyebrow">STEP 0{i + 1}</div>'
            f'<div class="step-label">{label}</div>'
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
