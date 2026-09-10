# 1-Pick Rescue Agent — 제품 분석 및 기술 설계 Brief

> 작성 목적: 해커톤 MVP 구현 전, 요구사항 분석·Agent 구조 재설계·기술 설계를 확정하기 위한 문서.
> 입력 문서: `동양생명_10층석탑.docx` (STEP ①~⑨ 워크플로우 컨셉)

---

## 0. 결론 요약

- **Product Agent 구성(확정):** Orchestrator / Customer Selection Agent / Grounding and Safety Agent / Conversation Analysis Agent 4개.
  - 전화·문자·카카오톡·STT·CRM·Calendar는 **Tool로 분류**한다 (지능 불필요, 상태 전이 + 이력 기록).
- **Rescue Score는 규칙 기반**으로 계산한다 (R1~R5, `scoring_rules.json`). 데모 기준일 `DEMO_AS_OF_DATE=2026-09-09` 기준, 김동양 고객 90점(담당 FC 변경 11개월 +20 · 최근 접촉 14개월 전 +30 · 특약 갱신 D-32 +25 · 최근 상담 이력 없음 +15).
- **Eligibility → Score → Pick 순서 고정:** ① 연락 가능성 체크 → ② Eligible 만 Rescue Score 계산 → ③ 최고 점수 1명 선정. Ineligible 은 daily_pick 후보 제외, rescue_score=null, 참고용 potential_score 만 표시.
- 핵심 차별화: ① 매일 **고객 1명**만 추천(목록이 아님), ② 모든 멘트가 **공식 상품자료에 근거**(Grounding), ③ **통화 자체가 CRM 데이터**가 되는 자동화, ④ 상담 종료 후 **FC가 직접 입력하지 않음**(CRM은 초안 → FC 확인 → 저장).
- 모든 외부 시스템(전화/카톡/CRM/캘린더/STT)은 Mock Tool로 대체하되, **데이터 모델과 단계별 I/O는 실제와 동일하게** 설계.
- **기술 스택(확정):** Python + Streamlit + SQLite/JSON. **Demo 시간(확정):** 5분 이내(실행 4:30 + 버퍼 0:30). **Learn:** 실제 모델 재학습 대신 **피드백 데이터만 저장**. **STT:** 실제 STT 없이 준비된 Transcript로 데모 가능.

---

## 1. MVP에서 반드시 구현해야 하는 기능

`동양생명_10층석탑.docx` STEP ①~⑨을 그대로 사다리로 삼는다.

| # | 기능 | 설명 | 화면/산출물 |
|---|------|------|------------|
| 1 | 샘플 고아계약 데이터 | 담당 FC가 변경되었거나 최근 상담이 없는 고객 5~7명 Mock DB | 고객/계약 데이터 시드 |
| 2 | Rescue Score 산출 | 고객관리 필요성 → 계약 유지 위험 → 시점 적절성 → 연락 가능성 순 가중치 합산 (규칙 기반) | 고객별 점수 + 산출 근거(breakdown) |
| 3 | 오늘의 1-Pick 선정 | 스코어 기반 순위 + 후보 간 LLM 판단으로 **1명** 확정 | Action Card |
| 4 | Contact Reason 생성 | 후보 3개 생성 → "지금 이 고객에게 가장 맞는 이유 1개" 선택 | 이유 + 선택 근거 (A/B/C 공개하지 않음) |
| 5 | 고객 맞춤 스크립트 생성 | 첫마디(전화) + 문자/카카오톡 초안 | 대사 초안 |
| 6 | Compliance 검증 | 금지/과장 표현 규칙 체크 + 상품자료(RAG) 근거 연결 | 검증 통과/경고 + 근거 출처 |
| 7 | Action Card UI | [📞 전화하기] [💬 문자] [💬 카카오톡] [⏰ 나중에] | 실행 버튼 |
| 8 | 연락 실행(Mock) + Tracking | 채널별 시도·연결·완료 상태 기록, 시도 시각 자동 기록 | 연락 이력 |
| 9 | 상담 Transcript 입력 + 분석 | 텍스트 입력(Mock STT) → 니즈·관심사·거절사유·후속 희망 추출 | 구조화 상담 결과 |
| 10 | CRM 상담기록 자동 생성 | 상담 분석을 FC 검토 → 확인 → 저장 | CRM 기록 |
| 11 | Next Action + 후속 일정 생성 | 후속 Task + 캘린더 일정 후보 → FC 확인 → 등록 | 후속 업무 목록 |
| 12 | 추천-결과 피드백 저장(Learn) | 추천·연락·상담결과를 연결 저장해 다음 추천에 반영 가능한 구조 | 학습용 이력 |

