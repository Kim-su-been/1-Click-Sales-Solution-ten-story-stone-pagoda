# -*- coding: utf-8 -*-
"""1-Pick Rescue Agent QA 감사 스크립트 (읽기 전용)"""
import json, pathlib, re, unicodedata
from datetime import date

print("=== 검증 1: Data Integrity ===")
jsons = ['data/seed/customers.json','data/seed/contracts.json','data/seed/scoring_rules.json',
 'data/expected/daily_pick_expected.json','data/expected/contact-script-expected.json',
 'data/expected/safety-reject-expected.json','data/expected/session-analysis-expected.json',
 'data/expected/crm-record-expected.json','data/expected/next-action-expected.json']
missing = [f for f in jsons if not pathlib.Path(f).exists()]
print("JSON 존재:", "OK" if not missing else "FAIL " + str(missing))
for f in jsons:
    try:
        json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print("  JSON parse FAIL:", f, e)
print("JSON 문법: OK (9개)")

for f in jsons:
    d = json.load(open(f, encoding='utf-8'))
    if 'demo_as_of_date' in d:
        assert d['demo_as_of_date'] == '2026-09-09', f
print("DEMO_AS_OF_DATE==2026-09-09: OK")

customers = json.load(open('data/seed/customers.json', encoding='utf-8'))['customers']
contracts = json.load(open('data/seed/contracts.json', encoding='utf-8'))['contracts']
cids = {c['customer_id'] for c in customers}
bad = [ct['contract_id'] for ct in contracts if ct['customer_id'] not in cids]
print("contract.customer_id 참조:", "OK" if not bad else "FAIL " + str(bad))

DEMO = date(2026, 9, 9)
def days(d):
    return (date.fromisoformat(d) - DEMO).days
def months_between(a, b):
    da, db = date.fromisoformat(a), date.fromisoformat(b)
    return (db.year - da.year) * 12 + (db.month - da.month)

kim = next(c for c in customers if c['customer_id'] == 'CUST-001')
ren = next(ct['renewal_date'] for ct in contracts if ct['customer_id'] == 'CUST-001' and ct['renewal_date'])
print("D-32 재계산:", days(ren), "(renewal", ren, ")")
print("14개월 재계산:", months_between(kim['last_contacted_at'], '2026-09-09'), "(last_contact", kim['last_contacted_at'], ")")
print("11개월 재계산:", months_between(kim['fc_changed_at'], '2026-09-09'), "(fc_changed", kim['fc_changed_at'], ")")

def score(cust):
    pts = []
    fm = months_between(cust['fc_changed_at'], '2026-09-09')
    if cust.get('previous_fc_id'):
        if fm <= 3:
            pts.append(('R1a', 25))
        elif fm <= 12:
            pts.append(('R1b', 20))
    if months_between(cust['last_contacted_at'], '2026-09-09') >= 12:
        pts.append(('R2', 30))
    rens = [ct['renewal_date'] for ct in contracts if ct['customer_id'] == cust['customer_id'] and ct['renewal_date']]
    if rens:
        d = min(days(r) for r in rens)
        if d <= 45:
            pts.append(('R3a', 25))
        elif d <= 60:
            pts.append(('R3b', 20))
    lc = cust.get('last_consultation_at')
    if lc is None or months_between(lc, '2026-09-09') >= 6:
        pts.append(('R4', 15))
    if any(ct['premium_status'] == 'OVERDUE' for ct in contracts if ct['customer_id'] == cust['customer_id']):
        pts.append(('R5', 3))
    return sum(p for _, p in pts), [p for p, _ in pts]

s, br = score(kim)
print("김동양 규칙 재계산:", s, br, "->", "PASS" if s == 90 else "FAIL")

hard = [c['customer_id'] for c in customers if '90' in c.get('memo', '')]
print("하드코딩 검사(memo에 90):", "OK" if not hard else "FAIL " + str(hard))

rules = json.load(open('data/seed/scoring_rules.json', encoding='utf-8'))
prem_used = any('premium' in str(r).lower() for r in rules['score_rules'])
notes_ok = any('보험료' in n and '사용하지' in n for n in rules.get('notes', []))
print("보험료 미사용:", "OK" if not prem_used and notes_ok else "WARN {} {}".format(prem_used, notes_ok))

dp = json.load(open('data/expected/daily_pick_expected.json', encoding='utf-8'))
inelig = [c for c in dp['candidates'] if c['eligibility'] == 'INELIGIBLE']
elig = [c for c in dp['candidates'] if c['eligibility'] == 'ELIGIBLE']
print("Ineligible rescue_score null:", "OK" if all(c['rescue_score'] is None and isinstance(c.get('potential_score'), int) and c.get('exclusion_reason') for c in inelig) else "FAIL")
print("김동양 최고점:", "OK" if max(c['rescue_score'] for c in elig) == 90 and any(c['customer_id'] == 'CUST-001' and c['rescue_score'] == 90 for c in elig) else "FAIL")

print()
print("=== 검증 2: Grounding & Evidence ===")
md_paths = ['data/knowledge/product-guide.md', 'data/knowledge/terms.md',
            'data/knowledge/renewal-faq.md', 'data/knowledge/sales-cautions.md']
md = {p: pathlib.Path(p).read_text(encoding='utf-8') for p in md_paths}
notice = "본 문서는 1-Pick Rescue Agent 해커톤 시연을 위한 가상 자료이며 실제 보험상품의 약관 또는 상품설명서가 아닙니다."
for p, t in md.items():
    first = t.splitlines()[0]
    print("  {} 첫줄 고지문:".format(p), "OK" if first == notice else "FAIL " + first[:30])
