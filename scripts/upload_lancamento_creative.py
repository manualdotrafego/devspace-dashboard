import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"  # Joao Mafra Lancamento

r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields':'id,name,status,effective_status,daily_budget',
    'limit':200, 'access_token':TOKEN
}, timeout=30)
camps = r.json().get('data', [])
print(f"=== TODAS AS CAMPANHAS — Joao Mafra Lancamento ({len(camps)}) ===\n")
for c in sorted(camps, key=lambda x: x.get('effective_status','')):
    st = c.get('effective_status','')
    db = int(c.get('daily_budget') or 0)/100
    mark = "ATIVA " if st == 'ACTIVE' else f"[{st}]"
    print(f"  {mark:10} | {c['name']}")
    print(f"             id={c['id']}")
