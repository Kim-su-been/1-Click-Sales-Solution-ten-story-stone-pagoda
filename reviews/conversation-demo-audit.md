# QA 감사 보고서 — Conversation and Demo Auditor

> 감사자: 감사 3: Conversation and Demo Auditor (Build-time)
> 기준일: `DEMO_AS_OF_DATE = 2026-09-09`
> 실행 상태: 감사 에이전트 실행은 **런타임 정책으로 실행 실패** → 주 감사 에이전트가 동일 절차로 대체 검토
> 대상: `data/demo/consultation-transcript.txt` + `data/expected/{session-analysis,crm-record,next-action}-expected.json` + `docs/demo-and-acceptance.md`

---

## 1. Transcript 분량

| 항목 | 값 | 결과 |
|---|---|---|
| 발화 수 | 17 (스피커 태그 라인) | **PASS** (1~2분 규모) |
| 통화 시작·종료 | 11:00~11:02 (2분) | **PASS** (`session-analysis-expected.json` call_meta) |

## 2. 발화 고유성

| 검사 | 결과 | 근거 |
|---|---|---|
| 발화 ID(spk:N) 중복 없음 | **PASS** | transcript 17발화 + evidenceRef spk 1~17 이 모두 유효범위 |
| 스피커 라인 중복 없음 | **PASS** | 각 라인 고유 |

## 3. evidenceRef → 실제 발화

| 파일 | refs | 결과 |
|---|---|---|
| session-analysis-expected.json | 8 | **PASS** (spk 6,8,10,12,14,17 등 전부 발화 인덱스 범위) |
| crm-record-expected.json | 4 | **PASS** |
| next-action-expected.json | 4 | **PASS** |

## 4. evidenceText 정확 일치

| 검사 | 결과 | 근거 |
|---|---|---|
| evidenceText가 transcript 원문과 문자 그대로 일치 | **PASS** | 16건 전부 `speaks[idx-1]` 에 정확히 포함 (화자 태그 제거 정규화 후 일치 확인) |

## 5. 필수 4종 내용 presence

| 항목 | transcript 근거 | 결과 |
|---|---|---|
| 기존 계약 보장내용 확인 요청 | "가입한 보험에서 입원하면 얼마나 보장되는지 정리해서 알려주실 수 있어요?" | **PASS** |
| 보험료·갱신 걱정 | "갱신되면 보험료가 오른다고 들었는데 걱정이 되네요." | **PASS** |
| 추가 가입 의향 낮음 | "새로 가입할 생각은 아직 없어요." | **PASS** |
| 후속 일정 (2026-09-17 오후) | "다음 주 목요일 오후에 다시 연락 주시면..." | **PASS** |

## 6. 후속 일정 날짜

| 대상 | 값 | 결과 |
|---|---|---|
| preferred_datetime (session/crm) | `2026-09-17T14:00:00` | **PASS** (오후) |
| ACT-001 / calendar_candidate due_datetime | `2026-09-17T14:00:00` | **PASS** |
| ACT-002 (자료 준비) | `2026-09-16T18:00` | PASS (보조 task, 9/17 전 준비 목표로 정합) |
| ACT-003 (갱신 안내 준비) | `2026-09-24T18:00` | PASS (D-32 前 30일 안내 준비로 정합) |

## 7. CRM DRAFT 상태

| 필드 | 값 | 결과 |
|---|---|---|
| status | `DRAFT` | **PASS** |
| phase | `FC_REVIEW` | **PASS** |
| auto_finalized | `false` | **PASS** |
| fc_confirm_required | `true` | **PASS** |
| note | "FC 확인 후 저장(SAVED)" | **PASS** |

## 8. 자동 저장/자동 확정 금지

| 검사 | 결과 |
|---|---|
| 초안 생성 후 FC 확인 없이 저장 없음 | **PASS** — `fc_confirm_required=true`, `auto_finalized=false`, CRM/Calendar 모두 `PENDING_FC_CONFIRM`/`SUGGESTED` 상태 |

## 9. 메인 데모 4:30

| 검사 | 결과 |
|---|---|
| 실행 4분 30초 + 버퍼 30초 (총 5분 이내) | **PASS** — `docs/demo-and-acceptance.md` 정상 시나리오 4:30 명시, 시간 배분 표 0:00~4:30 |

## 10. Safety Reject 분리

| 검사 | 결과 |
|---|---|
| Safety Reject가 보조(Backup) 시나리오로 별도 섹션 | **PASS** — "## 2. Safety Reject 시나리오 (Backup, 30초~1분)" 로 정상 흐름(1장)과 분리 |

## 11. 발견 문제

- 없음 (모든 항목 PASS)

## 12. 총평

**PASS** — Transcript-분석-후속-데모가 서로 정합하며, CRM 초안(비자동 확정)과 데모 4:30 규약을 준수.