# 1-Pick Rescue Agent — 해커톤 데모 시나리오 및 인수 기준

> 본 문서는 1-Pick Rescue Agent 해커톤 시연(2026-09-09 기준일, DEMO_AS_OF_DATE=2026-09-09)을 위한 데모 스크립트와 인수 기준이다.

- **Demo 목표 실행 시간: 4분 30초** (나머지 30초는 화면 지연·발표 전환 버퍼 → 총 5분 이내)
- **데이터 원칙:** 모든 날짜 계산은 DEMO_AS_OF_DATE(2026-09-09) 기준. 시스템 현재 날짜 사용 금지.
- **Evidence 원칙:** 모든 자동 생성 결과는 근거(evidenceType: CUSTOMER_DATA / KNOWLEDGE_DOCUMENT / TRANSCRIPT)를 포함한다. EXECUTION_LOG는 런타임 구현 단계에서만 사용한다.

---

## 1. 정상 시나리오 (Normal Flow, 4:30)

### 1-1. 시간 배분

| 구간 | 시간 | 내용 |
|------|------|------|
| 1 | 0:00~0:35 | 오늘의 1-Pick 실행 및 김동양 고객 선정 |
| 2 | 0:35~1:15 | Rescue Score, 선정 이유, 고객 데이터 근거 (CUSTOMER_DATA) |
| 3 | 1:15~1:50 | 연락 스크립트와 Grounding 및 Safety 결과 (KNOWLEDGE_DOCUMENT) |
| 4 | 1:50~2:50 | Mock 전화와 준비된 Transcript 처리 |
| 5 | 2:50~3:50 | 상담 분석과 CRM Draft 생성 (TRANSCRIPT) |
| 6 | 3:50~4:20 | Next Action과 후속 일정 확인 |
| 7 | 4:20~4:30 | 추천-연락-상담-후속 Agent Loop 정리 |

### 1-2. 상세 흐름

1. **(0:00)** FC가 "오늘의 1-Pick 시작" 클릭
   → Orchestrator가 고아계약 고객 5명 스캔
   → **Eligibility Check** : CUST-002(연락 동의 없음)·CUST-003(민원 진행 중)은 INELIGIBLE로 후보 제외, rescue_score=null
   → **Rescue Score 계산** : Eligible 3명 중 CUST-001 김동양 90점 최고
   → **1-Pick 확정** : 김동양 1명 Action Card 표시 (이유 1줄 + 첫마디)
2. **(0:35)** Rescue Score breakdown 노출
   - 담당 FC 변경 11개월(+20) · 최근 접촉 14개월 전(+30) · 특약 갱신 D-32(+25) · 최근 상담 이력 없음(+15) = **90점**
   - 근거: `data/seed/customers.json`, `data/seed/contracts.json` (CUSTOMER_DATA)
   - Ineligible 고객의 potential_score(95·88)를 **참고 점수**로 표시해 "점수는 높지만 연락할 수 없는 고객" 설명
3. **(1:15)** 연락 스크립트 생성 + **Grounding and Safety Agent** 검증
   - 전화 첫마디·문자·카카오톡 초안이 Knowledge 문서(상품설명서·약관·FAQ)의 문장과 1:1 연결
   - 금지 표현(위협·과장·근거 없는 단정) 0건 → `COMPLIANT` 통과, 발송 버튼 활성화
   - 비교 데모: 근거 없는 스크립트("지금 바꾸지 않으면 보장이 크게 줄어듭니다")를 입력 → `REJECTED`
4. **(1:50)** **Mock 전화** 연결 → 시각·상태 자동 Tracking → 녹취(STT는 Mock, 준비된 Transcript 사용)
5. **(2:50)** Conversation Analysis Agent가 Transcript 분석
   - 보장내용 점검 요청·갱신 보험료 걱정·추가가입 의향 낮음·치아보험 무관심 추출
   - 모든 필드에 TRANSCRIPT evidence 표시
   - **CRM Draft 생성 (DRAFT / FC_REVIEW)** — 자동 확정 아님
6. **(3:50)** FC가 CRM 초안 확인 → [확인 및 등록] → **Next Action·캘린더 후보 생성**
   - 재상담(2026-09-17 14:00) · 보장내역 정리 자료 준비 · 갱신 사전 안내 확인