MVP 성공 기준: **"1명 추천 → 사유·대사 → 연락 실행(Tracking) → 상담 분석 → CRM/Next Action 자동 생성 → 피드백 저장"** 루프가 한 사이클 끝까지 실제로 동작한다.

---

## 2. 구현하지 않아도 되는 기능 (비-MVP / 제외 범위)

| 기능 | 제외 사유 | 대응 |
|------|----------|------|
| 실제 전화/문자/카카오톡 API 연동 | 해커톤 환경에 없음 | Mock Channel Gateway + 상태 머신 |
| 실제 STT 엔진 (실시간 음성 인식) | 데모 안정성 위해 | 사전 녹취본/transcript 텍스트 입력 (Mock STT) |
| 통화 중 실시간 Co-pilot (STEP ⑥의 실시간 질문 감지) | 대기시간·플로우 복잡도 | **상담 후 분석**에 집중. 실시간은 "앞으로" 섹션에 기록 |
| 실제 CRM / 캘린더 / 업무관리 SaaS 연동 | 외부 연동 불필요 | 내부 저장소(DB/JSON)로 대체, 인터페이스만 실제 규격과 유사 |
| 로그인·권한·감사 로그, 멀티 FC 조직 구조 | 데모 단계 과함 | 단일 FC 가정 |
| 실제 임베딩 기반 RAG 인프라 | 자료 규모가 작음 | 샘플 상품자료에 대한 키워드/벡터 검색 기반 Grounding(true RAG) |
| 복잡한 ML 모델/대시보드 (Learn 단계 고도화) | MVP 1차에서 과함 | 추천-결과 이력 저장까지만 구현 |
| 여러 고객 목록 UI (CRM 리스트형 화면) | 설계 원칙과 정면 배치 | **1명 Action Card만** 노출 |

---

## 3. 필요한 데이터 구조

핵심 원칙: **추천-연락-상담-후속이 모두 한 고객을 따라 연결**되어야 Learn 단계(피드백 루프)가 성립한다.

### 3.1 Mock 데이터 (시드)

```
customers        – 고객 기본 정보
  id, name, birth_year, sex, phone, consent_channels (['CALL','SMS','KAKAO']),
  is_orphan(고아계약 여부), orphan_assigned_at

contracts        – 보험계약
  id, customer_id, product_code, status(유지/해지), premium(월 보험료),
  premium_status(정상/연체), fc_id, previous_fc_id, fc_changed_at,
  start_date, renewal_date(갱신형 특약 갱신 예정일), maturity_date,
  last_contacted_at, lapse_risk_factors

products         – 상품/특약 마스터 (Grounding 참조 대상)
  product_code, name, product_type(종신/실손/갱신형 특약 등),
  renewal_cycle_months, key_benefits, exclusions, sales_guide_notes

knowledge_docs    – 공식 자료 (RAG 말뭉치)
  doc_id, product_code, doc_type(상품설명서/약관/판매가이드/FAQ/매뉴얼),
  content, source(파일명), updated_at
```

### 3.2 런타임 데이터 (워크플로우가 생성)

