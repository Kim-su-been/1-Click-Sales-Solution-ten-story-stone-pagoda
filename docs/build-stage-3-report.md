# Stage 3 Runtime Tool 빌드 보고서

> 날짜: 2026-09-10 / 범위: Mock Communication·STT·CRM·Calendar·Feedback Tool 연결 → FC 확인 포함 End-to-End Demo 흐름 완성

## 1. 목표

Stage 2 의 Runtime Product Agent 4종은 유지한 채, 모든 외부 시스템을
**Tool Interface + Mock Adapter** 로 구현해 FC 확인까지 포함한 End-to-End Demo 흐름을 완성한다.

- 실제 전화·문자·카카오톡·STT·CRM·Calendar API 는 사용하지 않는다.
- 실제 LLM 도 사용하지 않는다.
- SQLite(`data/runtime/demo.db`)는 실제 사내 시스템을 대신하는 Demo Adapter 이다.

## 2. Runtime Tool Contract

`docs/data-contracts.md` 9절에 `Runtime Tool Contract` 를 확정했다.

- 최소 공통 구조: `execution_id` · `session_id` · `tool_name` · `event_type` · `success` · `executed_at` · `result_ref` · `error_code` · `error_message`
- event_type(한정): `CALL_STARTED` · `CALL_COMPLETED` · `SMS_SENT` · `KAKAO_SENT` · `STT_COMPLETED` · `FC_CONFIRMED` · `CRM_SAVED` · `CALENDAR_SCHEDULED` · `FEEDBACK_STORED`
- Tool Gate: Safety `COMPLIANT` 만 채널 실행, `fc_confirmed=true` 여야 CRM/Calendar 실행, 동일 (session_id, event_type) 반복 호출은 중복 저장 금지
- `EXECUTION_LOG` evidenceType 은 Runtime 실행기록부터 사용. `data/expected/**` 에는 추가하지 않음

## 3. 구현 산출물

```
src/tools/
  interfaces.py           Tool Interface (ChannelGateway·SttTool·CrmTool·CalendarTool·FeedbackStore·ExecutionLog)
  mock_channel.py         Mock 전화·문자·카카오톡 (Safety Gate 포함)
  mock_stt.py             Mock STT (data/demo/consultation-transcript.txt 반환)
  mock_crm.py             Mock CRM (FC 확인 전 거부)
  mock_calendar.py        Mock Calendar (FC 확인 전 거부)
  feedback_store.py       Feedback Store (승인/수정/거절 + 원본·수정 Draft·Safety·최종 실행)
  execution_log.py        Mock Execution Log (EXECUTION_LOG 근거)
src/runtime_db.py         SQLite Mock 저장소 (execution_logs·contact_attempts·crm_records·calendar_events·feedback_events)
src/agents/orchestrator.py  Tool 실행 메서드 추가 (start_mock_call·complete_mock_call·process_mock_stt·send_mock_sms·send_mock_kakao·confirm_and_execute·reset_demo_session)
ui/screens/*.py           3화면 Tool 연결 (전화·STT·FC 확인·Mock 저장·Demo 초기화)
docs/data-contracts.md    9절 Runtime Tool Contract
tests/                    Tool 단위·Safety Gate·Idempotency·End-to-End 8종
```

## 4. Tool Interface vs Mock Adapter

| Tool | Interface | Mock Adapter | Gate |
|---|---|---|---|
| Channel Gateway | `ChannelGateway` | `MockChannelGateway` | Safety COMPLIANT 만 (REJECTED → `SAFETY_BLOCKED`) |
| STT | `SttTool` | `MockSttTool` | — |
| CRM | `CrmTool` | `MockCrmTool` | `fc_confirmed=true` 만 (`FC_NOT_CONFIRMED`) |
| Calendar | `CalendarTool` | `MockCalendarTool` | `fc_confirmed=true` 만 (`FC_NOT_CONFIRMED`) |
| Feedback | `FeedbackStore` | `MockFeedbackStore` | — |
| Execution Log | `ExecutionLog` | `MockExecutionLog` | — |

## 5. SQLite Mock 저장소 (data/runtime/demo.db)

