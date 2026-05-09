import requests, os, json

TOKEN    = os.environ['META_ACCESS_TOKEN']
BASE     = 'https://graph.facebook.com/v19.0'
ADSET_ID = '120247963788170581'
CAMP_ID  = '120247963737730581'

# Get adset budget info
r = requests.get(f'{BASE}/{ADSET_ID}', params={
    'fields': 'id,name,status,effective_status,daily_budget,lifetime_budget,bid_amount',
    'access_token': TOKEN
}, timeout=30)
print('[ADSET]', json.dumps(r.json(), indent=2, ensure_ascii=False))

# Get campaign budget (CBO)
r2 = requests.get(f'{BASE}/{CAMP_ID}', params={
    'fields': 'id,name,daily_budget,lifetime_budget,budget_remaining',
    'access_token': TOKEN
}, timeout=30)
print('[CAMPAIGN]', json.dumps(r2.json(), indent=2, ensure_ascii=False))

# Pause the adset
print('\n[~] Pausando AD SET 1.5...')
u = requests.post(f'{BASE}/{ADSET_ID}', data={
    'status': 'PAUSED',
    'access_token': TOKEN
}, timeout=30)
print('[POST]', u.text)
if 'success' in u.text:
    print('OK: Conjunto pausado!')
