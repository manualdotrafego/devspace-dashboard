import requests, os, time
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

TARGETS = [
    ("120248912638000002", "[AD SET 1.7 alterado dia 12] - [SÓ VIDEO]"),
    ("120248547611860002", "[AD SET 1.4] - [E_AD01 NOVO]"),
]

print("=== PAUSAR [1.7 alt] e [1.4] ===\n")
paused = 0
for cid, name in TARGETS:
    print(f"  Pausando: {name}")
    pr = requests.post(f"{BASE}/{cid}", data={
        'status':'PAUSED','access_token':TOKEN
    }, timeout=30).json()
    print(f"     POST -> {pr}")
    if pr.get('success'):
        paused += 1
    time.sleep(0.3)

print(f"\n=== {paused}/{len(TARGETS)} pausados ===")

# Final state
print("\n=== ATIVOS RESTANTES ===")
r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
total = 0
for a in sorted(r.json().get('data',[]), key=lambda x: -int(x.get('daily_budget',0))):
    if a.get('effective_status') == 'ACTIVE':
        db = int(a.get('daily_budget') or 0)/100
        total += db
        print(f"  ATIVO €{db:>5.2f}/d | {a['name']}")
print(f"\nTotal ativo: €{total:.2f}/dia")
