import requests, os, time
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

# 5 conjuntos com CPL caro (€6+) esta semana
TARGETS = [
    ('[AD SET 1.8]',  'SÓ VIDEO',          '€6,11'),
    ('[AD SET 1.12]', 'vd-teste',          '€6,43'),
    ('[AD SET 1.6]',  'ESTÁTICO MODELADO', '€10,60'),
    ('[AD SET 1.17]', 'vd-teste',          '€10,83'),
    ('[AD SET 1.9]',  'SÓ VIDEO',          '€12,09'),
]

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

print("=== PAUSAR 5 CONJUNTOS COM CPL CARO ===\n")
paused = 0
for pat, desc, cpl in TARGETS:
    a = next((x for x in adsets if x['name'].startswith(pat)), None)
    if not a:
        print(f"  NAO ENCONTRADO: {pat}"); continue
    print(f"  Pausando: {a['name'][:55]}  (CPL {cpl})")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'status':'PAUSED','access_token':TOKEN
    }, timeout=30).json()
    print(f"     POST -> {pr}")
    if pr.get('success'):
        paused += 1
    time.sleep(0.3)

print(f"\n=== {paused}/{len(TARGETS)} pausados ===")

# Final state
print("\n=== CONJUNTOS ATIVOS RESTANTES ===")
r2 = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
total = 0
for a in sorted(r2.json().get('data',[]), key=lambda x: -int(x.get('daily_budget',0))):
    if a.get('effective_status') == 'ACTIVE':
        db = int(a.get('daily_budget') or 0)/100
        total += db
        print(f"  ATIVO €{db:>5.2f}/d | {a['name']}")
print(f"\nTotal ativo: €{total:.2f}/dia")
