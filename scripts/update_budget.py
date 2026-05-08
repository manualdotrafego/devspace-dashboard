import requests, os, json, sys

TOKEN    = os.environ['META_ACCESS_TOKEN']
BASE     = 'https://graph.facebook.com/v19.0'
CAMP_ID  = os.environ.get('CAMP_ID', '120248610894960581')
ADD_BRL  = float(os.environ.get('ADD_BRL', '40'))
ADD_CENTS = int(ADD_BRL * 100)

print(f"[+] Atualizando campanha {CAMP_ID} (+R${ADD_BRL:.2f})")

r = requests.get(f'{BASE}/{CAMP_ID}', params={
    'fields': 'id,name,daily_budget,lifetime_budget,effective_status',
    'access_token': TOKEN
}, timeout=30)
data = r.json()
print("[GET]", json.dumps(data, indent=2, ensure_ascii=False))

if 'error' in data:
    print("ERRO:", data['error']['message'])
    sys.exit(1)

current_cents = int(data.get('daily_budget') or 0)
new_cents     = current_cents + ADD_CENTS

print(f"[~] Orcamento: R${current_cents/100:.2f} -> R${new_cents/100:.2f}")

u = requests.post(f'{BASE}/{CAMP_ID}', data={
    'daily_budget': new_cents,
    'access_token': TOKEN
}, timeout=30)
print("[POST]", u.text)

if u.ok and 'success' in u.text:
    print(f"OK: Campanha atualizada para R${new_cents/100:.2f}/dia")
else:
    print("Verifique resposta acima")