```
daily_picks       – 추천 이력 (Observe/Reason/1-Pick 결과)
  id, pick_date, customer_id, rescue_score, score_breakdown(JSON),
  contact_reason_code, contact_reason_text, reason_evidence(JSON),
  grounding_docs(JSON, 출처 목록), compliance_status, script_call, script_sms,
  created_at, status

contacts          – 연락 이력 (STEP ⑤~⑥ Tracking)
  id, pick_id, channel(CALL/SMS/KAKAO), attempt_at, status(시도/연결/미연결/발송/전송실패/응답없음),
  outcome_note

conversations     – 상담 원본 (STEP ⑥)
  id, pick_id, customer_id, channel, connected_at, ended_at, transcript(전문),
  recording_ref(Mock)

consultation_results – 상담 분석 결과 (STEP ⑦~⑧)
  id, conversation_id, outcome(성공/부분/거절/미연결), customer_needs(JSON),
  customer_interests(JSON), rejection_reason, followup_needed, preferred_datetime,
  ai_summary, crm_record(JSON, CRM 초안)

next_actions      – 후속 업무 (STEP ⑧)
  id, conversation_id, action_type(재상담/자료준비/보장점검/CROSS_SELL_DEFERRED 등),
  due_datetime, status, calendar_candidate(JSON/캘린더 등록 후보)

feedback_events   – Learn(STEP ⑨)용 이벤트
  id, pick_id, conversation_id, fc_action(연락/스킵), outcome, improvement_hint
```

ERD (축약): `customers 1─N contracts` · `customers 1─N daily_picks` · `daily_picks 1─N contacts` · `daily_picks 1─1 conversations` · `conversations 1─1 consultation_results` · `conversations 1─N next_actions` · `daily_picks ─N feedback_events`

---

## 4. 필요한 Agent (확정 구조)

> 초안(4-Agent)은 확정안이 아니었다. 각 역할을 검토한 뒤 **Product Agent 4개**로 확정한다. 전화·문자·카톡·STT·CRM·Calendar 는 Agent가 아닌 Tool 이다.

| 초안 역할 | 확정 | 판정 근거 |
|-----------|------|-----------|
| Orchestrator Agent | **유지 (Orchestrator)** | 워크플로우 순서 제어·단계 간 데이터 전달·FC 인터랙션. LLM 판단 없이 결정론적 상태 머신 |
| Customer & Reasoning Agent | **Customer Selection Agent** | Eligibility Check → Rescue Score 계산 → 1-Pick + Contact Reason 선정. 스코어링은 규칙(Tool), 이유 생성만 LLM |
| Compliance Agent | **Grounding and Safety Agent** | 상품자료 근거 연결(Grounding) + 금지표현·근거 없는 주장 검증(Safety). 하나의 책임으로 통합 |
| Communication Agent | **Tool 묶음으로 격하 (Channel/STT/CRM/Calendar)** | 실제 API 없음 + 지능 불필요. 상태 전이 + 이력 기록만으로 충분 |
| Closing Agent | **Conversation Analysis Agent** | 상담 Transcript 분석 → 구조화 결과 → CRM 초안 → Next Action 생성. 상담 분석 책임으로 전문화 |

### 4.1 최종 Product Agent 구성

```
┌─────────────────────────────────────────────────────┐
│ Orchestrator Agent (결정론적 상태 머신)               │
│ · Eligibility → Score → Pick → Script → Contact      │
│ · → Analysis → CRM Draft → Next Action → Feedback    │
│ · Tool 호출 라우팅 · FC 인터랙션(확인/수정/스킵)        │
└─────────────┬──────────────┬──────────────┬─────────┘
              │              │              │
   Customer Selection   Grounding and   Conversation
   Agent                Safety Agent    Analysis Agent
   · Eligibility        · 상품자료 근거    · Transcript 분석
   · Rescue Score       · 금지표현 검증   · 구조화 결과
   · 1-Pick/이유        · 근거 ref 매칭  · CRM Draft
                                          · Next Action
              │              │              │
        ┌─────┴──────────────┴──────────────┴─────┐
        │        Tool 계층 (전부 Tool)              │
        │  DB 조회 · RescueScore · KnowledgeRetriever│
        │  ComplianceChecker · ScriptGenerator      │
        │  ChannelGateway · SttService(Mock)        │
        │  CrmService · CalendarScheduler ·         │
        │  NextActionBuilder · FeedbackStore        │
        └──────────────────────────────────────────┘
```

---

## 5. 필요한 Tool/API (Mock 포함)

