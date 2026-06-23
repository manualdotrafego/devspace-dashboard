import requests, os
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"

# 1. Check permissions
print("=== /me/permissions ===")
r = requests.get(f"{BASE}/me/permissions", params={'access_token':TOKEN}, timeout=30).json()
for p in r.get('data', [])[:30]:
    print(f"  {p.get('status'):<8} {p.get('permission')}")

print("\n=== /me ===")
r = requests.get(f"{BASE}/me", params={'access_token':TOKEN, 'fields':'id,name'}, timeout=30).json()
print(f"  {r}")

# 2. Try /me/accounts to get page access tokens
print("\n=== /me/accounts ===")
r = requests.get(f"{BASE}/me/accounts", params={
    'access_token':TOKEN,
    'fields':'id,name,access_token,tasks'
}, timeout=30).json()
if 'data' in r:
    for pg in r['data'][:10]:
        has_token = 'access_token' in pg
        tasks = ','.join(pg.get('tasks',[]))[:60]
        print(f"  Page: {pg.get('name','?')} | id={pg.get('id','?')}")
        print(f"        has_token={has_token} | tasks={tasks}")
else:
    print(f"  ERROR: {r}")

# 3. Try the system_user/account approach for joao mafra page
print("\n=== Trying page direct: 110278364765662 ===")
r = requests.get(f"{BASE}/110278364765662", params={
    'access_token':TOKEN,
    'fields':'id,name,access_token'
}, timeout=30).json()
print(f"  {r}")
