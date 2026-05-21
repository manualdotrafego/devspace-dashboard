import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"  # [NOVA CAPTACAO] - [WEBNAR]

r = requests.get(f"{BASE}/{CAMP}", params={
    'fields':'name,status,effective_status', 'access_token':TOKEN
}, timeout=30).json()
print(f"Campanha: {r.get('name')}")
print(f"Status atual: {r.get('effective_status')}")

pr = requests.post(f"{BASE}/{CAMP}", data={
    'status':'ACTIVE', 'access_token':TOKEN
}, timeout=30).json()
print(f"POST ativar -> {pr}")

v = requests.get(f"{BASE}/{CAMP}", params={
    'fields':'name,status,effective_status', 'access_token':TOKEN
}, timeout=30).json()
print(f"Status apos: status={v.get('status')} | effective={v.get('effective_status')}")

# List adsets state
print("\n=== CONJUNTOS ===")
as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget', 'limit':100, 'access_token':TOKEN
}, timeout=30)
total = 0
for a in as_r.json().get('data', []):
    st = a.get('effective_status','')
    db = int(a.get('daily_budget') or 0)/100
    if st == 'ACTIVE':
        total += db
        print(f"  ATIVO  €{db:>6.2f}/d | {a['name']}")
    else:
        print(f"  [{st}] €{db:>6.2f}/d | {a['name']}")
print(f"\nTotal ativo: €{total:.2f}/dia")
