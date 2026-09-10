# -*- coding: utf-8 -*-
# 데이터/구현 파일 상태 점검 헬퍼
import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    'src/config.py', 'src/data_loader.py', 'src/demo_state.py',
    'ui/common.py', 'ui/screens/daily_pick.py', 'ui/screens/consultation.py',
    'ui/screens/closing.py', 'app.py', 'tests/test_data_loader.py',
    'tests/test_demo_state.py', 'requirements.txt'
]
for f in files:
    p = pathlib.Path(f)
    print(f, 'exists' if p.exists() else 'MISSING', end='  ')
    if p.exists():
        s = p.read_text(encoding='utf-8')
        print('size', len(s), 'lines', len(s.splitlines()), 'head:', repr(s[:60]))
    else:
        print()