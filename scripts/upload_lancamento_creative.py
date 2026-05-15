import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120247963737730581"  # VALIDACAO CRIATIVO

# Find target adsets
r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget', 
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

# (pat, new_budget_cents, label)
UPDATES = [
    ('[AD SET 1.3]',  '20000', 'R$200'),
    ('[AD SET 1.8]',  '20000', 'R$200'),
    ('[AD SET 1.9]',  '20000', 'R$200'),
    ('[AD SET 1.10]', '20000', 'R$200'),
    ('[AD SET 1.21]', '40000', 'R$400'),
]

print("=== ATUALIZAR ORCAMENTOS ===\n")
for pat, new_budget, label in UPDATES:
    a = next((x for x in adsets if x['name'].startswith(pat)), None)
    if not a:
        print(f"  NAO ENCONTRADO: {pat}"); continue
    cur = int(a.get('daily_budget') or 0)/100
    print(f"  {a['name']}")
    print(f"     Status: {a.get('effective_status')} | Atual: R${cur:.2f}/d -> Novo: {label}/d")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'daily_budget': new_budget, 'access_token': TOKEN
    }, timeout=30).json()
    print(f"     POST -> {pr}")
    time.sleep(0.4)

# Final state
print("\n=== ATIVOS APOS UPDATE ===")
r2 = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget', 
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
total = 0
for a in sorted(r2.json().get('data', []), key=lambda x: -int(x.get('daily_budget',0))):
    if a.get('effective_status') == 'ACTIVE':
        db = int(a.get('daily_budget') or 0)/100
        total += db
        print(f"  R${db:>7.2f}/d  | {a['name']}")
print(f"\n  TOTAL FRIO: R${total:.2f}/dia")
print(f"  + QUENTE (CBO): R$100/dia")
print(f"  TOTAL DEVSPACE: R${total+100:.2f}/dia")
