import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status', 'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

def find(pat):
    for a in adsets:
        if pat in a['name']:
            return a
    return None

print("=== PAUSAR [1.12] e [1.17] ===")
for pat in ['[AD SET 1.12]', '[AD SET 1.17]']:
    a = find(pat)
    if not a:
        print(f"  NAO encontrado: {pat}"); continue
    print(f"  {a['name']} (status atual: {a.get('effective_status')})")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'status': 'PAUSED', 'access_token': TOKEN
    }, timeout=30).json()
    print(f"     -> {pr}")
    time.sleep(0.3)

# Final state
print("\n=== ATIVOS APOS PAUSE ===")
r2 = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget', 'limit': 100, 'access_token': TOKEN
}, timeout=30)
total = 0
for a in r2.json().get('data', []):
    if a.get('effective_status') == 'ACTIVE':
        db = int(a.get('daily_budget') or 0)/100
        total += db
        print(f"  €{db:>5.2f}/d  | {a['name']}")
print(f"\n  TOTAL ATIVO: €{total:.2f}/dia")
