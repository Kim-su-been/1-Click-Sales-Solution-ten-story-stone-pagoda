# 1-Pick Rescue Agent — 데이터 계약 (Data Contracts)

> 작성 목적: 해커톤 MVP 구현 전, **시드 데이터·러닝타임 데이터·Evidence 모델** 간 계약을 확정한다.
> 기준일: `DEMO_AS_OF_DATE = 2026-09-09` (모든 날짜 계산의 기준. 시스템 현재 날짜 사용 금지, ISO 8601 `YYYY-MM-DD`)

---

## 1. Evidence 모델 (공통)

모든 자동 생성 결과는 근거를 증명할 수 있어야 한다. 결과 JSON의 가능한 경우 다음 3개 필드를 사용한다.

| 필드 | 의미 | 예시 |
|------|------|------|
| `evidenceType` | 근거 종류 (아래 표) | `CUSTOMER_DATA` |
| `evidenceRef` | 근거 출처(파일·섹션·발화) | `data/seed/customers.json`, `data/knowledge/renewal-faq.md#Q3`, `data/demo/consultation-transcript.txt#spk:14` |
| `evidenceText` | 근거가 된 원문(필요 시 그대로 복사) | `"[CUST-001] 그럼 다음 주 목요일 오후에..."` |

### 1.1 evidenceType 정의

| evidenceType | 의미 | 사용 시점 | 예시 출처 |
|--------------|------|-----------|-----------|
| `CUSTOMER_DATA` | 고객·계약 데이터 기반 근거 | **고객 선정**(Eligibility/Score/1-Pick, Contact Reason) | `data/seed/customers.json`, `data/seed/contracts.json` |
| `KNOWLEDGE_DOCUMENT` | 공식(가상) 상품자료 기반 근거 | **상품 설명**(스크립트·근거 연결) | `data/knowledge/product-guide.md#...`, `terms.md#...`, `renewal-faq.md#...`, `sales-cautions.md#...` |
| `TRANSCRIPT` | 상담 원문 기반 근거 | **고객 관심사·후속 일정·CRM Draft** | `data/demo/consultation-transcript.txt#spk:6` |
| `EXECUTION_LOG` | 런타임 실행 기록 기반 근거 | **향후 구현 단계에서만 사용** (이 설계 문서에 정의만 함) | `execution_log` 런타임 레코드 |

> **규칙:** `EXECUTION_LOG` 는 아직 존재하지 않는 런타임 개념이다. 이번 단계에서 생성하는 expected 데이터는 제외하고 `CUSTOMER_DATA` / `KNOWLEDGE_DOCUMENT` / `TRANSCRIPT` 만 evidenceType 으로 사용한다.

### 1.2 근거 할당 매트릭스 (어떤 결과에 어느 evidenceType)

| 결과 | evidenceType |
|------|--------------|
| 고객 선정 (1-Pick, 스코어, Contact Reason) | `CUSTOMER_DATA` |
| 상품 설명 / 스크립트 문장 / 갱신 안내 | `KNOWLEDGE_DOCUMENT` |
| 고객 관심사항 / 니즈 / 거절 / 후속 일정 / CRM Draft | `TRANSCRIPT` |
| (런타임) 추천-연락 실행 로그 | `EXECUTION_LOG` (미래) |

---

## 2. 시드 데이터 (data/seed/)

### 2.1 customers.json
```json
{
  "demo_as_of_date": "2026-09-09",
  "customers": [
    {
      "customer_id": "CUST-001",
      "name": "김동양",
      "birth_year": 1981,
      "sex": "F",
      "phone": "010-0000-0001",
      "consent_channels": ["CALL", "SMS", "KAKAO"],
      "active_complaint": false,
      "complaint_detail": null,
      "fc_id": "FC-001",
      "previous_fc_id": "FC-OLD-9",
      "fc_changed_at": "2025-10-09",
      "last_contacted_at": "2025-07-09",
      "last_consultation_at": null,
      "memo": "데모 주인공: 담당 FC 변경 11개월·최근 접촉 14개월 전·갱신 D-32"
    }
  ]
}
```

