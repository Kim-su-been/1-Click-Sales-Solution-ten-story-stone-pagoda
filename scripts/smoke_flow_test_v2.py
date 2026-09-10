# -*- coding: utf-8 -*-
# Streamlit AppTest 기반 화면 흐름 검증 (v2 — 새 파일)
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from streamlit.testing.v1 import AppTest


def find_button(at, label_substr):
    labels = [b.label for b in at.button]
    for i, l in enumerate(labels):
        if label_substr in l:
            return i
    return -1


def dump_buttons(at):
    return [b.label for b in at.button]


at = AppTest.from_file("app.py", default_timeout=45)
at.run()
print("[1] DAILY_PICK 초기 렌더")
print("  title:", [m.value for m in at.markdown if "1-Pick" in getattr(m, "value", "")][:1])
print("  error:", len(at.exception))
assert len(at.exception) == 0
print("  buttons:", dump_buttons(at))

i = find_button(at, "전화하기")
assert i != -1
at.button[i].click().run()
print("[2] CONSULTATION error:", len(at.exception))
assert len(at.exception) == 0
md = " ".join(getattr(m, "value", "") for m in at.markdown)
print("  'Mock 상담 진행 중':", "Mock 상담 진행 중" in md)
print("  buttons:", dump_buttons(at))

i = find_button(at, "Transcript 불러오기")
assert i != -1
at.button[i].click().run()
print("[3] Transcript error:", len(at.exception))
assert len(at.exception) == 0
code_all = " ".join(getattr(c, "value", "") for c in at.code)
print("  transcript 표시:", "김동양 고객님" in code_all)

i = find_button(at, "상담 완료 및 분석하기")
assert i != -1
at.button[i].click().run()
print("[4] CLOSING error:", len(at.exception))
assert len(at.exception) == 0
md = " ".join(getattr(m, "value", "") for m in at.markdown)
print("  요약 표시:", "요약" in md)
print("  DRAFT:", "DRAFT" in md)
print("  buttons:", dump_buttons(at))

i = find_button(at, "FC 확인")
if i != -1:
    at.button[i].click().run()
    print("[5] FC확인 error:", len(at.exception))
    assert len(at.exception) == 0

i = find_button(at, "처음으로 돌아가기")
assert i != -1
at.button[i].click().run()
print("[6] DAILY_PICK 복귀 error:", len(at.exception))
assert len(at.exception) == 0
print("  전화하기 버튼 복귀:", any("전화하기" in l for l in dump_buttons(at)))

print("\n=== 화면 흐름 검증 통과 ===")