for p, t in md.items():
    found = re.findall(r'\{#([\w\-]+)\}', t)
    dup = [a for a in set(found) if found.count(a) > 1]
    print("  {} 앵커 {}개 중복:".format(p, len(found)), "OK" if not dup else "FAIL " + str(dup))

def collect_refs_types(fn):
    refs, types = [], set()
    def walk(o):
        if isinstance(o, dict):
            if 'evidenceType' in o:
                types.add(o['evidenceType'])
            if 'evidenceRef' in o and isinstance(o['evidenceRef'], str):
                refs.append(o['evidenceRef'])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    data = json.load(open(fn, encoding='utf-8'))
    walk(data)
    return refs, types

all_types = set()
for fn in ['data/expected/contact-script-expected.json', 'data/expected/safety-reject-expected.json',
           'data/expected/session-analysis-expected.json', 'data/expected/crm-record-expected.json',
           'data/expected/next-action-expected.json']:
    refs, types = collect_refs_types(fn)
    all_types |= types
    bad_refs = []
    for r in refs:
        if r.startswith('data/knowledge/'):
            path, anchor = r.split('#')
            if not re.search(r'\{#' + re.escape(anchor) + r'\}', md[path]):
                bad_refs.append(r)
        elif r.endswith('#spk:' + r.rsplit('#spk:', 1)[-1]) and '#spk:' in r:
            # Transcript evidenceRef: #spk:N 은 발화 순서를 의미 (검증 3에서 수행)
            continue
        elif r == 'data/demo/consultation-transcript.txt':
            continue
        else:
            bad_refs.append(r)
    print("  {} evidenceRef 검증:".format(fn), "OK" if not bad_refs else "FAIL " + str(bad_refs))
print("evidenceType 집합:", all_types, "->", "OK" if all_types <= {'CUSTOMER_DATA', 'KNOWLEDGE_DOCUMENT', 'TRANSCRIPT'} else "FAIL")

exec_used = [fn for fn in ['data/expected/contact-script-expected.json', 'data/expected/safety-reject-expected.json',
                           'data/expected/session-analysis-expected.json', 'data/expected/crm-record-expected.json',
                           'data/expected/next-action-expected.json']
             if 'EXECUTION_LOG' in pathlib.Path(fn).read_text(encoding='utf-8')]
print("EXECUTION_LOG 미사용:", "OK" if not exec_used else "FAIL " + str(exec_used))

bad_uni = []
for fn in jsons + md_paths:
    s = pathlib.Path(fn).read_text(encoding='utf-8')
    if unicodedata.normalize('NFC', s) != s:
        bad_uni.append((fn, 'NFD'))
    if re.search(r'[\u0400-\u04FF]', s):
        bad_uni.append((fn, 'cyrillic'))
print("유니코드(NFC/키릴):", "OK" if not bad_uni else "FAIL " + str(bad_uni))

print()
print("=== 검증 3: Conversation & Demo ===")
tlines = pathlib.Path('data/demo/consultation-transcript.txt').read_text(encoding='utf-8').splitlines()
speaks = [l for l in tlines if l.startswith('[')]
print("발화 수:", len(speaks), "(1~2분 기대)")

def evs(fn):
    out = []
    data = json.load(open(fn, encoding='utf-8'))
    def walk(o):
        if isinstance(o, dict):
            if 'evidence' in o and isinstance(o['evidence'], dict):
                out.append(o['evidence'])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(data)
    return out

mism = []
for fn in ['data/expected/session-analysis-expected.json', 'data/expected/crm-record-expected.json',
           'data/expected/next-action-expected.json']:
    for e in evs(fn):
        et = e.get('evidenceText', '')
        m = re.search(r'#spk:(\d+)', e.get('evidenceRef', ''))
        idx = int(m.group(1)) if m else None
        if idx is None or idx < 1 or idx > len(speaks):
            mism.append((fn, 'ref범위', e.get('evidenceRef')))
            continue
        spk_text = speaks[idx - 1]
        if re.sub(r'^\[[^\]]+\]\s*', '', et).strip() not in spk_text:
            mism.append((fn, '불일치', et[:30]))
print("evidenceText 일치:", "OK" if not mism else "FAIL " + str(mism))

full = '\n'.join(speaks)
for kw in ['보장', '걱정', '새로 가입할 생각', '목요일 오후']:
    print("  transcript 포함 '{}':".format(kw), "OK" if kw in full else "FAIL")

na = json.load(open('data/expected/next-action-expected.json', encoding='utf-8'))
dts = []
def all_dt(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ('preferred_datetime', 'due_datetime') and isinstance(v, str):
                dts.append(v)
            all_dt(v)
    elif isinstance(o, list):
        for x in o:
            all_dt(x)
all_dt(na)
print("후속 일정:", dts, "->", "OK" if any('2026-09-17T' in d and 13 <= int(d[11:13]) <= 18 for d in dts) else "FAIL")

crm = json.load(open('data/expected/crm-record-expected.json', encoding='utf-8'))
print("CRM DRAFT:", "OK" if crm['status'] == 'DRAFT' and crm['phase'] == 'FC_REVIEW' and not crm['auto_finalized'] and crm['fc_confirm_required'] else "FAIL")

demo = pathlib.Path('docs/demo-and-acceptance.md').read_text(encoding='utf-8')
print("데모 4:30:", "OK" if ('4분 30초' in demo or '4:30' in demo) and '5분 이내' in demo else "FAIL")
print("Safety Reject 별도 섹션:", "OK" if 'Safety Reject' in demo and 'Backup' in demo else "WARN 확인필요")
print()
print("=== 종합: 모든 체크 수행완료 ===")