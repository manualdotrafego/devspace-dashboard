import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"

for cid, name in [
    ("120248610894960581", "QUENTE [CBO]"),
    ("120247963737730581", "VALIDACAO CRIATIVO"),
]:
    r = requests.get(f"{BASE}/{cid}", params={
        'fields':'name,status,effective_status,daily_budget',
        'access_token':TOKEN
    }, timeout=30).json()
    print(f"  {name}")
    print(f"    status={r.get('status')} | effective={r.get('effective_status')}")