### 2.2 contracts.json
```json
{
  "demo_as_of_date": "2026-09-09",
  "contracts": [
    {
      "contract_id": "CTR-101",
      "customer_id": "CUST-001",
      "product_code": "TS-1001",
      "product_name": "10층석탑 종신보험(가상)",
      "contract_type": "WHOLE_LIFE",
      "status": "ACTIVE",
      "monthly_premium": 120000,
      "premium_status": "NORMAL",
      "rider_flag": false,
      "started_at": "2018-03-15",
      "renewal_date": null,
      "maturity_date": null
    },
    {
      "contract_id": "CTR-102",
      "customer_id": "CUST-001",
      "product_code": "TS-2001",
      "product_name": "10층석탑 갱신형 암·입원 보장 특약(가상)",
      "contract_type": "RIDER",
      "status": "ACTIVE",
      "monthly_premium": 32000,
      "premium_status": "NORMAL",
      "rider_flag": true,
      "started_at": "2021-10-11",
      "renewal_date": "2026-10-11",
      "maturity_date": null
    }
  ]
}
```

### 2.3 scoring_rules.json

| rule_id | 조건 | points | category |
|---------|------|--------|----------|
| R1a | FC 변경 후 3개월 이내 | +25 | 고객관리필요성 |
| R1b | FC 변경 후 3개월 초과~12개월 | +20 | 고객관리필요성 |
| R2 | 최근 접촉 후 12개월 이상 경과 | +30 | 계약유지위험 |
| R3a | 갱신일까지 45일 이내 | +25 | 시점적절성 |
| R3b | 갱신일까지 46~60일 | +20 | 시점적절성 |
| R4 | 최근 6개월 내 상담 이력 없음 | +15 | 고객관리필요성 |
| R5 | 보험료 연체 1회 이상 | +3 | 계약유지위험 |

- **보험료 금액(원)은 어떠한 규칙에서도 사용하지 않는다.**
- 조건의 "개월/일" 계산은 `DEMO_AS_OF_DATE(2026-09-09)` 기준 월/일 차이로 한다.

### 2.4 Eligibility 조건 (customers.json 기반)

| 조건 | INELIGIBLE 사유 |
|------|-----------------|
| `consent_channels` 가 비어 있음 | `CONTACT_CONSENT_NONE` |
| `active_complaint == true` | `ACTIVE_COMPLAINT` |

- 처리 순서 고정: **① Eligibility Check → ② Eligible 만 Rescue Score 계산 → ③ 최고 점수 1명 Pick**
- Ineligible: `rescue_score=null`, `potential_score`(참고 계산값) 만 표시, 반드시 `exclusion_reason` 포함

### 2.5 daily_pick_expected.json (예상 결과)

- `candidates`: 고객 5명 전원 (eligibility / exclusion_reason / rescue_score / potential_score / score_breakdown)
- `daily_pick`: Eligible 중 최고 점수 1명 (데모 기준 **CUST-001 김동양 90점**)
- `evidence.type = CUSTOMER_DATA`

---

## 3. Knowledge 문서 (data/knowledge/)

| 파일 | 내용 | 앵커 |
|------|------|------|
| `product-guide.md` | 가상 상품설명서 (TS-1001·TS-2001) | `#ts2001-renewal` 등 |
| `terms.md` | 가상 약관 일부 (T-1~T-6) | `#T2-renewal-premium` 등 |
| `renewal-faq.md` | 갱신 안내 FAQ (Q1~Q5) | `#Q1`~`#Q5` |
| `sales-cautions.md` | 판매 유의사항·금지/허용 표현 | `#safety-forbidden`, `#safety-allowed` |

- **모든 .md 첫 줄:** "본 문서는 1-Pick Rescue Agent 해커톤 시연을 위한 가상 자료이며 실제 보험상품의 약관 또는 상품설명서가 아닙니다."
- 스크립트의 각 문장은 `evidenceRef: data/knowledge/<file>#<anchor>` 로 1:1 연결되어야 한다.

---

## 4. 상담 데이터 (data/demo/)

| 파일 | 내용 |
|------|------|
| `consultation-transcript.txt` | [화자] 발화 형식 17발화 (CUST-001·FC-001) |

