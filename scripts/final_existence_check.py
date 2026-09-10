# -*- coding: utf-8 -*-
# 최종 완료 조건 확인
import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = pathlib.Path('/Users/siyoung/Desktop/one-pick-rescue-agent')

must = ['app.py','requirements.txt','src/config.py','src/data_loader.py','src/demo_state.py',
        'ui/common.py','ui/screens/daily_pick.py','ui/screens/consultation.py','ui/screens/closing.py',
        'tests/test_data_loader.py','tests/test_demo_state.py','docs/build-stage-1-report.md',
        'docs/implementation-plan.md']
print("필수 파일:", all((ROOT/f).exists() for f in must))

# agents/ (Runtime Product Agent 코드) 미생성 확인
agents_dir = ROOT / 'agents'
print("agents/ 생성 여부:", agents_dir.exists())

# app.py 에 Runtime Agent import 문구 없는지
app_src = (ROOT/'app.py').read_text(encoding='utf-8')
print("app.py 에 agents import:", 'import agents' in app_src or 'from agents' in app_src)

# requirements 최소 의존성
req = (ROOT/'requirements.txt').read_text(encoding='utf-8')
print("requirements:", req.strip().replace(chr(10), ' / '))
print("LLM/API/SQLite 의존성:", any(k in req for k in ['openai','anthropic','langchain','sqlalchemy','sqlite']))

# 루트에 implementation-plan.md 중복 없음
print("루트 implementation-plan.md 중복:", (ROOT/'implementation-plan.md').exists())