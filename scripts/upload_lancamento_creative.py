import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP_ID = "120248546729160002"  # [NOVA CAPTACAO] - [WEBNAR]

# Confirm name + current status
r = requests.get(f"{BASE}/{CAMP_ID}", params={
    'fields': 'id,name,effective_status,status',
    'access_token': TOKEN
}, timeout=30)
c = r.json()
print(f"Campanha: {c.get('name')}")
print(f"Status atual: {c.get('effective_status')}  (raw: {c.get('status')})")

# Pause
print("\n=== Pausando ===")
p_r = requests.post(f"{BASE}/{CAMP_ID}", data={
    'status': 'PAUSED',
    'access_token': TOKEN
}, timeout=30)
print("Resposta:", p_r.json())

# Verify
v_r = requests.get(f"{BASE}/{CAMP_ID}", params={
    'fields': 'id,name,effective_status,status',
    'access_token': TOKEN
}, timeout=30)
v = v_r.json()
print(f"\nStatus pos-pause: {v.get('effective_status')}  (raw: {v.get('status')})")
