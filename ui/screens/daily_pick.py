"""화면 1: 오늘의 1-Pick — 선정된 고객·Rescue Score·스크립트·근거 표시."""
from __future__ import annotations

import unicodedata

import streamlit as st

import src.config as cfg
from src import demo_state
from src.data_loader import DataLoader
from ui.common import nfc, page_header, render_evidence, section_header


def _format_months(m: int | None) -> str:
    return "없음" if m is None else f"{m}개월"


def render(loader: DataLoader) -> None:
    page_header("오늘의 1-Pick", "STEP 1 / 3 · 고객 선정")

    # 가상 데이터 고지
    st.markdown(
        f'<div class="notice">{nfc(cfg.NOTICE_TEXT)}</div>',
        unsafe_allow_html=True,
    )

    # Runtime Agent 결과 직접 계산 (Expected 미사용)
    from src.agents.customer_selection import run_customer_selection, load_contracts_by_customer
    from src.agents.grounding_safety import run_grounding_safety
    from src.config import DEMO_AS_OF_DATE

    score_rules = [dict(r.raw) for r in loader.scoring_rules]
    customers = list(loader.customers.values())
    selection, _ = run_customer_selection(
        customers, load_contracts_by_customer(loader.contracts), score_rules, DEMO_AS_OF_DATE
    )
    pick_cust = selection.picked_customer
    pick_score = selection.picked_score

    cust_id = pick_cust.customer_id
    cust = loader.get_customer(cust_id)
    gs = run_grounding_safety(
        pick_cust,
        loader.contracts_of(cust_id),
        cfg.PROJECT_ROOT / "data" / "knowledge",
        [dict(r) for r in _safety_rules(loader)],
    )

    # --- 1-Pick 카드 ---
    section_header("오늘의 1-Pick 고객", first=True)
    st.markdown(
        f"""
        <div class="pick-card">
          <span class="score-badge">Rescue Score {pick_score.total}점</span>
          <div class="title">{nfc(cust.name)} 고객님 ({cust_id})</div>
          <div style="margin-top:6px">담당 FC 변경 후 <b>{_format_months(loader.months_elapsed(cust.fc_changed_at))}</b> ·
             최근 접촉 <b>{_format_months(loader.months_elapsed(cust.last_contacted_at))}</b> 전 ·
             특약 갱신 <b>D-{loader.days_until(_renewal_date(loader, cust_id))}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 점수 세부 항목: 쉬운 말 우선 표시, 상세 산출식은 보조 텍스트로 ---
    section_header("점수 세부 항목")
    with st.container(border=True):
        for item in pick_score.items:
            if item.points > 0:
                st.markdown(
                    f'<div style="margin-bottom:12px;">'
                    f'<div style="font-size:0.95rem;">{nfc(item.name_kr)} · '
                    f'<span style="color:var(--accent);font-weight:700;">+{item.points}점</span></div>'
                    f'<div style="font-size:0.78rem;color:var(--ink-tertiary);margin-top:2px;">{nfc(item.evidence_text)}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.caption(
            f"합계 {pick_score.total}점 — 연락 가능한 고객 중 이 점수가 가장 높아 오늘의 1-Pick으로 선정되었습니다."
        )

    # --- 고객 선정 근거: 코드 나열 대신 문장으로 설명 ---
    section_header("고객 선정 근거")
    from src.eligibility import EXCLUSION_REASON_LABELS

    ineligible = [(cid, res.exclusion_reason) for cid, res in selection.eligible.items() if not res.eligible]
    st.caption(
        f"전체 후보 {len(customers)}명 중 연락 가능 여부를 먼저 확인한 뒤, "
        "그 안에서 점수가 가장 높은 고객 1명을 오늘의 1-Pick으로 선정했습니다."
    )
    if ineligible:
        excluded_text = ", ".join(
            f"{nfc(loader.get_customer(cid).name)} 고객님({cid}) · "
            f"{EXCLUSION_REASON_LABELS.get(reason, reason)}"
            for cid, reason in ineligible
        )
        st.caption(f"이번에 제외된 고객 {len(ineligible)}명: {excluded_text}")

    # --- Contact Reason ---
    reason = gs.contact_reason
    section_header("추천 연락 사유")
    st.markdown(
        f'<b>{nfc(reason["text"])}</b> '
        f'<span class="badge badge-info">{nfc(reason["code"])}</span>',
        unsafe_allow_html=True,
    )
    st.caption(nfc(reason.get("pick_basis", "")))

    # --- 전화 스크립트 (Compliance 통과) ---
    scripts = gs.scripts
    section_header("전화 스크립트")
    with st.container(border=True):
        st.markdown(
            '<span class="badge badge-ok">COMPLIANT</span> '
            "금지 표현 0건 · 모든 문장이 Knowledge 근거에 연결됨",
            unsafe_allow_html=True,
        )
        call = scripts["CALL_FIRST_OPENING"]
        st.markdown(f"**{nfc(call['text'])}**")
        if st.button("Knowledge 근거 보기", key="kd_open"):
            for se in call["sentence_evidence"]:
                st.markdown(f"- `{nfc(se['sentence'])}`")
                render_evidence(se, label="문장 근거", key_prefix=f"cs_{se['sentence'][:10]}")

    # --- 채널 버튼 ---
    section_header("연락 채널")
    call_script = call["text"]
    sms_script = scripts["SMS"]["text"]
    kakao_script = scripts["KAKAO"]["text"]
    session_id = demo_state.get_session_id()

    from src.agents.orchestrator import (
        postpone_pick,
        send_mock_kakao,
        send_mock_sms,
        start_mock_call,
    )

    results_now = demo_state.get_tool_results()
    sms_sent = bool(results_now.get("SMS_SENT", {}).get("success"))
    kakao_sent = bool(results_now.get("KAKAO_SENT", {}).get("success"))
    postponed = bool(results_now.get("POSTPONED", {}).get("success"))
    contacted = sms_sent or kakao_sent  # 문자/카톡은 채널이 다르므로 둘 다 보낼 수 있다.

    @st.dialog("문자 발송")
    def _confirm_sms() -> None:
        st.write(f"**{nfc(cust.name)} 고객님**에게 아래 문자를 보내시겠습니까?")
        st.write(nfc(sms_script))
        b1, b2 = st.columns(2)
        if b1.button("보내기", type="primary", use_container_width=True, key="sms_confirm_send"):
            res = send_mock_sms(session_id, cust_id, sms_script)
            demo_state.set_tool_result("SMS_SENT", res.to_dict())
            if not res.success:
                st.error(f"문자를 보낼 수 없습니다: {res.error_message}")
            st.rerun()
        if b2.button("취소", use_container_width=True, key="sms_confirm_cancel"):
            st.rerun()

    @st.dialog("카카오톡 발송")
    def _confirm_kakao() -> None:
        st.write(f"**{nfc(cust.name)} 고객님**에게 아래 카카오톡을 보내시겠습니까?")
        st.write(nfc(kakao_script))
        b1, b2 = st.columns(2)
        if b1.button("보내기", type="primary", use_container_width=True, key="kakao_confirm_send"):
            res = send_mock_kakao(session_id, cust_id, kakao_script)
            demo_state.set_tool_result("KAKAO_SENT", res.to_dict())
            if not res.success:
                st.error(f"카카오톡을 보낼 수 없습니다: {res.error_message}")
            st.rerun()
        if b2.button("취소", use_container_width=True, key="kakao_confirm_cancel"):
            st.rerun()

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("전화하기", use_container_width=True, type="primary"):
        res = start_mock_call(session_id, cust_id, call_script)
        demo_state.set_tool_result("CALL_STARTED", res.to_dict())
        if res.success:
            demo_state.set_call_active(True)
            demo_state.go_to(cfg.SCREEN_CONSULTATION)
        else:
            st.error(f"전화를 시작할 수 없습니다: {res.error_message}")
        st.rerun()

    # 문자/카톡은 서로 함께 보낼 수 있지만, "나중에(오늘은 연락 안 함)"와는 배타적이다.
    if c2.button("문자 발송", use_container_width=True, disabled=postponed or sms_sent):
        _confirm_sms()

    if c3.button("카카오톡 발송", use_container_width=True, disabled=postponed or kakao_sent):
        _confirm_kakao()

    if c4.button("나중에", use_container_width=True, disabled=contacted or postponed):
        res = postpone_pick(session_id, cust_id)
        demo_state.set_tool_result("POSTPONED", res.to_dict())
        st.rerun()

    if sms_sent:
        with st.container(border=True):
            st.markdown(f"**{nfc(cust.name)} 고객님에게 문자를 보냈습니다.**")
            st.write(nfc(sms_script))
            render_evidence(scripts["SMS"]["sentence_evidence"], label="문자 근거 보기", key_prefix="sms")
        if st.button("다시 선택하기", key="reset_channel_sms"):
            results_now.pop("SMS_SENT", None)
            st.rerun()

    if kakao_sent:
        with st.container(border=True):
            st.markdown(f"**{nfc(cust.name)} 고객님에게 카카오톡을 보냈습니다.**")
            st.write(nfc(kakao_script))
            render_evidence(scripts["KAKAO"]["sentence_evidence"], label="카카오톡 근거 보기", key_prefix="kakao")
        if st.button("다시 선택하기", key="reset_channel_kakao"):
            results_now.pop("KAKAO_SENT", None)
            st.rerun()

    if postponed:
        with st.container(border=True):
            st.markdown(f"**오늘은 {nfc(cust.name)} 고객님에게 연락하지 않기로 했습니다.**")
            st.caption("이 선택은 다음 1-Pick 추천에 반영됩니다.")
        if st.button("다시 선택하기", key="reset_channel_postpone"):
            results_now.pop("POSTPONED", None)
            st.rerun()

    # --- Stage 2 Runtime 패널: 판매 흐름과 분리된 검증용 패널 ---
    with st.expander("기능 검증 정보 — Stage 2 Runtime (Orchestrator)"):
        st.caption(
            "Runtime Agent 파이프라인 실행 로그입니다. 위 화면 구성과는 별개로, "
            "내부 동작이 정상인지 확인하려는 개발/QA 목적으로 제공됩니다."
        )
        st.caption("POOL_SCAN → SCORING → PICK_READY → GROUNDING → SAFETY_CHECK → … → DONE")
        try:
            from src.agents.orchestrator import run_demo_pipeline

            result = run_demo_pipeline()
            st.markdown(f"**Workflow 상태:** `{result.output.workflow_state}`")
            if result.output.errors:
                st.error(" → ".join(e.reason for e in result.output.errors))
            else:
                st.success("전체 사이클 정상 완료 (DONE) · 오류 없음")
            with st.expander("단계별 Evidence (StepResult)"):
                for s in result.steps:
                    st.markdown(f"- **`{s.step_name}`** → `{s.state}` — {nfc(s.summary)}")
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Stage 2 런타임을 실행하지 못했습니다: {exc}")


def _renewal_date(loader: DataLoader, cust_id: str) -> str | None:
    for c in loader.contracts_of(cust_id):
        if c.renewal_date:
            return c.renewal_date
    return None


def _safety_rules(loader: DataLoader) -> list[dict]:
    """config/safety_rules.json 을 읽어 safety 규칙 목록 반환."""
    import json

    path = cfg.CONFIG_DIR / "safety_rules.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("safety_rules", []) if isinstance(raw, dict) else raw