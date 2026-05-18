import requests, os, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"  # DevSpace

# Get all active campaigns with "captacao" in name
r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 100,
    'effective_status': '["ACTIVE"]',
    'access_token': TOKEN
}, timeout=30)
camps = r.json().get('data', [])

# Filter case-insensitive "captacao" (with or without diacritic)
import unicodedata
def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

targets = [c for c in camps if 'captacao' in norm(c.get('name',''))]

print(f"=== ATIVAS NA DEVSPACE: {len(camps)} | COM 'CAPTAÇÃO': {len(targets)} ===\n")

for c in targets:
    print(f"  Pausando: {c['name']}")
    print(f"     id: {c['id']}")
    pr = requests.post(f"{BASE}/{c['id']}", data={
        'status': 'PAUSED', 'access_token': TOKEN
    }, timeout=30).json()
    print(f"     POST -> {pr}")
    time.sleep(0.3)

# Verify
print("\n=== ESTADO FINAL DAS CAMPANHAS ===")
r2 = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
total_active = 0
for c in r2.json().get('data', []):
    status = c.get('effective_status','')
    db = int(c.get('daily_budget') or 0)/100
    marker = "🟢" if status == 'ACTIVE' else "⏸️" if status == 'PAUSED' else "❓"
    if status == 'ACTIVE': total_active += 1
    print(f"  {marker} [{status:8}] R${db:>7.2f}/d | {c['name']}")
print(f"\nCampanhas ativas restantes: {total_active}")
