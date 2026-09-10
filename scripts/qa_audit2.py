# -*- coding: utf-8 -*-
"""오탐 원인 확인 + 보완 검증 (읽기 전용)"""
import json, pathlib, re

print("== 보완 1: daily_pick_expected.json 의 evidenceType/구조 ==")
dp = json.load(open('data/expected/daily_pick_expected.json', encoding='utf-8'))
print("daily_pick evidence:", dp.get('evidence'))

print()
print("== 보완 2: 보험료 금액(monthly_premium)이 어느 규칙에도 사용되는가 ==")
rules = json.load(open('data/seed/scoring_rules.json', encoding='utf-8'))
flat = json.dumps(rules, ensure_ascii=False)
print("scoring_rules.json 에 'monthly_premium' 언급:", 'monthly_premium' in flat)
print("scoring_rules.json 에 'PREMIUM_OVERDUE' 존재:", 'PREMIUM_OVERDUE' in flat)
print("-- 규칙 목록 --")
for r in rules['score_rules']:
    print("  ", r['rule_id'], r['points'], r.get('condition', '')[:60])
print("-- notes --")
for n in rules.get('notes', []):
    print("  -", n)
# R5가 금액이 아닌 '연체 이력' 기반인지 확인
r5 = next(r for r in rules['score_rules'] if r['rule_id'] == 'R5')
print("R5 condition:", r5.get('condition'))

print()
print("== 보완 3: transcript evidenceRef(spk) 전수 유효성 (3개 expected) ==")
tlines = pathlib.Path('data/demo/consultation-transcript.txt').read_text(encoding='utf-8').splitlines()
speaks = [l for l in tlines if l.startswith('[')]
print("발화 수:", len(speaks))

def all_refs(fn):
    out = []
    data = json.load(open(fn, encoding='utf-8'))
    def walk(o):
        if isinstance(o, dict):
            if 'evidenceRef' in o and isinstance(o['evidenceRef'], str):
                out.append(o['evidenceRef'])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(data)
    return out

for fn in ['data/expected/session-analysis-expected.json',
           'data/expected/crm-record-expected.json',
           'data/expected/next-action-expected.json']:
    refs = all_refs(fn)
    bad = []
    for r in refs:
        m = re.search(r'data/demo/consultation-transcript.txt#spk:(\d+)', r)
        if not m:
            bad.append(('format', r))
        else:
            idx = int(m.group(1))
            if idx < 1 or idx > len(speaks):
                bad.append(('range', r))
    print("  {}: refs {}개 ->".format(fn, len(refs)), "OK" if not bad else "FAIL " + str(bad))

print()
print("== 보완 4: product-brief.md Analyst 잔여 + 4-Agent 구조 확인 ==")
brief = pathlib.Path('product-brief.md').read_text(encoding='utf-8')
print("'Analyst Agent — 모드' 잔여:", 'Analyst Agent — 모드' in brief)
for name in ['Orchestrator', 'Customer Selection Agent', 'Grounding and Safety Agent', 'Conversation Analysis Agent']:
    print("  '{}' 언급:".format(name), 'OK' if name in brief else 'MISSING')

print()
print("== 보완 5: Streamlit/Product Agent 코드 미생성 확인 ==")
import os
root = pathlib.Path('.')
py_files = [str(p) for p in root.rglob('*.py')]
print("py 파일:", py_files)
print("app.py 존재:", pathlib.Path('app.py').exists())
print("agents/ 존재:", pathlib.Path('agents').exists())

print()
print("== 보완 6: implementation-plan.md 단일 기준 가능 여부 ==")
plan = pathlib.Path('docs/implementation-plan.md').read_text(encoding='utf-8')
steps = re.findall(r'^## (.+)$', plan, re.M)
print("계획 단계 수(추정):", len(steps))
for m in re.finditer(r'^## (.+)$', plan, re.M):
    print("  ##", m.group(1))
print()
print("모든 보완 검증 완료")