- 발화 인덱스: 파일 첫 발화부터 `spk:1` ... `spk:17`. `evidenceRef: data/demo/consultation-transcript.txt#spk:14` 형식.
- `spk:6`=보장내용 확인 요청, `spk:8`=갱신 보험료 걱정, `spk:10`=추가 가입 의향 낮음, `spk:12`=치아보험 무관심, `spk:14`=다음 주 목요일 오후 재상담, `spk:17`=FC 마무리.

---

## 5. 상담 결과·CRM·Next Action (data/expected/)

### 5.1 session-analysis-expected.json
```json
{
  "demo_as_of_date": "2026-09-09",
  "analysis": {
    "outcome": { "value": "상담_성공", "evidence": { "evidenceType": "TRANSCRIPT", "evidenceRef": "...#spk:17", "evidenceText": "..." } },
    "customer_needs": [ { "need": "기존 계약 보장내용 점검", "evidence": { ... } } ],
    "concerns": [ { "concern": "갱신_보험료_부담", "evidence": { ... } } ],
    "followup_requested": { "needed": true, "preferred_datetime": "2026-09-17T14:00:00", "evidence": { ... } }
  }
}
```
- **모든 분석 필드는 반드시 TRANSCRIPT evidence 를 포함**해야 한다.

### 5.2 crm-record-expected.json
- `status: "DRAFT"`, `phase: "FC_REVIEW"`, `auto_finalized: false`, `fc_confirm_required: true`
- **CRM 기록은 초안(DRAFT)이며 FC 확인 후에만 SAVED로 저장**된다 (자동 확정 금지).
- 각 필드마다 TRANSCRIPT evidence 연결.

### 5.3 next-action-expected.json
- `next_actions[]`: action_id / action_type / title / due_datetime / status(`SUGGESTED`) / evidence
- `calendar_candidate`: 재상담 후보, `due_datetime: 2026-09-17T14:00:00`, `status: PENDING_FC_CONFIRM`
- 모든 항목에 TRANSCRIPT evidence.

---

## 6. 런타임 데이터 (data/app.db 등 — 향후 구현)

> 이번 단계에서는 런타임 DB 를 만들지 않는다. 아래는 **구현 단계에서 적용할 계약**이다.

| 테이블 | 주요 필드 |
|--------|-----------|
| daily_picks | pick_id, pick_date, customer_id, rescue_score, score_breakdown, contact_reason, grounding_docs, compliance_status, script_call, script_sms, status |
| contacts | contact_id, pick_id, channel, attempt_at, status, outcome_note |
| conversations | conversation_id, pick_id, customer_id, started_at, ended_at, transcript |
| consultation_results | conversation_id, outcome, needs, interests, rejection, followup, ai_summary, crm_draft |
| next_actions | action_id, conversation_id, action_type, due_datetime, status |
| feedback_events | event_id, pick_id, conversation_id, fc_action, outcome |
| execution_log | log_id, pick_id, agent, tool, called_at, input_ref, output_ref, status |

- `execution_log` 는 런타임에서 추천·연락·분석 실행 기록을 증명하기 위해 사용한다. **evidenceType `EXECUTION_LOG` 는 이 테이블 레코드에서만 사용**한다.

---

## 7. 검증 방법 (파일 수준)

1. 모든 `.json` 은 `python3 -c "import json; json.load(open(...))"` 로 문법 검증
2. `contracts[].customer_id` 는 반드시 `customers[].customer_id` 에 존재
3. `evidenceRef` 의 파일·앵커는 실제 존재 (파일 기준)
4. `evidenceText` 는 `consultation-transcript.txt` 원문과 문자 그대로 일치
5. Rescue Score 는 `scoring_rules.json` 규칙을 `DEMO_AS_OF_DATE` 로 재계산한 값과 일치

---

## 8. Runtime Status Contract (확정 — Stage 2)

> 아래 상태값은 `data/expected/*.json`(Golden)과 본 문서 5절의 기존 계약을
> 코드 작성 전 추출·대조해 확정한 **읽기 전용 상태 계약**이다.
> 각 영역의 상태는 **별도 Namespace**로 관리한다 (다른 영역을 하나의 Enum으로 합치지 않는다).

### 8.1 Orchestrator Workflow State (WorkflowState)

`docs/implementation-plan.md` 9절의 상태 전이에서 원용.

