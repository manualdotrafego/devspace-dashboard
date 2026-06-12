import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
r = requests.get(f"{BASE}/120248546729160002", params={
    'fields':'name,status,effective_status','access_token':TOKEN
}, timeout=30).json()
print(f"  {r.get('name')}")
print(f"  status={r.get('status')} | effective={r.get('effective_status')}")
