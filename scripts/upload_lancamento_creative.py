import requests, os, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"  # WEBNAR Mafra

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget','limit':100,'access_token':TOKEN
}, timeout=30)
adsets = r.json().get('data',[])

print("=== PAUSAR [1.14] e [1.16] ===\n")
for pat in ['[AD SET 1.14]','[AD SET 1.16]']:
    a = next((x for x in adsets if x['name'].startswith(pat)), None)
    if not a:
        print(f"  NAO ENCONTRADO: {pat}"); continue
    print(f"  {a['name']} (status atual: {a.get('effective_status')})")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'status':'PAUSED','access_token':TOKEN
    }, timeout=30).json()
    print(f"     POST -> {pr}")
    time.sleep(0.3)

print("\n=== ATIVOS APOS PAUSE ===")
r2 = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget','limit':100,'access_token':TOKEN
}, timeout=30)
total=0
for a in r2.json().get('data',[]):
    if a.get('effective_status') == 'ACTIVE':
        db = int(a.get('daily_budget') or 0)/100
        total += db
        print(f"  EUR {db:>5.2f}/d  | {a['name']}")
print(f"\n  TOTAL ATIVO: EUR {total:.2f}/dia")