| 상태 | 의미 |
|------|------|
| `IDLE` | 시작 전 / 사이클 완료 후 대기 |
| `POOL_SCAN` | 고객 Pool 탐색 |
| `SCORING` | Eligibility → Rescue Score 계산 |
| `PICK_READY` | 1-Pick 선정 완료 |
| `GROUNDING` | Knowledge 검색·스크립트 생성 중 |
| `SAFETY_CHECK` | 금지표현·근거 검증 중 |
| `CONTACT_READY` | Mock 연락 준비 완료 |
| `TRANSCRIPT_READY` | Transcript 확보 |
| `ANALYSIS` | 상담 분석 중 |
| `CRM_DRAFT` | CRM 초안 생성 완료 |
| `NEXT_ACTION` | Next Action 생성 완료 |
| `FEEDBACK` | Safety Reject 후 FC 검토 또는 스크립트 수정이 필요한 상태 (CRM 저장·모델 재학습 완료 상태가 아님) |
| `DONE` | Runtime Agent 의 추천·스크립트·상담 분석·CRM Draft·Next Action **생성 작업이 완료**된 상태. CRM 저장 완료를 뜻하지 않음 |

> **DONE / FEEDBACK 의미 확정 (Stage 2 정리):**
> - `WorkflowState.DONE` 은 Runtime Agent 가 한 사이클의 산출물(1-Pick·스크립트·상담 분석·CRM Draft·Next Action)을
>   모두 **생성 완료**했음을 의미한다. **실제 CRM 저장 또는 Calendar 등록이 완료되었다는 의미가 아니다.**
> - CRM 의 실제 상태는 `CrmStatus`(`DRAFT`) / `CrmPhase`(`FC_REVIEW`) 필드가 담당한다.
> - Calendar 의 실제 상태는 `ActionStatus`(`SUGGESTED` / `PENDING_FC_CONFIRM`) 필드가 담당한다.
> - FC 확인(`fc_confirm_required=true`) 전에는 실제 CRM 저장 또는 Calendar 등록이 수행되지 않는다.
> - `WorkflowState.FEEDBACK` 은 Safety `REJECTED` 판정 이후 FC 검토 또는 스크립트 재작성이 필요한 상태이다.
>   CRM 저장이나 모델 재학습 완료 상태가 아니다.
> - 이번 정리에서는 WorkflowState 값을 추가·변경하지 않는다.

### 8.2 Streamlit 화면 상태 (Screen)

`src/demo_state.py` 의 스크린 상수 (Stage 1 확정).

| 값 | 의미 |
|----|------|
| `DAILY_PICK` | 오늘의 1-Pick 화면 |
| `CONSULTATION` | 상담 진행 화면 |
| `CLOSING` | 상담 완료 화면 |

### 8.3 Grounding/Safety 판정 상태 (SafetyDecision)

`contact-script-expected.json`·`safety-reject-expected.json` 에서 확인.

| 영역 | 값 |
|------|----|
| `review_result.decision` | `COMPLIANT` (정상 통과) / `REJECTED` (차단) |
| `violation_type` | `THREAT_PRESSURE` / `UNGROUNDED_CLAIM` / `EXAGGERATION` |
| `grounding_status` | `MISSING` (근거 없음) / `GROUNDED` (근거 연결됨) |

### 8.4 CRM Record 상태 (CrmStatus, CrmPhase — 분리 관리)

| 필드 | 값 |
|------|----|
| `status` | `DRAFT` (MVP 에서 유일, 자동 확정 금지) |
| `phase` | `FC_REVIEW` (MVP 에서 유일, 검토 단계) |
| `auto_finalized` | `false` |
| `fc_confirm_required` | `true` |

> **주의:** `DRAFT/FC_REVIEW` 표시는 하나의 복합 문자열이 아니라 **`status`와 `phase` 두 필드 값을 UI에서 결합해 표시한 것**이다.

### 8.5 FC Review / Confirmation 상태 (FcConfirmation)

| 필드 | 값 |
|------|----|
| `fc_confirm_required` | `true` |
| `FC_CONFIRM_ACTIONS` | `CONFIRM`(확인) / `EDIT`(수정) — UI session_state 플래그 |
| `SAVED` | 실제 저장은 이후 Mock Tool 단계에서만 사용 (이번 단계 사용 금지) |

