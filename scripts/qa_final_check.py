# -*- coding: utf-8 -*-
# QA 산출물 최종 확인 스크립트
import pathlib, sys

sys.stdout.reconfigure(encoding='utf-8')

files = ['reviews/data-integrity-audit.md','reviews/grounding-evidence-audit.md','reviews/conversation-demo-audit.md','docs/qa-audit.md']
for f in files:
    p = pathlib.Path(f)
    print(f, "exists:", p.exists())
    if not p.exists():
        continue
    s = p.read_text(encoding='utf-8')
    print("  size:", len(s), "bytes  PASS/FAIL marks:", s.count('**PASS**') + s.count('**FAIL**'))

qa = pathlib.Path('docs/qa-audit.md').read_text(encoding='utf-8')
print("\nqa-audit.md checks:")
checks = {
    "final= PASS_WITH_WARNINGS": "PASS_WITH_WARNINGS" in qa,
    "audit-agents section": "감사 에이전트" in qa,
    "json9 section": "JSON" in qa and "9" in qa,
    "id/evidence section": "Evidence" in qa,
    "score/date section": "재계산" in qa,
    "modified files section": "수정한 파일" in qa,
    "warnings section": "주의사항" in qa,
}
for k, v in checks.items():
    print("  ", "OK" if v else "MISSING", k)

for f in files[:3]:
    s = pathlib.Path(f).read_text(encoding='utf-8')
    has_result = ('PASS' in s or 'FAIL' in s)
    has_evidence = any(x in s for x in ['data/seed/', 'data/expected/', 'data/knowledge/', 'data/demo/', 'docs/'])
    print(f, "-> result_mark:", has_result, "evidence_path:", has_evidence)