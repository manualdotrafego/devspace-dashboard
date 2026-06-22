import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,status,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)

print("=== ESTADO DOS CONJUNTOS — WEBNAR ===\n")
active = paused = 0
for a in sorted(r.json().get('data',[]), key=lambda x: (x.get('effective_status'),x['name'])):
    eff = a.get('effective_status','')
    st = a.get('status','')
    db = int(a.get('daily_budget') or 0)/100
    if eff == 'ACTIVE':
        active += 1
        print(f"  ATIVO    | status={st:<7} effective={eff:<10} €{db:>5.2f}/d | {a['name']}")
    else:
        paused += 1
        print(f"  PAUSADO  | status={st:<7} effective={eff:<10} €{db:>5.2f}/d | {a['name']}")

print(f"\nTotal: {active} ATIVOS, {paused} PAUSADOS")