| Tool | 역할 | 구현 방식 |
|------|------|-----------|
| 1. Customer/Contract DB 조회 | 고아계약 Pool 탐색, 고객·계약 정보 | sqlite / JSON 시드 |
| 2. RescueScoreCalculator | 가중치 합산 + 근거 breakdown | 결정적 규칙 (구현 필수, LLM 무관) |
| 3. KnowledgeRetriever (RAG) | Contact Reason/스크립트 근거 검색 | 샘플 `knowledge_docs`에 대한 키워드+LLM 근거 선별 |
| 4. ComplianceChecker | 금지표현·근거 결여·미검증 수치 검사 | 규칙 기반 사전 + LLM 검증 병행 |
| 5. ScriptGenerator | 첫마디·SMS·카톡 초안 | LLM(템플릿+고객·계약 컨텍스트) |
| 6. ChannelGateway (Mock) | 전화/문자/카톡 시도·연결·완료, 시각·상태 기록 | Mock 상태 머신 |
| 7. SttService (Mock) | 녹취음성→Text | **transcript 직접 입력**(또는 미리 준비된 녹취 파일) |
| 8. CrmService | 상담기록 생성/저장 | 내부 DB에 CRM 레코드 저장 |
| 9. CalendarScheduler | 후속 일정 후보 생성/등록 | 내부 저장소, "등록할까요? [확인]" 흐름 |
| 10. NextActionBuilder | 후속 Task 생성 | LLM 분석 결과 기반 결정적 코드 |
| 11. FeedbackStore | 추천-결과 매핑 저장(Learn) | daily_picks↔consultation_results 연결 기록 |

---

## 6. 각 Agent의 Input / Output

### Orchestrator Agent
| Input | Output |
|-------|--------|
| 시작 명령(데모 버튼/CLI), FC 행동(버튼 이벤트), 각 단계 결과 | 다음 단계 호출, FC 확인 요청, 최종 상태(전 사이클 완료) |

### Customer Selection Agent (STEP ① ② ④)
| Input | Output |
|-------|--------|
| 고아계약 Pool(고객·계약 데이터), Eligibility 규칙, Rescue Score 규칙 | ① 고객별 eligibility(rescue_score 또는 potential_score + exclusion_reason) ② 1-Pick 고객 1명 + Contact Reason 1개 + 선택 근거 |

### Grounding and Safety Agent (STEP ③ ⑤)
| Input | Output |
|-------|--------|
| Contact Reason, 생성된 스크립트(첫마디·SMS·카톡), Knowledge 문서 | ① 각 문장에 KNOWLEDGE_DOCUMENT 근거(evidenceRef) 연결 ② Compliance 검증 결과(COMPLIANT / REJECTED + 위반 유형) ③ Safe 스크립트 확정 |

### Conversation Analysis Agent (STEP ⑦ ⑧)
| Input | Output |
|-------|--------|
| 상담 transcript(STT Mock), 고객·계약 컨텍스트 | ① 구조화 상담 결과(outcome/니즈/관심/거절사유/후속희망일시, 모두 TRANSCRIPT evidence) ② CRM 상담기록 초안(DRAFT) ③ Next Action 목록(재상담 일정 후보 포함) |

### Tools의 Input/Output은 5절에 요약. **모든 LLM 출력은 반드시 근거 출처(문서명·절)를 함께 반환**하도록 강제한다.

---

## 7. 전체 Workflow (STEP ①~⑨ 대응)

```
[매일 실행]
① Observe   고아계약 Pool 탐색 → 고객별 Rescue Score + breakdown
② Reason    Contact Reason 후보 3개 생성 → 최적 1개 선택 (근거 포함)
③ Grounding KnowledgeRetriever로 상품자료 검색 → 허용 설명만 사용
④ 1-Pick    Action Card 생성 (고객 1명 + 이유 + 첫마디)
⑤ Act       [문자/카톡] → 초안 생성 → Compliance 검증 → FC 확인 → 발송(Mock)
⑥ Contact   [전화] → 연결(Mock) → 시각·상태 자동 Tracking → 녹취/transcript 확보
⑦ Analyze   STT(또는 transcript) → 니즈/관심/거절/후속희망 자동 추출
⑧ Closing   CRM 기록 초안 → FC 확인 → 저장 → 후속 Task + 일정 후보 → 확인 → 등록
⑨ Learn     추천-연락-결과 feedback 저장 → 다음 1-Pick에 반영 가능
```

