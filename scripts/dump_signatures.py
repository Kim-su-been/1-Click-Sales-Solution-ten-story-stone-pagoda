# -*- coding: utf-8
import sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
def dump(fname):
    p = pathlib.Path('/Users/siyoung/Desktop/one-pick-rescue-agent')/fname
    s = p.read_text(encoding='utf-8')
    print(f"===== {fname} ({len(s)} bytes, {len(s.splitlines())} lines) =====")
    # 클래스/def/시그니처만
    for i, l in enumerate(s.splitlines(), 1):
        st = l.strip()
        if st.startswith(('def ', 'class ', '    def ')):
            print(f"  {i}: {l}")
for f in ['src/data_loader.py','src/demo_state.py','tests/test_data_loader.py','ui/screens/daily_pick.py','ui/screens/consultation.py','ui/screens/closing.py']:
    dump(f)
    print()