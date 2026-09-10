# 1-Pick Rescue Agent — Build Stage 1 보고서 (Walking Skeleton)

> 단계: Streamlit 프로젝트 초기화 · Mock 데이터 로딩 · 화면 이동 UI 뼈대
> 기준일: `DEMO_AS_OF_DATE = 2026-09-09` · 기술 스택: Python + Streamlit (SQLite/LLM 미사용)

---

## 1. 생성·수정한 파일

### 신규 (앱·UI)
| 파일 | 역할 |
|------|------|
| `app.py` | Streamlit 엔트리포인트. 사이드바 진행 단계 표시 + 3화면 라우팅 |
| `requirements.txt` | `streamlit>=1.32.0`, `pytest>=8.0.0` (외부 API·LLM 의존성 없음) |
| `src/config.py` | 경로 상수·`DEMO_AS_OF_DATE=2026-09-09`·가상 데이터 고지문 |
| `src/data_loader.py` | 시드/Expected/Knowledge/Transcript 로딩 + ID 참조·spk 매핑·NFC 정규화·오류 메시지 |
| `src/demo_state.py` | `DAILY_PICK/CONSULTATION/CLOSING` 화면 상태 (session_state 전용) |
| `ui/common.py` | 카드·배지·Evidence 접기 스타일 헬퍼 |
| `ui/screens/daily_pick.py` | 화면 1 (1-Pick · 스코어 · 스크립트 · 근거) |
| `ui/screens/consultation.py` | 화면 2 (Mock 전화 · Transcript · STT Mock) |
| `ui/screens/closing.py` | 화면 3 (분석 결과 · CRM DRAFT · Next Action) |
| `tests/test_data_loader.py` | Data Loader 테스트 16건 |
| `tests/test_demo_state.py` | 화면 상태 테스트 5건 |
| `docs/build-stage-1-report.md` | 본 보고서 |

### 수정
| 파일 | 내용 |
|------|------|
| `product-brief.md` | Analyst 2-mode 이력 문구 1줄 제거 (4-Agent 구조만 남김) |
| `scripts/qa_audit2.py` | 잘못된 regex(80행) 수정 — 오류로 중단되던 부분 복구 |
| `scripts/smoke_flow_test*.py` | 화면 흐름(AppTest) 검증 스크립트 추가 |

## 2. 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
# 브라우저 http://localhost:8501 (또는 Streamlit 표시 URL)
```

데모 기준일은 `src/config.py` 의 `DEMO_AS_OF_DATE = "2026-09-09"` 로 고정 — 시스템 날짜를 사용하지 않는다.

## 3. 테스트 결과

### pytest (21건 전부 통과)
```
tests/test_data_loader.py .............. (16 passed)
tests/test_demo_state.py ..... (5 passed)
21 passed in ~20s
```

### 화면 흐름 검증 (scripts/smoke_flow_test_v2.py, Streamlit AppTest)
```
[1] DAILY_PICK 초기 렌더          error 0
[2] CONSULTATION 전환             error 0, 'Mock 상담 진행 중' 표시
[3] Transcript 불러오기           error 0, transcript 내용 표시
[4] CLOSING 전환                  error 0, 요약/DRAFT 표시
[5] FC 확인 (Mock)                error 0
[6] DAILY_PICK 복귀               error 0, 전화하기 버튼 복귀
```

### Streamlit headless 실행
```
streamlit run app.py --server.headless true → Local URL 정상 기동, HTTP 200
```
(백그라운드로 기동 후 응답 확인, 종료 완료)

### 기존 QA 스크립트
- `scripts/qa_audit.py` : 스크립트 로직 오탐(transcript ref를 KNOWLEDGE 경로로 잘못 검사)은 산출물 무관. 요구 검증(JSON·앵커·유니코드·CRM/데모)은 PASS.
- `scripts/qa_audit2.py` : regex 오류 수정 후 정상 실행 — 규칙·spk·4-Agent 구조 확인 PASS.

## 4. 세 화면 동작

| 화면 | 표시 내용 | 동작 |
|------|-----------|------|
| DAILY_PICK | 김동양 90점 · D-32 · 14개월 · 11개월 · 점수 breakdown · 선정 근거 · CUSTOMER_DATA evidence · Contact Reason · 전화 스크립트 · Knowledge 근거 접기 · 가상 데이터 고지 | [📞 전화하기]→화면2 / [💬 문자·카카오톡 초안 보기]→초안+근거 표시 |
| CONSULTATION | 김동양 정보 · "Mock 상담 진행 중" · 통화/STT 배지(Mock) · Transcript 불러오기 · STT Mock 처리 상태 | [Transcript 불러오기]→수록 내용 표시 / [상담 완료 및 분석하기]→화면3 |
| CLOSING | 상담 요약 · 니즈/관심/걱정/거절(각각 TRANSCRIPT evidence) · CRM DRAFT(FC_REVIEW) · 후속 일정 2026-09-17 오후 · Next Action 3건 · 캘린더 후보 | [FC 확인]→session_state만 확인, 저장 미연결 안내 / [처음으로 돌아가기]→화면1 |

## 5. Mock 처리된 기능 (명시적)
- 전화 발신·연결 → Mock (vect 상태만 변경)
- 문자/카카오톡 발송 → Mock (Expected 초안 표시만, 발송 안 함)
- STT(음성 인식) → Mock (준비된 Transcript 로딩으로 대체)
- CRM 저장 → Mock (DRAFT 유지, FC 확인 시 session_state만)
- 캘린더 등록 → Mock (후보 표시만)
- LLM·외부 API·SQLite → **미사용** (실제 의존성 없음)

## 6. 제약 / 이후 Runtime Product Agent 구현 단계
- 모든 화면 데이터는 `src/data_loader.py`를 통해서만 로딩 (파일 직접 접근 없음)
- 추후 Runtime Agent 구현 시 `daily_pick_expected.json`→`Customer Selection Agent` 출력, `contact-script-expected`→`Grounding and Safety Agent` 출력, `session-analysis/crm/next-action-expected`→`Conversation Analysis Agent` 출력으로 **각각 교체**하면 UI는 그대로 사용 가능
- 남은 단계 (implementation-plan.md): agents/customer_selection.py, agents/grounding_safety.py, agents/conversation_analysis.py, tools/(channel·stt_mock·crm·calendar), End-to-End 연결, UI 개선, 테스트·데모 검증