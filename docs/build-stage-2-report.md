# Stage 2 Runtime 빌드 보고서

> 날짜: 2026-09-10 / 범위: Runtime Status Contract 동결 → Runtime Product Agent 4종(Orchestrator·Customer Selection·Grounding and Safety·Conversation Analysis) 구현 → Stage 1 UI Runtime 교체 → 검증

## 1. 목표

Stage 1(정적 Expected 데이터 기반 데모)을 넘어, **Orchestrator가 Runtime Product Agent 4종 구조로
1-Pick 선정 → 근거 확인(Grounding) → 안전 검토(Safety) → CRM Draft/Next Action 까지
Runtime 상태(WorkflowState)를 따라 실제 계산**하는 Stage 2 런타임을 구현한다.

> Build-time 감사 에이전트(감사용)와 Runtime Product Agent(런타임 내 논리적 역할)는 별개 개념이다.
> 이 문서에서 "Agent" 는 모두 Runtime Product Agent 를 말한다.

## 2. Gate 0: Runtime Status Contract 동결

`docs/data-contracts.md` 8절에 상태 계약을 확정했고, 코드(`src/runtime_models.py`)가 이를 그대로 따른다.

| 영역 | 값 | 비고 |
|---|---|---|
| Screen | `DAILY_PICK` / `CONSULTATION` / `CLOSING` | UI 화면 |
| WorkflowState | `IDLE→POOL_SCAN→SCORING→PICK_READY→GROUNDING→SAFETY_CHECK→CONTACT_READY→TRANSCRIPT_READY→ANALYSIS→CRM_DRAFT→NEXT_ACTION→DONE` | 오케스트레이션 (FEEDBACK 포함 13개) |
| SafetyDecision | `COMPLIANT` / `REJECTED` | `review_result.decision` |
| ViolationType | `THREAT_PRESSURE` / `UNGROUNDED_CLAIM` / `EXAGGERATION` | 안전 위반 3유형 |
| GroundingStatus | `GROUNDED` / `MISSING` | 대본 문장↔knowledge 근거 |
| CrmStatus / CrmPhase | `DRAFT` / `FC_REVIEW` | MVP 는 자동 확정 없음 (`auto_finalized=false`) |
| ActionStatus | `SUGGESTED` / `PENDING_FC_CONFIRM` | 일정: `2026-09-17T14:00:00` |

주의: WorkflowState `FEEDBACK` 은 Safety REJECT 시에만 진입하며 정상 사이클에서는
`NEXT_ACTION → DONE` 이 유효하다 (`is_valid_transition`).

### DONE / FEEDBACK 의미 확정

- `WorkflowState.DONE` = Runtime Agent 의 추천·스크립트·상담 분석·CRM Draft·Next Action **생성 작업 완료**.
  **CRM 저장 완료를 뜻하지 않는다.**
  - CRM 의 실제 상태는 `CrmStatus`(`DRAFT`) / `CrmPhase`(`FC_REVIEW`) 필드가 담당
  - Calendar 의 실제 상태는 `ActionStatus`(`SUGGESTED` / `PENDING_FC_CONFIRM`) 필드가 담당
  - FC 확인(`fc_confirm_required=true`) 전에는 실제 CRM 저장 또는 Calendar 등록이 수행되지 않음
- `WorkflowState.FEEDBACK` = Safety `REJECTED` 이후 FC 검토 또는 스크립트 재작성이 필요한 상태.
  CRM 저장이나 모델 재학습 완료 상태가 아니다.

> 이번 정리에서 WorkflowState 값은 추가·변경하지 않았다.
> 실제 CRM 저장·Calendar 등록은 아직 미구현(다음 Mock Tool 단계 대상).

## 3. 구현 산출물

```
src/
  runtime_models.py          상태 상수·전이 검증·Evidence/StepResult/Turn/Safety 모델
  eligibility.py             연락 동의·민원·계약 유효성 → INELIGIBLE 사유
  rescue_score.py            R1~R5 Rescue Score 계산 (보험료 금액 미사용)
  knowledge_search.py        knowledge/*.md 섹션 파싱·키워드 검색 (LLM 없음)
  safety_rules.py            금지 표현 규칙 기반 위반 감지 (SafetyCheckResult)
  transcript_parser.py       대본 → Turn 목록
  agents/
    orchestrator.py          Orchestrator: Runtime Agent 4종 파이프라인 실행·상태 전이 검증
    customer_selection.py    Customer Selection Agent: POOL_SCAN→SCORING→PICK_READY
    grounding.py             Grounding and Safety Agent 일부: 대본 claim ↔ evidenceRef
    safety.py                Grounding and Safety Agent 일부: SafetyCheckResult → COMPLIANT/REJECTED
    grounding_safety.py      Grounding and Safety Agent: Contact Reason·스크립트 생성·근거 연결
    conversation_analysis.py Conversation Analysis Agent: Transcript 분석·CRM Draft·Next Action
config/safety_rules.json      Safety 규칙 설정 (data/knowledge/sales-cautions.md 근거)
tests/test_stage2_runtime.py  검증 테스트 (17건)
```

> **Golden 파일 수정 0건**: `data/seed/customers.json`·`contracts.json`·`scoring_rules.json`,
> `data/expected/**`, `data/knowledge/**`, `data/demo/consultation-transcript.txt` 는 모두 수정하지 않았다.

### Stage 2 에서 신규 생성한 설정 파일

| 파일 | 용도 | 최종 위치 |
|---|---|---|
| `config/safety_rules.json` | 안전 규칙(금지 표현 4건) 설정 — `data/knowledge/sales-cautions.md` 가 공식 근거 | `config/` (Seed 영역 아님) |

