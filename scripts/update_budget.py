import requests, os, json, sys

TOKEN    = os.environ['META_ACCESS_TOKEN']
BASE     = 'https://graph.facebook.com/v19.0'
CAMP_ID  = os.environ.get('CAMP_ID', '120248610894960581')
ADD_BRL  = float(os.environ.get('ADD_BRL', '10'))
ADD_CENTS = int(ADD_BRL * 100)

print(f"[+] Campanha {CAMP_ID} (+R${ADD_BRL:.2f})")

r = requests.get(f'{BASE}/{CAMP_ID}', params={
    'fields': 'id,name,daily_budget,effective_status',
    'access_token': TOKEN
}, timeout=30)
data = r.json()
print('[GET]', json.dumps(data, indent=2, ensure_ascii=False))

if 'error' in data:
    print('ERRO:', data['error']['message']); sys.exit(1)

current = int(data.get('daily_budget', 0))
new_budget = current + ADD_CENTS
print(f'R${current/100:.2f} -> R${new_budget/100:.2f}')

u = requests.post(f'{BASE}/{CAMP_ID}', data={
    'daily_budget': new_budget,
    'access_token': TOKEN
}, timeout=30)
print('[POST]', u.text)
if 'success' in u.text:
    print(f'OK: Campanha atualizada para R${new_budget/100:.2f}/dia')
