import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP_ID = "120248546729160002"  # [NOVA CAPTACAO] - [WEBNAR]

r = requests.get(f"{BASE}/{CAMP_ID}", params={
    'fields': 'id,name,effective_status,status',
    'access_token': TOKEN
}, timeout=30).json()
print(f"Campanha: {r.get('name')}")
print(f"Status anterior: {r.get('effective_status')}")

print("\n=== Ativando ===")
p = requests.post(f"{BASE}/{CAMP_ID}", data={
    'status': 'ACTIVE', 'access_token': TOKEN
}, timeout=30).json()
print("Resposta:", p)

v = requests.get(f"{BASE}/{CAMP_ID}", params={
    'fields': 'id,name,effective_status,status,daily_budget,lifetime_budget',
    'access_token': TOKEN
}, timeout=30).json()
print(f"\nStatus pos-ativacao: {v.get('effective_status')}")
db = int(v.get('daily_budget') or 0)/100
lb = int(v.get('lifetime_budget') or 0)/100
if db: print(f"Orcamento: {db:.2f}/dia (campanha)")
if lb: print(f"Orcamento: {lb:.2f} lifetime")
