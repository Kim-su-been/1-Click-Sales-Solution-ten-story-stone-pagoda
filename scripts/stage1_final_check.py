# -*- coding: utf-8 -*-
# Stage1 완료조건 최종 검증
import sys, pathlib, re
sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path('/Users/siyoung/Desktop/one-pick-rescue-agent')

print("== 완료 조건 체크 ==")

# 1) 필수 파일 존재
files = ['app.py','requirements.txt','src/config.py','src/data_loader.py','src/demo_state.py',
         'ui/screens/daily_pick.py','ui/screens/consultation.py','ui/screens/closing.py',
         'tests/test_data_loader.py','tests/test_demo_state.py','docs/build-stage-1-report.md',
         'docs/implementation-plan.md']
missing = [f for f in files if not (ROOT/f).exists()]
print("1) 필수 파일 존재:", "OK" if not missing else f"FAIL {missing}")

# 2) product-brief Analyst 잔여 없음
brief = (ROOT/'product-brief.md').read_text(encoding='utf-8')
print("2) product-brief Analyst 이력 제거:", "OK" if 'Analyst' not in brief else "FAIL(잔존)")

# 3) Runtime Product Agent 코드 미생성 (agents/ 없음, agents/ import 없음)
has_agents_dir = (ROOT/'agents').exists()
app_src = (ROOT/'app.py').read_text(encoding='utf-8')
print("3) agents/ 미생성:", "OK" if not has_agents_dir else "FAIL")
print("   app.py 에 Runtime Agent import 없음:", "OK" if 'customer_selection' not in app_src and 'grounding' not in app_src and 'conversation' not in app_src else "FAIL")

# 4) requirements 에 LLM/외부/DB 의존성 없음
req = (ROOT/'requirements.txt').read_text(encoding='utf-8')
lower = req.lower()
banned = ['openai','anthropic','langchain','sqlite','sqlalchemy','requests','httpx','llama','faiss','chromadb']
hits = [b for b in banned if b in lower]
print("4) 의존성 최소(LLM/외부/SQLite 없음):", "OK" if not hits else f"FAIL {hits}  ({req.splitlines()})")

# 5) DEMO_AS_OF_DATE 고정 확인
cfg = (ROOT/'src/config.py').read_text(encoding='utf-8')
print("5) DEMO_AS_OF_DATE=2026-09-09 고정:", "OK" if 'DEMO_AS_OF_DATE = "2026-09-09"' in cfg else "FAIL")

# 6) DataLoader 가 UI에서 직접 경로 접근 안 함 (screens 에 pathlib/open 없음)
for f in ['ui/screens/daily_pick.py','ui/screens/consultation.py','ui/screens/closing.py']:
    s = (ROOT/f).read_text(encoding='utf-8')
    pathlib_used = 'pathlib' in s or 'open(' in s or 'read_text' in s
    print(f"   {f} 직접 파일접근 없음:", "OK" if not pathlib_used else "WARN")

# 7) Ineligible 1-Pick 배제 — expected 및 UI 모두
dp = __import__('json').load(open(ROOT/'data/expected/daily_pick_expected.json', encoding='utf-8'))
pick = dp['daily_pick']
print("7) daily_pick == CUST-001(김동양):", "OK" if pick['customer_id']=='CUST-001' else "FAIL")

# 8) 보험료가 점수에 미사용 (scoring_rules 검사)
rules = __import__('json').load(open(ROOT/'data/seed/scoring_rules.json', encoding='utf-8'))
# 보험료 '금액'(monthly_premium)이 rule 의 condition/points 에 사용되면 안 됨. premium_status(연체 상태)는 금액이 아님.
used_prem = any('monthly_premium' in r.get('condition','') for r in rules['score_rules'])
notes_ok = any('보험료' in n and '사용하지' in n for n in rules.get('notes',[]))
print("8) 보험료 미사용:", "OK" if not used_prem and notes_ok else "FAIL")

# 9) docs 확인
print("9) implementation-plan.md 존재:", "OK" if (ROOT/'docs/implementation-plan.md').exists() else "FAIL")
print("   build-stage-1-report.md 존재:", "OK" if (ROOT/'docs/build-stage-1-report.md').exists() else "FAIL")

print("\n=== Stage1 완료조건 점검 종료 ===")