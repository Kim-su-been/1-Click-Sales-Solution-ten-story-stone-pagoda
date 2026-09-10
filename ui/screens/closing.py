"""화면 3: 상담 완료 — 분석 결과·CRM 초안·Next Action·Transcript Evidence."""
from __future__ import annotations

import re
import unicodedata

import streamlit as st

import src.config as cfg
from src import demo_state
from src.data_loader import DataLoader
from ui.common import nfc, page_header, render_evidence, section_header


def _transcript_snippet(loader: DataLoader, evidenceRef: str) -> str:
    """#spk:N 을 실제 발화로 변환해 반환 (파일 줄 번호가 아니라 발화 순서)."""
    m = re.search(r"#spk:(\d+)$", (evidenceRef or "").strip())
    if not m:
        return ""
    u = loader.utter_by_spk(int(m.group(1)))
    return u.line if u else ""


def render(loader: DataLoader) -> None:
    page_header("상담 완료", "STEP 3 / 3 · 분석 및 마무리")

    # Runtime Conversation Analysis 결과로 교체 (Expected 미사용)
    from src.agents.orchestrator import run_demo_pipeline

    rt = run_demo_pipeline()
    analysis = rt.output.analysis_result
    crm = rt.output.crm_draft
    next_actions = rt.output.next_action_result["next_actions"]
    calendar = rt.output.next_action_result["calendar_candidate"]
    cust_id = rt.output.daily_pick["customer_id"]

    st.markdown(
        f'<div class="notice">{nfc(cfg.NOTICE_TEXT)}</div>',
        unsafe_allow_html=True,
    )

    # 상담 요약
    section_header("상담 요약", first=True)
    with st.container(border=True):
        st.write(nfc(analysis.get("ai_summary", "")))
        st.caption(
            f"총 {len(loader.transcript)} 발화 · Runtime Conversation Analysis 결과 (Transcript 근거 기반)"
        )

    # 고객 반응·관심·걱정·거절
    section_header("고객의 관심사항과 반응")
    st.markdown("**기존 보장내용 확인 요청**")
    for need in analysis["customer_needs"]:
        st.markdown(f"- {nfc(need['need'])}")
        render_evidence(need["evidence"], label="근거", key_prefix=f"need_{need['need'][:8]}")

    st.markdown("**보험료 및 갱신 걱정**")
    for c in analysis["concerns"]:
        st.markdown(f"- {nfc(c['concern'])}")
        render_evidence(c["evidence"], label="근거", key_prefix=f"concern_{c['concern'][:8]}")

    st.markdown("**추가 가입 의향 / 무관심**")
    for item in analysis["rejection_or_disinterest"]:
        st.markdown(f"- {nfc(item['item'])}")
        render_evidence(item["evidence"], label="근거", key_prefix=f"rej_{item['item'][:8]}")

    # 상담 결과
    section_header("고객 반응과 상담 결과")
    outcome = analysis["outcome"]
    st.markdown(
        f'<span class="badge badge-ok">{nfc(outcome["value"])}</span> '
        f'후속 상담 필요: <b>{"예" if analysis["followup_requested"]["needed"] else "아니오"}</b> · '
        f'희망 일시 <b>{analysis["followup_requested"].get("preferred_datetime", "")}</b>',
        unsafe_allow_html=True,
    )
    render_evidence(outcome["evidence"], label="결과 근거", key_prefix="outcome")

    # CRM 상담기록 초안
    section_header("CRM 상담기록 초안")
    status = crm.get("status", "DRAFT")
    phase = crm.get("phase", "FC_REVIEW")
    auto = crm.get("auto_finalized", False)
    st.markdown(
        f'<span class="badge badge-warn">status: <b>{status}</b> · phase: <b>{nfc(phase)}</b>'
        f' · auto_finalized: {"true" if auto else "false"}</span>',
        unsafe_allow_html=True,
    )
    st.caption(nfc(crm.get("note", "")))

    rec = crm["crm_record"]
    st.markdown(
        f"""
        - **상담 유형**: {nfc(rec.get('consultation_type',''))} · **일시**: {rec.get('consultation_datetime')}
        - **결과**: {nfc(rec.get('outcome',''))}
        - **고객 니즈**: {', '.join(nfc(x) for x in rec.get('customer_needs', []))}
        - **관심사**: {', '.join(nfc(x) for x in rec.get('customer_interests', []))}
        - **걱정**: {', '.join(nfc(x) for x in rec.get('concerns', []))}
        - **무관심**: {', '.join(nfc(x) for x in rec.get('disinterest_items', []))}
        - **후속 필요**: {'예' if rec.get('followup_needed') else '아니오'} ·
          **희망 일시**: {rec.get('preferred_datetime')}
        """
    )
    st.markdown("**Transcript Evidence (CRM Draft)**")
    render_evidence(crm["each_field_evidence"], label="CRM 필드별 근거", key_prefix="crm")

    # FC 확인 + Mock 저장 (Stage 3 Tool 연결)
    section_header("FC 확인 및 Mock 저장")
    session_id = demo_state.get_session_id()
    results = demo_state.get_tool_results()

    if demo_state.is_crm_confirmed():
        st.markdown(
            '<span class="badge badge-ok">FC 확인 완료</span> '
            '<span class="badge badge-info">CRM DRAFT / FC_REVIEW 유지</span>',
            unsafe_allow_html=True,
        )
        # Mock 저장 결과 표시
        for key, label in (("CRM_SAVED", "CRM 저장"), ("CALENDAR_SCHEDULED", "Calendar 등록"), ("FEEDBACK_STORED", "Feedback 저장")):
            res = results.get(key)
            if res:
                st.markdown(
                    f'<span class="badge badge-ok">【{label}】 성공 · '
                    f'{res.get("result_ref") or res.get("execution_id")}</span>',
                    unsafe_allow_html=True,
                )
        st.warning("실제 CRM·Calendar 시스템에는 저장되지 않았습니다. 모든 기록은 data/runtime/demo.db 의 Mock 데이터입니다.")
        if st.button("Demo 초기화 (내 기록만)", use_container_width=True):
            demo_state.reset_demo(all_data=False)
            st.rerun()
    else:
        st.caption("FC 확인 전에는 CRM 저장과 Calendar 등록이 차단됩니다.")
        # CRM Draft 수정 입력란 (FC 검토)
        draft_text = st.text_area(
            "CRM Draft 메모 수정 (선택)",
            value=demo_state.get_fc_draft_text() or nfc(crm.get("note", "")),
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
                calendar_title=calendar.get("title", "재상담 (Mock)"),
                calendar_due_datetime=cal_due,
                fc_action="ACCEPTED" if not draft_text or draft_text == nfc(crm.get("note", "")) else "EDITED",
                safety_result={"decision": "COMPLIANT"},
            )
            for k, v in out.get("results", {}).items():
                demo_state.set_tool_result(v.event_type, v.to_dict())
            if out.get("success"):
                demo_state.set_crm_confirmed(True)
            st.rerun()
        st.caption("버튼 클릭 시 Mock CRM 저장 → Mock Calendar 등록 → Feedback 저장이 순서대로 실행됩니다.")

    # Next Action
    section_header("Next Action")
    for act in next_actions:
        st.markdown(
            f"- **[{nfc(act['action_type'])}]** {nfc(act['title'])} — "
            f"due: {act.get('due_datetime')} · 상태: {nfc(act.get('status',''))}"
        )
    st.markdown("**캘린더 후보**")
    st.markdown(
        f"- {nfc(calendar.get('title',''))} — {calendar.get('due_datetime')} "
        f"({calendar.get('duration_minutes')}분) · 상태: {nfc(calendar.get('status',''))}"
    )
    render_evidence(calendar.get("evidence"), label="캘린더 근거", key_prefix="cal")

    # 처음으로 / Demo 초기화
    st.markdown("---")
    if st.button("처음으로 돌아가기", use_container_width=True):
        demo_state.reset_to_daily_pick()
        st.rerun()
    if st.button("Demo 초기화 (내 실행 기록 재시작)", use_container_width=True):
        demo_state.reset_demo(all_data=True)
        st.rerun()
    st.caption("Demo 초기화는 현재 세션의 Mock 실행 데이터만 삭제합니다. 고객 Seed·Expected·Knowledge 문서는 유지됩니다.")