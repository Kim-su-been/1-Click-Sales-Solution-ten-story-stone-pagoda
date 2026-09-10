# 1-Pick Rescue Agent — 구현 계획 (Implementation Plan)

> 이 문서는 해커톤 MVP 구현 단계(다음 단계)의 실행 계획이다. **현재 단계(데이터·설계)에서는 앱 코드를 만들지 않는다.**
> 기술 스택(확정): Python + Streamlit + SQLite/JSON · 데모 5분 이내(실행 4:30) · 기준일 `DEMO_AS_OF_DATE=2026-09-09`

---

## 구현 전 준비 (이미 완료된 산출물)

- `data/seed/*.json` — 고객 5명·계약·스코어 규칙·Eligibility
- `data/expected/daily_pick_expected.json` — 1-Pick 기대 결과 (김동양 90점)
- `data/knowledge/*.md` — 가상 상품설명서·약관·FAQ·판매유의사항
- `data/expected/contact-script-expected.json` · `safety-reject-expected.json`
- `data/demo/consultation-transcript.txt` · `data/expected/session-analysis-expected.json` · `crm-record-expected.json` · `next-action-expected.json`
- `docs/demo-and-acceptance.md`, `docs/data-contracts.md`

---

## 구현 단계

### 1. Streamlit 프로젝트 초기화
- `app.py` + `requirements.txt` (streamlit) 생성
- 설정: 페이지 타이틀 "1-Pick Rescue Agent", `DEMO_AS_OF_DATE=2026-09-09` 상수
- `.streamlit/config.toml` (테마·세로폭)

### 2. Mock 데이터 로딩
- `data_loader.py`: `data/seed/*.json`, `data/knowledge/*.md`, `data/demo/*.txt` 로딩 + 검증
- 로딩 시 JSON 문법·ID 참조·앵커 존재 검증 함수 포함
- 날짜 계산 헬퍼 (기준일 고정, `days_until`, `months_elapsed`)

### 3. 화면 이동이 가능한 UI 뼈대
- 좌측 사이드바 또는 상단 탭으로 단계별 화면 분리: `오늘의 1-Pick` / `스크립트·Safety` / `Mock 전화·Transcript` / `상담 분석·CRM` / `Next Action`
- 각 화면 전환 시 상태 유지 (`st.session_state`)

### 4. Customer Selection Agent
- `agents/customer_selection.py`:
  - **Eligibility Check** → consent_channels/active_complaint 검사
  - **Rescue Score 계산** (scoring_rules.json 기반, 규칙 재계산, LLM 무관)
  - Ineligible: `rescue_score=null` + `potential_score` + `exclusion_reason`
  - **1-Pick**: Eligible 중 최고 점수 1명 + Contact Reason(갱신 사전안내) + 근거(CUSTOMER_DATA)
- expected: `daily_pick_expected.json` 과 대조

### 5. Grounding and Safety Agent
- `agents/grounding_safety.py`:
  - **Grounding**: Knowledge 문서 앵커 검색 → 스크립트 문장과 `evidenceRef` 1:1 연결
  - **Safety**: 금지표현(위협/과장/근거없는 단정) 사전 + 근거 미연결 문장 검출 → `COMPLIANT`/`REJECTED`
  - `contact-script-expected.json`, `safety-reject-expected.json` 과 대조

### 6. Mock Communication Tool
- `tools/channel.py`: Call/SMS/Kakao 상태 머신 (시도→연결→완료/실패), 시각·상태 Tracking
- `tools/stt_mock.py`: 준비된 transcript 로딩 (실제 녹음 없이)

### 7. Conversation Analysis Agent
- `agents/conversation_analysis.py`:
  - Transcript 입력 → 구조화 상담 결과 (outcome/니즈/관심/거절/후속희망)
  - **모든 분석 필드에 TRANSCRIPT evidence** 부착 (evidenceText = 원문 그대로)
- expected: `session-analysis-expected.json` 과 대조

### 8. CRM 및 Calendar Mock Tool
- `tools/crm.py`: 상담기록 Draft 생성 (`status=DRAFT`, `phase=FC_REVIEW`) → FC 확인 → SAVED
- `tools/calendar.py`: 후속 일정 후보 생성 → `PENDING_FC_CONFIRM` → 등록
- expected: `crm-record-expected.json`, `next-action-expected.json` 과 대조

### 9. End-to-End 연결
- `workflows/state_machine.py`: ①→⑨ 상태 전이 (IDLE→POOL_SCAN→SCORING→...→FEEDBACK)
- Orchestrator 가 Agent/Tool 호출 순서 제어, FC 버튼 이벤트 처리
- 한 사이클: 1-Pick → 스크립트 → 연락 → 분석 → CRM → Next Action → 피드백 저장

### 10. UI 개선
- Action Card 시각화 (점수 breakdown, 근거 표시, [전화][문자][카톡][나중에])
- 검증 결과(COMPLIANT/REJECTED) 배지, 근거 ref 툴팁
- 데모 타임라인 하이라이트 (4:30 기준)

### 11. 테스트 및 Demo 검증
- `pytest`: 데이터 로딩 검증 / 점수 재계산(90점) / Eligibility 제외 / evidence 일치 / CRM DRAFT
- `docs/demo-and-acceptance.md` 의 인수기준 A1~A10 전부 만족 확인
- 4:30 타임박스 체험 리허설 + Safety Reject 백업 시나리오 확인

---

## 완료 조건 (이 계획의 체크리스트)

- [ ] Streamlit 앱에서 ①→⑨ 한 사이클이 버튼 클릭으로 동작
- [ ] 김동양 90점, CUST-002·CUST-003 제외(potential_score 표시)
- [ ] 스크립트 문장마다 KNOWLEDGE_DOCUMENT 근거 / 금지표현 0건
- [ ] Transcript 기반 분석 결과와 expected 일치
- [ ] CRM Draft → FC 확인 → SAVED
- [ ] Next Action·캘린더(2026-09-17 오후) 후보 → 등록
- [ ] 피드백 저장 → 다음 추천 반영 대비
- [ ] 데모 4:30 (5분 이내)
- [ ] 실제 LLM/STT/전화 API 없이 Mock 으로 동작

---

## 다음 단계 (이후 고도화)

- 실제 STT 연동, 실시간 통화 중 Co-pilot, 실제 전화/문자/카톡 API
- 임베딩 기반 RAG 강화, Learn 루프 기반 추천 모델 개선 (실제 재학습)
- 멀티 FC·권한·감사 로그