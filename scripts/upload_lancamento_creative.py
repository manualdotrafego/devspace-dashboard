import requests, os, time
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"

TO_PAUSE = [
    ("120248546729160002", "[NOVA CAPTAÇÃO] - [WEBNAR]"),
    ("120249001823230002", "[EVENTO PRESENCIAL] - [VALIDAÇÃO]"),
]
KEEP = ("120249814173860002", "[TRÁFEGO INSTAGRAM] - [VISITA]")

print("=== PAUSAR WEBNAR + PRESENCIAL ===\n")
for cid, name in TO_PAUSE:
    print(f"  Pausando: {name}")
    pr = requests.post(f"{BASE}/{cid}", data={
        'status':'PAUSED', 'access_token':TOKEN
    }, timeout=30).json()
    print(f"     POST -> {pr}")
    time.sleep(0.4)

print(f"\n=== VERIFICACAO FINAL ===")
r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields':'id,name,status,effective_status',
    'limit':200, 'access_token':TOKEN
}, timeout=30)
active = [c for c in r.json().get('data',[]) if c.get('effective_status')=='ACTIVE']
print(f"Campanhas ATIVAS restantes: {len(active)}")
for c in active:
    print(f"  🟢 {c['name']}  (id={c['id']})")

# Confirm the 2 are paused
print(f"\nStatus das pausadas:")
for cid, name in TO_PAUSE:
    v = requests.get(f"{BASE}/{cid}", params={
        'fields':'status,effective_status','access_token':TOKEN
    }, timeout=30).json()
    print(f"  ⏸️ {name}: status={v.get('status')} effective={v.get('effective_status')}")