| 테이블 | 주요 필드 | 중복 방지 키 |
|--------|-----------|--------------|
| `execution_logs` | execution_id·session_id·tool_name·event_type·success·executed_at·result_ref·error_code·error_message | UNIQUE (session_id, event_type) |
| `contact_attempts` | attempt_id·session_id·customer_id·channel·event_type·script_text·success·executed_at | UNIQUE (session_id, event_type) |
| `crm_records` | record_id·session_id·customer_id·status·phase·payload·created_at | UNIQUE (session_id) |
| `calendar_events` | event_id·session_id·customer_id·title·due_datetime·status·created_at | UNIQUE (session_id) |
| `feedback_events` | event_id·session_id·fc_action·original_draft·revised_draft·safety_result·final_execution·stored_at | UNIQUE (session_id) |

## 6. Orchestrator Tool 연결

- `start_mock_call` → `CALL_STARTED`
- `complete_mock_call` → `CALL_COMPLETED`
- `process_mock_stt` → `STT_COMPLETED` (+ transcript 반환)
- `send_mock_sms` / `send_mock_kakao` → `SMS_SENT` / `KAKAO_SENT`
- `confirm_and_execute` → `FC_CONFIRMED` → Mock CRM 저장 → Mock Calendar 등록 → Feedback 저장
- `reset_demo_session` → 현재 session 의 Runtime Mock 데이터만 삭제 (Seed/Expected/Knowledge 무관)

Orchestrator 는 Tool 을 직접 구현하지 않고 Interface 를 통해 호출한다.

## 7. FC 확인 전후 동작 차이

| 동작 | FC 확인 전 | FC 확인 후 |
|------|-----------|-----------|
| CRM 저장 | 거부 (`FC_NOT_CONFIRMED`) | 성공 (`CRM_SAVED`, record_id 발급) |
| Calendar 등록 | 거부 (`FC_NOT_CONFIRMED`) | 성공 (`CALENDAR_SCHEDULED`, event_id 발급) |
| Feedback 저장 | — | 성공 (`FEEDBACK_STORED`) |
| UI 표시 | 저장 금지 안내 | record_id·event_id·실제 저장 아님 고지 |

## 8. Idempotency

- 동일 `session_id` + `event_type` 반복 호출 → 기존 `execution_id` 재사용 (`reused=true`)
- 동일 `session_id` CRM 중복 저장 → 동일 `record_id` 반환
- 동일 `session_id` Calendar 중복 등록 → 동일 `event_id` 반환
- FC 확인 버튼 중복 클릭 시에도 CRM 1건 · Calendar 1건만 생성

## 9. 검증 결과

- `python3 -m pytest -q` → **111 passed** (기존 83 + Stage 3 Tool/E2E 28)
- `python3 scripts/qa_audit.py` → 전 항목 OK
- `python3 scripts/qa_final_check.py` → 전 항목 OK
- Runtime 독립성 테스트 → 5 passed (Expected 미사용·하드코딩 없음)
- Streamlit headless → `/_stcore/health` **ok**
- UI 화면 전환(smoke_flow_test) → 에러 0, CONSULTATION 전환 정상

## 10. Golden Fixture 변경

**0건.** `data/seed/**`·`data/expected/**`·`data/knowledge/**`·`data/demo/consultation-transcript.txt` 수정 없음.
`data/runtime/demo.db` 는 Runtime 생성 파일로 `.gitignore` 에 추가했다.

## 11. 기존 상태 계약 변경

**없음.** Screen·WorkflowState·SafetyDecision·ViolationType·GroundingStatus·CrmStatus·CrmPhase·ActionStatus 는
변경하지 않았다. Tool 실행 결과는 별도 `ToolExecutionResult`(`Runtime Tool Contract`)로 표현한다.
`WorkflowState.DONE` 은 여전히 **Runtime Agent 생성 작업 완료**이며 CRM 저장 완료를 뜻하지 않는다.

## 12. 다음 단계 (UI 개선 및 최종 Demo 검증)

- 실제 LLM 연결 (규칙·키워드 → LLM 판단 전환)
- 실제 전화·문자·카톡·STT·CRM·Calendar 연동 (Mock Adapter → 실제 Adapter 교체)
- UI 디자인 고도화 (상태·Tool 결과 시각 구분 개선)
- 최종 Demo 검증 (사용자 핸즈온 시나리오)