7. **(4:20)** 추천-연락-상담-후속 **Agent Loop** 정리 + 다음 추천 반영 (Feedback 저장) → 종료

### 1-3. 데모에서 강조할 메시지
- "목록이 아니라 **이유를 가진 한 명**"
- "AI가 만든 멘트가 아니라 **공식 자료에 근거한 멘트**"
- "전화를 거는 순간부터 **CRM 기록이 완성**된다 (FC는 초안을 검토만)"

---

## 2. Safety Reject 시나리오 (Backup, 30초~1분)

- 목적: **근거 없는 보험 설명 차단** 기능 시연
- 흐름:
  1. 스크립트 예시 1건 로드: "지금 바꾸지 않으면 보장이 크게 줄어듭니다. 이 상품은 보험료가 절대 오르지 않습니다."
  2. Grounding and Safety Agent가 검증 → 세 가지 위반 검출
     - `THREAT_PRESSURE` (위협·부추김) — sales-cautions 위반
     - `UNGROUNDED_CLAIM` (근거 없는 단정) — 약관 T-2와 대조
     - `EXAGGERATION` (과장) — 금지표현 위반
  3. 결과: **REJECTED** + 근거 ref 표시 + 교정 대안 문장 제시
- 근거 파일: `data/expected/safety-reject-expected.json`, `data/knowledge/sales-cautions.md#safety-forbidden`

---

## 3. 인수 기준 (Acceptance Criteria)

| # | 기준 | 통과 여부 |
|---|------|-----------|
| A1 | 김동양 고객 rescue_score 가 규칙 계산 결과 **90점** | 통과 |
| A2 | CUST-002(연락 동의 없음)가 daily_pick 후보에서 제외되고 rescue_score=null | 통과 |
| A3 | CUST-003(민원 진행 중)이 daily_pick 후보에서 제외되고 rescue_score=null | 통과 |
| A4 | 1-Pick 은 Eligible 고객 중 최고 점수 1명 (CUST-001) | 통과 |
| A5 | 상품 설명에 KNOWLEDGE_DOCUMENT 근거(evidenceRef)가 연결 | 통과 |
| A6 | 상담 분석 결과가 Transcript 실제 문장과 일치(문자 그대로) | 통과 |
| A7 | CRM 기록이 `DRAFT`/`FC_REVIEW` 이며 자동 확정 아님 | 통과 |
| A8 | Demo 총 실행 4분 30초 (5분 이내) | 통과 |
| A9 | Next Action·캘린더 후보가 2026-09-17 오후로 생성 | 통과 |
| A10 | Streamlit 앱·Product Agent 코드 미생성 (데이터·설계 단계) | 통과(대기) |

---

## 4. 데모 사전 준비물

- [ ] 샘플 데이터 5명 시드 (`data/seed/*.json`)
- [ ] Knowledge 문서 4종 (`data/knowledge/*.md`) — 첫 줄 가상 자료 문구 포함
- [ ] 준비된 Transcript (`data/demo/consultation-transcript.txt`)
- [ ] expected 결과 5종 (`data/expected/*.json`)
- [ ] Mock 전화·문자·카톡 실행 버튼 (Streamlit)
- [ ] 안정적인 화면 전환 (저지연) — 대기 화면 최소화

---

## 5. 리스크 및 대비

| 리스크 | 대비 |
|--------|------|
| LLM 스크립트가 근거 없는 보험 문구 생성 | Grounding and Safety Agent가 KNOWN_DOC 기반 문장에만 허용, 근거 없으면 REJECTED |
| Transcript evidenceText 와 화면 불일치 | expected JSON의 evidenceText 를 transcript 원문과 1:1 매칭해 데모에 그대로 사용 |
| 갱신 D-32·경과 개월 수 오차 | 모든 파생값을 DEMO_AS_OF_DATE(2026-09-09) 기준 규칙으로 계산, 하드코딩 금지 |
| 데모 시간 초과 | 4:30 타임박스 준수, Safety Reject는 백업 시나리오로만 사용 |
| 실제 API 부재 | 전화/문자/카톡/STT/CRM/캘린더는 Mock Tool 로 시연 가능 |