### 8.6 Calendar / Next Action 상태 (ActionStatus)

| 영역 | 값 |
|------|----|
| `next_actions[].status` | `SUGGESTED` (MVP 유일) |
| `calendar_candidate.status` | `PENDING_FC_CONFIRM` (MVP 유일) |
| `due_datetime` | `2026-09-17T14:00:00` (후속 재상담 희망 일시, ISO 8601) |

> 확정 기준: 위 모든 값은 Golden Expected 6개 파일과 본 문서 5절 기존 계약에서
> 그대로 추출했으며 불일치가 없었다. 이 계약을 **MVP 최종 Status Contract**로 사용한다.

---

## 9. Runtime Tool Contract (확정 — Stage 3)

> 이번 단계에서 Tool(전화·문자·카카오톡·STT·CRM·Calendar·Feedback·Execution Log) 실행 결과를
> 기존 상태 Namespace와 **분리**해 정의한다. 분석 결과(Agent)와 실행 결과(Tool)는 구분한다.
> Tool 은 모두 Mock Adapter 로 구현한다 (실제 외부 API 호출 없음).

### 9.1 ToolExecutionResult (최소 공통 구조)

| 필드 | 의미 | 예시 |
|------|------|------|
| `execution_id` | 실행 고유 ID (idempotency 키) | `exec-call-9b2f` |
| `session_id` | 데모 실행 세션 ID | `demo-20260909-abc` |
| `tool_name` | 호출한 Tool 이름 | `channel_gateway` |
| `event_type` | 아래 9.2 의 이벤트 유형 | `CALL_STARTED` |
| `success` | 성공 여부 | `true` |
| `executed_at` | 실행 시각 (ISO 8601) | `2026-09-09T11:00:00` |
| `result_ref` | 저장 결과 참조 (record_id 등) | `rec-crm-0001` |
| `error_code` | 실패 코드 (없으면 null) | `SAFETY_BLOCKED` |
| `error_message` | 실패 설명 (없으면 null) | `스크립트가 Safety REJECTED` |

### 9.2 event_type 목록 (한정)

| event_type | 의미 | 산출 Tool |
|------------|------|----------|
| `CALL_STARTED` | Mock 전화 시작 | channel_gateway.start_call |
| `CALL_COMPLETED` | Mock 전화 종료 | channel_gateway.complete_call |
| `SMS_SENT` | Mock 문자 발송 | channel_gateway.send_sms |
| `KAKAO_SENT` | Mock 카카오톡 발송 | channel_gateway.send_kakao |
| `POSTPONED` | 오늘의 1-Pick 연락 보류(나중에) | channel_gateway.postpone |
| `STT_COMPLETED` | Mock STT 완료 (transcript 반환) | stt.transcribe |
| `FC_CONFIRMED` | FC 확인 완료 | orchestrator.confirm_and_execute |
| `CRM_SAVED` | Mock CRM 저장 | crm.save_confirmed_draft |
| `CALENDAR_SCHEDULED` | Mock Calendar 등록 (오표기 아님, 계약대로) | calendar.schedule_confirmed_action |
| `FEEDBACK_STORED` | Feedback 저장 | feedback_store |

> **예:** `CALENDAR_SCHEDULED` 는 계약상 event_type 명칭이다 (SCHEDULED 철자).

### 9.3 Tool Gate 규칙

- Channel Gateway 는 Safety `COMPLIANT` 스크립트만 실행 가능. `REJECTED` 는 `SAFETY_BLOCKED` 로 거부.
- CrmTool / CalendarTool 은 `fc_confirmed=true` 인 경우에만 실행. 아니면 `FC_NOT_CONFIRMED` 로 거부.
- 동일 `session_id` + `event_type` 에 대한 반복 호출은 중복 저장하지 않는다 (idempotency).

### 9.4 EXECUTION_LOG evidenceType 사용

- `EXECUTION_LOG` evidenceType 은 이번 Runtime 실행기록(execution_logs 테이블)부터 사용 가능.
- 기존 `data/expected/**` 에는 EXECUTION_LOG 를 추가하지 않는다 (Golden 수정 금지).