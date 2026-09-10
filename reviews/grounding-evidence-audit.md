# QA 감사 보고서 — Grounding and Evidence Auditor

> 감사자: 감사 2: Grounding and Evidence Auditor (Build-time)
> 기준일: `DEMO_AS_OF_DATE = 2026-09-09`
> 실행 상태: 감사 에이전트 실행은 **런타임 정책(`Detached child requires an active runtime owner`)으로 실행 실패** → 주 감사 에이전트가 동일 절차로 대체 검토
> 대상: `data/knowledge/*.md` 4종 + `data/expected/*.json` 5종 + `docs/data-contracts.md`

---

## 1. Knowledge 문서 고지문 (첫 줄)

| 문서 | 첫 줄 정확 일치 | 근거 |
|---|---|---|
| `data/knowledge/product-guide.md` | **PASS** | `... 가상 자료이며 실제 보험상품의 약관 또는 상품설명서가 아닙니다.` |
| `data/knowledge/terms.md` | **PASS** | 동일 |
| `data/knowledge/renewal-faq.md` | **PASS** | 동일 |
| `data/knowledge/sales-cautions.md` | **PASS** | 동일 |

## 2. document_id / section_id (앵커) 중복 검사

| 문서 | 앵커 수 | 중복 | 근거 |
|---|---|---|---|
| product-guide.md | 12 | **PASS** | `{#...}` 정규식 수집, 중복 없음 |
| terms.md | 6 | **PASS** | 중복 없음 |
| renewal-faq.md | 5 | **PASS** | 중복 없음 |
| sales-cautions.md | 4 | **PASS** | 중복 없음 |

## 3. contact-script-expected.json evidenceRef → Knowledge 문서 연결

| 경계 | 결과 | 근거 |
|---|---|---|
| 모든 evidenceRef가 `data/knowledge/<file>#<anchor>` 형식 | **PASS** | `data/expected/contact-script-expected.json` 의 CALL/SMS/KAKAO 문장별 evidenceRef |
| 각 anchor 가 실제 md 에 존재 | **PASS** | `re.search(r'\{#anchor\}', md_text)` 로 전건 확인 (예: `#ts2001-renewal`, `#T5-renewal-notice`, `#Q2`) |
| 문장별로 KNOWLEDGE_DOCUMENT evidenceText 보유 | **PASS** | 전 문장 evidenceType=KNOWLEDGE_DOCUMENT |

## 4. safety-reject-expected.json REJECTED 처리

| 항목 | 결과 | 근거 |
|---|---|---|
| `review_result.decision == "REJECTED"` | **PASS** | `data/expected/safety-reject-expected.json` |
| 위반 3건 각각 KNOWLEDGE_DOCUMENT 근거 | **PASS** | THREAT_PRESSURE→`sales-cautions.md#safety-forbidden`, UNGROUNDED_CLAIM→`terms.md#T2-renewal-premium`, EXAGGERATION→`sales-cautions.md#safety-forbidden` |
| 교정 대안 문장 + 근거 ref | **PASS** | `allowable_alternative.grounding_refs` 3건 |

## 5. EXECUTION_LOG 미사용 (expected 데이터)

| 범위 | 결과 | 근거 |
|---|---|---|
| expected JSON 5종에 `EXECUTION_LOG` 문자열 존재 여부 | **PASS** | 5개 파일 전부 미포함. `docs/data-contracts.md` 에만 '런타임 구현 단계에서 사용' 정의 존재 (규약 정합) |

## 6. evidenceType 허용 집합

| 검사 | 결과 | 근거 |
|---|---|---|
| evidenceType ∈ {CUSTOMER_DATA, KNOWLEDGE_DOCUMENT, TRANSCRIPT} | **PASS** | expected 6종 전체 수집 결과 `{KNOWLEDGE_DOCUMENT, TRANSCRIPT, CUSTOMER_DATA}` 만 존재 |
| `daily_pick_expected.json` evidence.type = CUSTOMER_DATA | **PASS** | `data/expected/daily_pick_expected.json` |

## 7. 비정상 유니코드 (키릴 혼합) 검사

| 검사 | 결과 | 근거 |
|---|---|---|
| evidenceRef에 키릴 문자(`с`,`п` 등) 잔존 | **PASS** | JSON 9종·md 4종 전체 스캔에서 키릴 범위 `[\u0400-\u04FF]` 매칭 0건 (이전 단계에서 `#спk:` → `#spk:` 교체 완료) |

## 8. NFC 정규화

| 검사 | 결과 | 근거 |
|---|---|---|
| 모든 JSON·Markdown 이 `unicodedata.normalize('NFC', s) == s` | **PASS** | 대상 전부 NFC 정규화 상태 파싱 성공. 확인 스크립트: `scripts/qa_audit.py` |

## 9. 발견 문제

- 없음 (모든 항목 PASS)

## 10. 총평

**PASS** — Grounding(근거 연결)과 Safety(재현·차단) 검증 체계가 문서·데이터·예상 결과 모두에서 정합.