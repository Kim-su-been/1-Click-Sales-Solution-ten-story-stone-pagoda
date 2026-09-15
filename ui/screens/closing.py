"""화면 3: 상담 완료 — 분석 결과·CRM 초안·Next Action·Transcript Evidence."""
from __future__ import annotations

import re
import unicodedata

import streamlit as st

from src import demo_state
from src.data_loader import DataLoader
from ui.common import (
    fmt_dt,
    humanize,
    nfc,
    render_data_table,
    render_evidence,
    render_item_evidence,
    section_header,
)


def _transcript_snippet(loader: DataLoader, evidenceRef: str) -> str:
    """#spk:N 을 실제 발화로 변환해 반환 (파일 줄 번호가 아니라 발화 순서)."""
    m = re.search(r"#spk:(\d+)$", (evidenceRef or "").strip())
    if not m:
        return ""
    u = loader.utter_by_spk(int(m.group(1)))
    return u.line if u else ""


def render(loader: DataLoader) -> None:
    # Runtime Conversation Analysis 결과로 교체 (Expected 미사용)
    from src.agents.orchestrator import run_demo_pipeline

    rt = run_demo_pipeline()
    analysis = rt.output.analysis_result
    crm = rt.output.crm_draft
    next_actions = rt.output.next_action_result["next_actions"]
    calendar = rt.output.next_action_result["calendar_candidate"]
    cust_id = rt.output.daily_pick["customer_id"]

    # 상담 요약
    section_header("상담 요약", first=True)
    with st.container(border=True):
        st.write(nfc(analysis.get("ai_summary", "")))
        st.caption(f"총 {len(loader.transcript)}개 발화를 분석한 결과입니다.")

    # 고객 반응·관심·걱정·거절 — 항목 텍스트를 펼치기 제목으로 써서 항목당 한 줄로 압축
    section_header("고객의 관심사항과 반응")
    st.markdown("**기존 보장내용 확인 요청**")
    for need in analysis["customer_needs"]:
        render_item_evidence(humanize(need["need"]), need["evidence"], key_prefix=f"need_{need['need'][:8]}")

    st.markdown("**보험료 및 갱신 걱정**")
    for c in analysis["concerns"]:
        render_item_evidence(humanize(c["concern"]), c["evidence"], key_prefix=f"concern_{c['concern'][:8]}")

    st.markdown("**추가 가입 의향 / 무관심**")
    for item in analysis["rejection_or_disinterest"]:
        render_item_evidence(humanize(item["item"]), item["evidence"], key_prefix=f"rej_{item['item'][:8]}")

    # 상담 결과
    section_header("고객 반응과 상담 결과")
    outcome = analysis["outcome"]
    st.markdown(
        f'<span class="badge badge-ok">{humanize(outcome["value"])}</span> '
        f'후속 상담 필요: <b>{"예" if analysis["followup_requested"]["needed"] else "아니오"}</b> · '
        f'희망 일시 <b>{fmt_dt(analysis["followup_requested"].get("preferred_datetime", ""))}</b>',
        unsafe_allow_html=True,
    )
    render_evidence(outcome["evidence"], label="결과 근거", key_prefix="outcome")

    # CRM 상담기록 초안
    section_header("CRM 상담기록 초안")
    status = crm.get("status", "DRAFT")
    phase = crm.get("phase", "FC_REVIEW")
    st.markdown(
        f'<span class="badge badge-warn">{humanize(status)} · {humanize(phase)}</span>',
        unsafe_allow_html=True,
    )
    st.caption(nfc(crm.get("note", "")))

    rec = crm["crm_record"]
    with st.container(border=True):
        render_data_table(
            ["항목", "내용"],
            [
                ["<b>상담 유형</b>", nfc(rec.get("consultation_type", "")) or "-"],
                ["<b>상담 일시</b>", fmt_dt(rec.get("consultation_datetime")) or "-"],
                ["<b>결과</b>", humanize(rec.get("outcome", ""))],
                ["<b>고객 니즈</b>", ", ".join(humanize(x) for x in rec.get("customer_needs", [])) or "-"],
                ["<b>관심사</b>", ", ".join(nfc(x) for x in rec.get("customer_interests", [])) or "-"],
                ["<b>걱정</b>", ", ".join(humanize(x) for x in rec.get("concerns", [])) or "-"],
                ["<b>무관심</b>", ", ".join(humanize(x) for x in rec.get("disinterest_items", [])) or "-"],
                [
                    "<b>후속 필요</b>",
                    ("예 · 희망 일시 " + fmt_dt(rec.get("preferred_datetime")))
                    if rec.get("followup_needed") else "아니오",
                ],
            ],
        )
    render_evidence(crm["each_field_evidence"], label="통화 근거 확인", key_prefix="crm")

    # FC 확인 + 저장
    section_header("FC 확인 및 저장")
    session_id = demo_state.get_session_id()
    results = demo_state.get_tool_results()

    if demo_state.is_crm_confirmed():
        st.markdown(
            '<span class="badge badge-ok">FC 확인 완료</span> '
            '<span class="badge badge-info">CRM 초안 · FC 검토 상태 유지</span>',
            unsafe_allow_html=True,
        )
        # 저장 결과 표시
        for key, label in (
            ("CRM_SAVED", "CRM에 저장되었습니다"),
            ("CALENDAR_SCHEDULED", "재상담 일정이 등록되었습니다"),
            ("FEEDBACK_STORED", "추천 결과가 기록되었습니다"),
        ):
            if results.get(key):
                st.markdown(f'<span class="badge badge-ok">{label}</span>', unsafe_allow_html=True)
        if st.button("다시 시작 (내 기록만 초기화)", use_container_width=True):
            demo_state.reset_demo(all_data=False)
            st.rerun()
    else:
        st.caption("FC 확인 전에는 CRM 저장과 Calendar 등록이 차단됩니다.")
        # CRM Draft 수정 입력란 (FC 검토)
        draft_text = st.text_area(
            "CRM 메모 수정 (선택)",
            value=demo_state.get_fc_draft_text() or nfc(crm.get("note", "")),
            height=180,
            key="fc_draft_edit",
        )
        if st.button("FC 확인 및 저장", type="primary", use_container_width=True):
            from src.agents.orchestrator import confirm_and_execute

            demo_state.set_fc_draft_text(draft_text)
            fc_draft = dict(crm.get("crm_record", {}))
            fc_draft["note"] = draft_text

            cal_due = calendar.get("due_datetime", "")
            out = confirm_and_execute(
                session_id=session_id,
                customer_id=crm["crm_record"].get("customer_id") or cust_id,
                fc_confirmed=True,
                crm_draft={
                    **crm,
                    "crm_record": fc_draft,
                },
                calendar_title=calendar.get("title", "재상담"),
                calendar_due_datetime=cal_due,
                fc_action="ACCEPTED" if not draft_text or draft_text == nfc(crm.get("note", "")) else "EDITED",
                safety_result={"decision": "COMPLIANT"},
            )
            for k, v in out.get("results", {}).items():
                demo_state.set_tool_result(v.event_type, v.to_dict())
            if out.get("success"):
                demo_state.set_crm_confirmed(True)
            st.rerun()
        st.caption("버튼을 클릭하면 CRM 저장 → 재상담 일정 등록 → 추천 결과 기록이 순서대로 처리됩니다.")

    # Next Action
    section_header("다음 할 일")
    for act in next_actions:
        st.markdown(
            f"- **{nfc(act['title'])}** — "
            f"예정일 {fmt_dt(act.get('due_datetime'))} · 상태: {humanize(act.get('status',''))}"
        )
    st.markdown("**재상담 일정 후보**")
    st.markdown(
        f"- {nfc(calendar.get('title',''))} — {fmt_dt(calendar.get('due_datetime'))} "
        f"({calendar.get('duration_minutes')}분) · 상태: {humanize(calendar.get('status',''))}"
    )
    render_evidence(calendar.get("evidence"), label="캘린더 근거", key_prefix="cal")

    # 처음으로 / Demo 초기화 — 두 번째 동작은 QA/데모 초기화 용도라 덜 눈에 띄게 나란히 배치
    st.markdown("---")
    col_reset1, col_reset2 = st.columns(2)
    with col_reset1:
        if st.button("처음으로 돌아가기", use_container_width=True):
            demo_state.reset_to_daily_pick()
            st.rerun()
    with col_reset2:
        if st.button("처음부터 다시 시작", use_container_width=True):
            demo_state.reset_demo(all_data=True)
            st.rerun()
    st.caption("초기화하면 현재 세션의 실행 기록만 삭제됩니다. 고객 데이터와 지식 문서는 유지됩니다.")