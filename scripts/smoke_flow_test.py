# -*- coding: utf-8 -*-
# Streamlit AppTest 기반 화면 흐름 검증
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from streamlit.testing.v1 import AppTest

# 1) DAILY_PICK 초기 화면
at = AppTest.from_file("app.py", default_timeout=30)
at.run()
print("초기 화면 title:", [m.value for m in at.markdown if "1-Pick" in getattr(m, 'value', '')][:1])
print("에러:", len(at.exception))

# '전화하기' 버튼 찾아 클릭 (라벨에 아이콘 포함 가능)
buttons = [b.label for b in at.button]
print("버튼 목록:", buttons)

def find_btn(label_sub):
    for i, l in enumerate(buttons):
        if label_sub in l:
            return i
    return -1

i = find_btn("전화하기")
if i != -1:
    at.button[i].click().run()
    print("CONSULTATION 전환 후 에러:", len(at.exception))
    print("표시 문구:", [m.value for m in at.markdown if "Mock" in getattr(m, 'value', '') or "Transcript" in getattr(m, 'value', '')][:3])

    # Transcript 불러오기
    b2 = [b.label for b in at.button]
    i2 = find_btn("Transcript 불러오기")
    if i2 != -1:
        at.button[i2].click().run()
        print("Transcript 로딩 후 에러:", len(at.exception))
        print("transcript 렌더:", any("김동양 고객님" in (getattr(m, 'value', '') or '') for m in at.markdown) or any("김동양" in (getattr(c, 'value', '') or '') for c in at.code))

    # 상담 완료 및 분석하기
    b3 = [b.label for b in at.button]
    i3 = find_btn("상담 완료 및 분석하기")
    if i3 != -1:
        at.button[i3].click().run()
        print("CLOSING 전환 후 에러:", len(at.exception))
        print("CRM 문구:", any("DRAFT" in (getattr(m, 'value', '') or '') for m in at.markdown) or any("FC 확인" in (getattr(b, 'label', '') or '') for b in at.button))

        b4 = [b.label for b in at.button]
        i4 = find_btn("처음으로 돌아가기")
        if i4 != -1:
            at.button[i4].click().run()
            print("DAILY_PICK 복귀 후 에러:", len(at.exception))

print("\n=== 화면 흐름 검증 완료 ===")