상세 상태 머신 (Orchestrator):

```
IDLE → POOL_SCAN → SCORING → REASONING → GROUNDING
     → PICK_READY ──[나중에]──→ IDLE
                └─[문자]→ SMS_DRAFT → COMPLIANCE_CHECK ──통과──→ FC_REVIEW → SENT(Mock) → TRACK
                └─[전화]→ CALL_MOCK → CONNECTED → RECORDING → TRANSCRIPT_READY
     → ANALYSIS → CRM_DRAFT → FC_CONFIRM ──[수정]──→ REGENERATE
                                  └─[확인]──→ CRM_SAVED → NEXT_ACTION_DRAFT
     → NEXT_ACTION_CONFIRM ──[확인]──→ SAVED → FEEDBACK_LOGGED → IDLE
```

---

## 8. 기술 아키텍처

기술 스택(확정): **Python + Streamlit + SQLite/JSON**.

```
[프론트]  Streamlit 데모 UI (Action Card, 확인/수정 버튼, transcript 입력 폼)
            │
[앱 계층]  app.py — Orchestrator 상태 머신 구동, FC 인터랙션 이벤트 수신
            │
[도메인]   agents/customer_selection.py — Eligibility → Score → Pick
           agents/grounding_safety.py   — 근거 연결 + 금지표현 검증
           agents/conversation_analysis.py — Transcript 분석 → CRM Draft → Next Action
           workflows/state_machine.py — 단계 전이 정의
           tools/*.py — DB, RescueScore, KnowledgeRetriever, Compliance,
                        Channel, STT(Mock), CRM, Calendar, Feedback
            │
[데이터]   data/seed/*.json — 고객·계약·상품·공식자료 시드
           data/knowledge/*.md — Grounding 근거 문서
           data/demo/consultation-transcript.txt — 준비된 Transcript
           data/expected/*.json — 데모 예상 결과(검증용)
           data/app.db (sqlite) — 런타임 이력
            │
[외부]     LLM API (JSON 응답 강제, 근거 출처 필드 필수) — 미사용 시 Mock LLM 사전 로딩 가능
```

- 언어/런타임: Python 3.11+
- LLM 인터페이스: 단일 `llm_client` 추상화 (모델 교체 용이, JSON 모드). **데모는 준비된 Transcript·스크립트·결과를 사용해 LLM 없이도 동작 가능**
- Grounding: **키워드 검색 + 근거 매칭** (최소 임베딩 없이) — evidenceRef 로 문서 문장과 1:1 연결
- 데이터 무결성: 모든 이력은 `pick_id`로 연결 → Learn 피드백 루프 성립 (실제 모델 재학습 대신 **피드백 데이터만 저장**)
- 날짜: `DEMO_AS_OF_DATE=2026-09-09` 고정, 모든 D-Day·경과 개월 수는 기준일로부터 계산 (결과 JSON에 하드코딩 금지)

---

## 9. 예상 구현 난이도 및 위험 요소

| 항목 | 난이도 | 위험/대응 |
|------|--------|-----------|
| Rescue Score (규칙 기반) | 낮음 | 가중치가 데모 서사를 정함 → 시드 데이터를 데모 스토리에 맞게 조정 |
| Grounding(RAG) 품질 | 중간 | ⚠ **동양생명_10층석탑.docx에는 실제 상품자료가 없음.** 가상 상품설명서/약관/판매가이드 샘플을 직접 제작해야 함. 근거 출처를 반드시 출력 |
| Compliance 검증 | 중간 | LLM이 근거 없는 수치/보장을 만들면 실패 → 결정적 금지표현 사전 + "근거 문서 없는 주장 금지" 프롬프트 + 검증 통과 시에만 발송 허용 |
| STT | 중간 | 실제 STT 엔진 미사용 → transcript 입력으로 대체. 데모에서 "녹취 → STT → 분석"을 명시적으로 시연 |
| LLM 지연/할루시네이션 | 중간 | 스코어링은 결정론, LLM은 스크립트·분석에만 사용. 타임아웃·재시도 처리 |
| FC 검토 UI (확인/수정) | 낮음 | 수정 시 재검증 루프(Compliance 재실행) 포함 |
| 전체 통합 | 중간 | 상태 머신이 단순할수록 좋음. **9단계를 한 사이클 시연하는 것**이 최대 리스크 → 데모 스크립트 사전 고정 |
| 날짜 의존 시나리오 (갱신 D-32 등) | 낮음 | 데모 기준일을 코드로 고정하고 시드를 그에 맞게 생성 |

