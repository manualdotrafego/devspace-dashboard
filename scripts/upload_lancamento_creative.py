import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"  # [NOVA CAPTAÇÃO] - [WEBNAR]

r = requests.get(f"{BASE}/{CAMP}", params={
    'fields':'name,status,effective_status','access_token':TOKEN
}, timeout=30).json()
print(f"Campanha: {r.get('name')}")
print(f"Status atual: {r.get('effective_status')}")

pr = requests.post(f"{BASE}/{CAMP}", data={
    'status':'PAUSED','access_token':TOKEN
}, timeout=30).json()
print(f"POST pausar -> {pr}")

v = requests.get(f"{BASE}/{CAMP}", params={
    'fields':'name,status,effective_status','access_token':TOKEN
}, timeout=30).json()
print(f"Status apos: status={v.get('status')} | effective={v.get('effective_status')}")
