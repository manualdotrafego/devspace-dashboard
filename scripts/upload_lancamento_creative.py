import requests, os

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120247963737730581"

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)

print("=== ESTADO REAL DOS CONJUNTOS — VALIDACAO CRIATIVO (DevSpace) ===\n")
total_active = 0
all_data = sorted(r.json().get('data',[]), key=lambda x: -int(x.get('daily_budget',0)))
for a in all_data:
    db = int(a.get('daily_budget') or 0)/100
    status = a.get('effective_status','')
    marker = ""
    if status == 'ACTIVE':
        total_active += db
        marker = "[A]"
    elif status == 'IN_PROCESS':
        total_active += db
        marker = "[IP]"
    else:
        marker = f"[{status[:5]}]"
    print(f"  {marker:8} R${db:>7.2f}/d  | {a['name']}")

print(f"\n  TOTAL ATIVO (FRIO): R${total_active:.2f}/dia")
print(f"  + QUENTE [CBO]:     R$100.00/dia")
print(f"  TOTAL DEVSPACE:     R${total_active+100:.2f}/dia")