---

## 10. 해커톤 Demo Scenario (End-to-End, 5분 이내 — 실행 4:30 + 버퍼 0:30)

> 상세 타임라인·인수기준은 `docs/demo-and-acceptance.md` 와 동일 (실행 4:30).

### 사전 준비
- 샘플 고아계약 고객 5명 시드 (`data/seed/*.json`) — **김동양(CUST-001)** 이 데모 주인공: 담당 FC 변경 11개월 + 특약 갱신 D-32 + 14개월 무접촉, Rescue Score 90
- 가상 Knowledge 문서 4종 (`data/knowledge/*.md`) — 종신보험·갱신형 특약·판매가이드·FAQ
- 준비된 상담 transcript 1건 (`data/demo/consultation-transcript.txt`)
- expected 결과 5종 (`data/expected/*.json`)
- 데모 기준일 `DEMO_AS_OF_DATE=2026-09-09` 고정

### 흐름 (4:30)
1. **0:00~0:35 오늘의 1-Pick** — "오늘의 1-Pick 시작" → Eligibility Check → Rescue Score 계산 → **김동양 1명** Action Card
2. **0:35~1:15 Rescue Score·이유·고객 데이터 근거** — breakdown(+20/+30/+25/+15=90) + CUSTOMER_DATA 근거 + Ineligible 참고 점수(95·88) 노출
3. **1:15~1:50 스크립트와 Grounding·Safety** — 전화/문자/카톡 초안 + KNOWLEDGE_DOCUMENT 근거 연결 + 금지표현 0건 검증(COMPLIANT)
4. **1:50~2:50 Mock 전화와 준비된 Transcript 처리** — 통화 연결·Tracking·녹취(STT Mock) → transcript 확보
5. **2:50~3:50 상담 분석과 CRM Draft** — TRANSCRIPT evidence 기반 분석 → CRM Draft(DRAFT/FC_REVIEW) 표시
6. **3:50~4:20 Next Action과 후속 일정 확인** — 재상담(2026-09-17 14:00)·자료 준비·갱신 안내 → 캘린더 후보 → [확인 및 등록]
7. **4:20~4:30 Agent Loop 정리** — 추천-연락-상담-후속 피드백 저장 → 다음 추천 반영 안내

### 데모에서 강조할 메시지
- "목록이 아니라 **이유를 가진 한 명**"
- "AI가 만든 멘트가 아니라 **공식 자료에 근거한 멘트**"
- "전화를 거는 순간부터 **CRM 기록이 완성**된다 (FC는 초안만 검토)"

---

## 11. 미결정 사항 / 가정

| 항목 | 현재 가정 | 결정 시점 |
|------|-----------|-----------|
| UI 스택 | Streamlit 단일 앱 (가장 빠름) | 구현 착수 전 1차 확정 |
| LLM 모델/API | 해커톤 제공 모델 또는 OpenAI/Anthropic 호환 API | 환경 확정 후 |
| 가상 상품자료 제작 | 동양생명 실제 상품자료 미확보 → 가상 데이터로 Grounding 시연 | 샘플 제작 전 사용자 확인 (실제 자료 제공 시 교체) |
| 실시간 Co-pilot | MVP 제외, post-call 분석 중심 | 데모 후 고도화 로드맵 반영 |
| 연락 채널 우선순위 | 전화(첫 접촉) → 문자 → 카톡 | 시연 순서와 동일하게 |