- Safety 규칙의 공식 근거(document of record)는 `data/knowledge/sales-cautions.md` 로 유지한다.
- 결정론적 금지 표현 검출 로직은 `src/safety_rules.py` 가 담당한다.
- `config/safety_rules.json` 은 그 규칙을 런타임이 로드하는 설정 파일이다 (고객·계약 Seed 가 아님).
- 구 `data/seed/safety_rules.json` 은 제거했고, 관련 import·경로·테스트는 새 위치를 참조한다.

## 4. 검증 결과

### 4.1 자동 테스트
- `python3 -m pytest -q` → **83 passed** (기존 21 + Stage 2 17 + Golden 대조·독립성 45)
- `python3 -m compileall -q src/ ui/ app.py` → 성공
- `python3 scripts/qa_audit.py` → **evidenceRef 검증·evidenceText 일치 모두 OK**
- Streamlit headless 실행 → `/_stcore/health` **ok** (포트 8591, 정상 기동)

### 4.2 정상 사이클 (COMPLIANT)
`run_pipeline()` 실행 결과 (실제 Seed·Knowledge·Transcript 입력):

| 단계 | 상태 | 결과 |
|---|---|---|
| customer_selection | `PICK_READY` | eligible 3/5, 1-Pick=CUST-001(김동양), Rescue Score **90** |
| grounding | `GROUNDING` | claims=11, grounded=11 → **GROUNDED** |
| safety_review | `CONTACT_READY` | decision=**COMPLIANT**, violations=0 |
| contact_ready | `CONTACT_READY` | 1-Pick: 김동양 연락 준비 완료 |
| transcript_ready | `TRANSCRIPT_READY` | transcript_loaded=True |
| conversation_analysis | `ANALYSIS` | 상담 분석·관심사·후속 일정 추출 |
| crm_draft | `CRM_DRAFT` | status=`DRAFT`, phase=`FC_REVIEW`, fc_confirm_required=True |
| next_action | `NEXT_ACTION` | actions=`SUGGESTED`, calendar=`PENDING_FC_CONFIRM` |
| done | `DONE` | 전체 사이클 정상 완료 |

Runtime 출력과 Golden Expected 대조: `daily_pick` customer_id=`CUST-001`·name=`김동양`·rescue_score=**90** 일치.
Contact Reason `RENEWAL_PRENOTICE`(갱신 예정일 2026-10-11, D-32) — Golden 의미 일치.

Rescue Score 90 = R1b(+20) + R2(+30) + R3a(+25) + R4(+15) — `daily_pick_expected.json` 과 일치.
( R5 는 연체 계약 고객에게만 부여, CUST-001 해당 없음 )

### 4.3 SAFETY-REJECT 시나리오
`safety-reject-expected.json` 의 3문장 대본 검증:

| 문장 | violation_type |
|---|---|
| 지금 바꾸지 않으면 보장이 크게 줄어듭니다 | `THREAT_PRESSURE` |
| 이 상품은 보험료가 절대 오르지 않습니다 | `UNGROUNDED_CLAIM` |
| 세상에서 가장 좋은 보장입니다 | `EXAGGERATION` |

→ `decision=REJECTED` , 안전장치로 WorkflowState=`FEEDBACK` 진입 확인.

### 4.4 Grounding
- knowledge/*.md 4종 → 27개 섹션 파싱 (anchor `{#...}` 기준, evidenceRef 생성)
- 대본 FC 발화 11문장 모두 evidenceRef 연결 → `GROUNDED`

## 5. Stage 1 UI → Runtime Agent 결과 교체

UI Runtime 경로는 `data/expected` 를 더 이상 읽지 않으며, 전 화면이 Orchestrator(Agent) 결과를 공급받는다.

| 화면 | 공급원 | 표시 대상 |
|---|---|---|
| 오늘의 1-Pick (`daily_pick.py`) | Customer Selection + Grounding and Safety Agent | 1-Pick 고객·점수·Contact Reason·채널별 스크립트·Safety 결정 |
| 상담 진행 (`consultation.py`) | Orchestrator(CONTACT_READY→TRANSCRIPT_READY) | 준비된 Transcript 전달, 전화·STT 는 기존 Mock 유지 |
| 상담 완료 (`closing.py`) | Conversation Analysis Agent | 세션 분석·CRM Draft·Next Action·Transcript Evidence |

- 상태 표시는 기존 Golden Status Contract 값을 그대로 사용(사용자 표시 Label 과 원본 상태값을 함께 노출).
- 기존 3-화면 흐름(DAILY_PICK→CONSULTATION→CLOSING)은 그대로 유지 — 회귀 없음.

## 6. 남은 작업 (Stage 3+)
- 실제 외부 LLM API 연결 (현재 규칙·키워드 기반)
- 실제 전화 발신·문자/카카오톡 발송·STT·통화녹취 (현재 Mock)
- 실제 CRM 저장·FC 확인 확정·Calendar 등록 (현재 Draft/PENDING_FC_CONFIRM 대기)
- SQLite 영속 저장·Vector DB
- Product Agent(LLM) 연결 시 grounding/safety 를 확장 가능

## 7. 검증 명령
```bash
cd /Users/siyoung/Desktop/one-pick-rescue-agent
python3 -m pytest tests/ -q
python3 -m compileall -q src/ ui/ app.py
python3 -c "from src.agents.orchestrator import run_pipeline, _load_pipeline_input; from pathlib import Path; inp=_load_pipeline_input(Path('data')); r=run_pipeline(inp, saved_transcript=Path('data/demo/consultation-transcript.txt').read_text(encoding='utf-8')); print(r.output.workflow_state, r.output.daily_pick, r.output.errors)"
```