import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
QUENTE_CAMP = "120248610894960581"
FRIO_CAMP   = "120247963737730581"

# === 1. QUENTE (CBO) -> R$100/dia ===
print("=== QUENTE [CBO] -> R$100/dia ===")
# Current
r = requests.get(f"{BASE}/{QUENTE_CAMP}", params={
    'fields':'id,name,daily_budget','access_token':TOKEN}, timeout=30).json()
print(f"Atual: R${int(r.get('daily_budget',0))/100:.2f}/dia")
p = requests.post(f"{BASE}/{QUENTE_CAMP}", data={
    'daily_budget': '10000',  # R$100
    'access_token': TOKEN
}, timeout=30).json()
print(f"POST resp: {p}")
v = requests.get(f"{BASE}/{QUENTE_CAMP}", params={
    'fields':'daily_budget','access_token':TOKEN}, timeout=30).json()
print(f"Novo: R${int(v.get('daily_budget',0))/100:.2f}/dia")

# === 2. FRIO (ABO) -> distribuir R$100 nos 10 conjuntos ativos (R$10 cada) ===
print(f"\n=== FRIO (ABO) -> R$10/dia cada conjunto ativo (total R$100) ===")
as_r = requests.get(f"{BASE}/{FRIO_CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])
active = [a for a in adsets if a.get('effective_status') == 'ACTIVE']
print(f"Conjuntos ativos: {len(active)}")

success = 0
total_new = 0
for a in active:
    cur = int(a.get('daily_budget', 0))/100
    if cur == 10:
        print(f"  [SKIP] {a['name'][:55]} ja R$10")
        total_new += 10
        success += 1
        continue
    print(f"  Atualizando {a['name'][:55]}: R${cur:.0f} -> R$10")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'daily_budget': '1000',  # R$10
        'access_token': TOKEN
    }, timeout=30).json()
    if pr.get('success') or pr.get('id'):
        success += 1
        total_new += 10
        print(f"     OK")
    else:
        print(f"     ERRO: {pr}")
    time.sleep(0.3)

print(f"\n=== Resumo ===")
print(f"QUENTE: R$100/dia (CBO)")
print(f"FRIO:   R${total_new}/dia ({success} conjuntos x R$10)")
print(f"TOTAL DEVSPACE: R${100+total_new}/dia")
