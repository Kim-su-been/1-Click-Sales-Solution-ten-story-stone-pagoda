# -*- coding: utf-8
# Status Contract Freeze — Golden Expected 에서 실제 상태 필드/값 추출
import json, sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
ROOT = pathlib.Path('/Users/siyoung/Desktop/one-pick-rescue-agent')
EXP = ROOT/'data/expected'

print("== Status Contract Freeze: 상태값 전수 추출 ==")
# 1) CRM
crm = json.load(open(EXP/'crm-record-expected.json', encoding='utf-8'))
print("\n[CRM Record]")
for k in ['status','phase','auto_finalized','fc_confirm_required']:
    print(f"  {k} = {crm.get(k)!r}")

# 2) Next Action / Calendar
na = json.load(open(EXP/'next-action-expected.json', encoding='utf-8'))
print("\n[Next Action]")
for a in na['next_actions']:
    print(f"  {a['action_id']} type={a['action_type']!r} status={a['status']!r} due={a['due_datetime']!r}")
cal = na['calendar_candidate']
print(f"  calendar_candidate: status={cal['status']!r} due={cal['due_datetime']!r} duration={cal['duration_minutes']}")

# 3) Session analysis
sa = json.load(open(EXP/'session-analysis-expected.json', encoding='utf-8'))
print("\n[Session Analysis]")
print("  outcome.value =", sa['analysis']['outcome']['value'])
print("  followup.needed =", sa['analysis']['followup_requested']['needed'])
print("  followup.preferred_datetime =", sa['analysis']['followup_requested']['preferred_datetime'])

# 4) Contact script
cs = json.load(open(EXP/'contact-script-expected.json', encoding='utf-8'))
print("\n[Contact Script]")
print("  contact_reason.code =", cs['contact_reason']['code'])
print("  scripts keys =", list(cs['scripts'].keys()))
print("  grounding_docs count =", len(cs['grounding_docs']))

# 5) Safety
sr = json.load(open(EXP/'safety-reject-expected.json', encoding='utf-8'))
print("\n[Safety Reject]")
print("  review_result.decision =", sr['review_result']['decision'])
print("  violations types =", [v['violation_type'] for v in sr['rejected_script']['violations']])
print("  grounding_status =", sr['rejected_script']['violations'][0]['grounding_status'])

# 6) daily pick evidence
dp = json.load(open(EXP/'daily_pick_expected.json', encoding='utf-8'))
print("\n[Daily Pick]")
print("  evidence.type =", dp['evidence'].get('type'))
print("  candidates eligibility values =", sorted({c['eligibility'] for c in dp['candidates']}))
print("  exclusion_reason values =", sorted({c['exclusion_reason'] for c in dp['candidates'] if c['exclusion_reason']}))