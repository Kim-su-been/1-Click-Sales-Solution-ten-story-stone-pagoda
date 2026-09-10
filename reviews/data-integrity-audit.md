# QA 감사 보고서 — Data Integrity Auditor

> 감사자: 감사 1: Data Integrity Auditor (Build-time)
> 기준일: `DEMO_AS_OF_DATE = 2026-09-09` · 대상: 시드/예상 데이터 9종
> 실행 상태: 감사 에이전트 실행은 **승인 대기 후 취소**되어 주 감사 에이전트가 동일 검토 절차를 수행

---

## 1. 검사 대상 및 문법

| 항목 | 방법 | 결과 | 근거 |
|---|---|---|---|
| JSON 9개 존재 | 파일 시스템 확인 | **PASS** | 전부 존재 (아래 목록) |
| JSON 문법 | `json.load` | **PASS** | 9개 모두 파싱 성공 |
| `demo_as_of_date == 2026-09-09` | 최상위 키 확인 | **PASS** | customers/contracts/scoring_rules/daily_pick_expected |

**JSON 9개 목록**
1. `data/seed/customers.json`
2. `data/seed/contracts.json`
3. `data/seed/scoring_rules.json`
4. `data/expected/daily_pick_expected.json`
5. `data/expected/contact-script-expected.json`
6. `data/expected/safety-reject-expected.json`
7. `data/expected/session-analysis-expected.json`
8. `data/expected/crm-record-expected.json`
9. `data/expected/next-action-expected.json`

## 2. ID 참조 검증

| 검증 | 결과 | 근거 |
|---|---|---|
| `contracts[].customer_id ∈ customers[].customer_id` | **PASS** | 5건 전부 일치 (CTR-101~105) |
| `product_code` 존재 | **PASS** | TS-1001 / TS-2001 순서 일치 |
| `rider_id` 참조 | **PASS** | CTR-102(갱신형 특약)의 `rider_flag=true` + renewal_date 연결 |

## 3. 날짜 재계산 (기준일 2026-09-09)

| 항목 | 원본 날짜 | 계산 | 결과 |
|---|---|---|---|
| 갱신 D-Day | renewal_date `2026-10-11` | `(10/11 - 9/9).days = 32` | **PASS (D-32)** |
| 최근 접촉 경과 | last_contacted_at `2025-07-09` | 14개월 | **PASS (14개월)** |
| FC 변경 경과 | fc_changed_at `2025-10-09` | 11개월 | **PASS (11개월)** |

## 4. Rescue Score 규칙 재계산 (김동양 CUST-001)

| 규칙 | 적용 | 점수 |
|---|---|---|
| R1b (FC 변경 3<~<=12개월) | 적용 (11개월) | +20 |
| R2 (최근 접촉 12개월+) | 적용 (14개월) | +30 |
| R3a (갱신 45일 이내) | 적용 (D-32) | +25 |
| R4 (최근 6개월 상담 이력 없음) | 적용 (last_consultation_at=null) | +15 |
| R5 (연체) | 미적용 | 0 |
| **합계** | | **90** |

→ **PASS** (90점, 규칙 재계산 일치)

## 5. 하드코딩 / 파라미터 오염 검사

| 검증 | 결과 | 근거 |
|---|---|---|
| 김동양 이름/ID로 90 부여 로직 없음 | **PASS** | customers.json memo 에 점수 고정값 없음, 규칙 합산으로만 계산 |
| 보험료 금액 미사용 | **PASS** | `monthly_premium` 는 scoring_rules 어디에도 없음. R5는 `premium_status==OVERDUE`(연체 상태) 기반으로 금액과 무관. notes 에 '보험료 금액(월 보험료)은 점수에 사용하지 않음' 명시 |

## 6. Eligibility → Score → Pick 순서

| 항목 | 결과 |
|---|---|
| Eligibility 먼저 (CUST-002 동의 없음, CUST-003 민원) | **PASS** — 둘 다 INELIGIBLE, exclusion_reason 포함 |
| Ineligible은 rescue_score null + potential_score만 | **PASS** — (CUST-002: 95, CUST-003: 88) |
| Eligible(CUST-001,004,005) 중 최고점 1명 | **PASS** — 90 > 50 > 15, 김동양 선정 |

## 7. 발견 문제

- 없음 (모든 항목 PASS)

## 8. 총평

**PASS** — 데이터 무결성, 날짜·점수 재계산, Eligibility/Score/Pick 순서 모두 정합.