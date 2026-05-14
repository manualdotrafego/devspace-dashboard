import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

# Get all adsets
r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

# Match by name patterns
def find(pattern):
    for a in adsets:
        if pattern in a['name']:
            return a
    return None

targets_pause = [
    ('[AD SET 1.4]', None),
    ('[AD SET 1.2]', None),
    ('[AD SET 1.13]', None),
]
targets_budget = [
    ('[AD SET 1.18]', 1500),  # €15
    ('[AD SET 1.19]', 1500),  # €15
]

print("=== PAUSAR ===")
for pat, _ in targets_pause:
    a = find(pat)
    if not a:
        print(f"  NAO encontrado: {pat}"); continue
    print(f"  {a['name'][:55]} (status atual: {a.get('effective_status')})")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'status': 'PAUSED', 'access_token': TOKEN
    }, timeout=30).json()
    print(f"     -> {pr}")
    time.sleep(0.3)

print("\n=== AJUSTAR BUDGET PARA €15/dia ===")
for pat, new_db in targets_budget:
    a = find(pat)
    if not a:
        print(f"  NAO encontrado: {pat}"); continue
    cur = int(a.get('daily_budget') or 0)/100
    print(f"  {a['name'][:55]} (atual: €{cur:.2f}/d)")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'daily_budget': str(new_db), 'access_token': TOKEN
    }, timeout=30).json()
    print(f"     -> {pr}")
    time.sleep(0.3)

# Verify final state
print("\n=== ESTADO FINAL ATIVOS ===")
r2 = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets2 = r2.json().get('data', [])
active = [a for a in adsets2 if a.get('effective_status') == 'ACTIVE']
total = 0
for a in sorted(active, key=lambda x: -int(x.get('daily_budget') or 0)):
    db = int(a.get('daily_budget') or 0)/100
    total += db
    print(f"  €{db:>5.2f}/d  | {a['name'][:60]}")
print(f"\n  TOTAL ATIVO: €{total:.2f}/dia ({len(active)} conjuntos)")
