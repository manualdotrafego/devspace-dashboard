import requests, os

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"

r = requests.get(f"{BASE}/me/adaccounts", params={
    'access_token': TOKEN,
    'fields': 'id,name,account_status,currency,business',
    'limit': 200
}, timeout=20)

print(f"Status: {r.status_code}")
if r.ok:
    data = r.json().get('data', [])
    print(f"Total contas: {len(data)}")
    
    print("\n=== BUSCA 'dev' ou 'space' ===")
    matches = [a for a in data if 'dev' in a['name'].lower() or 'space' in a['name'].lower()]
    if matches:
        for a in matches:
            print(f"  ✅ FOUND: {a['name']} | {a['id']}")
    else:
        print("  Não encontrado neste token")
    
    print("\n=== TODAS AS CONTAS ===")
    for a in sorted(data, key=lambda x: x['name']):
        st = {1:'ATIVO',2:'DESATIV',3:'BLOQUEADO'}.get(a.get('account_status',0),'?')
        biz = a.get('business',{}).get('name','—')
        print(f"  [{st}] {a['name']} | {a['id']} | {biz}")
else:
    print(r.text[:300])
