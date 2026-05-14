import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,status,effective_status,daily_budget,lifetime_budget,configured_status,start_time,end_time,issues_info',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

# Focus on [1.18] and [1.19]
print("=== Status detalhado de [1.18] e [1.19] ===\n")
for a in adsets:
    if '[AD SET 1.18]' in a['name'] or '[AD SET 1.19]' in a['name']:
        print(f"NOME: {a['name']}")
        print(f"  id: {a['id']}")
        print(f"  status (configured): {a.get('configured_status')}")
        print(f"  effective_status: {a.get('effective_status')}")
        print(f"  daily_budget: {a.get('daily_budget')} (={int(a.get('daily_budget') or 0)/100:.2f})")
        print(f"  lifetime_budget: {a.get('lifetime_budget')}")
        print(f"  start_time: {a.get('start_time')}")
        print(f"  end_time: {a.get('end_time')}")
        print(f"  issues: {a.get('issues_info')}")
        print()

# All adsets full list
print("\n=== TODOS os conjuntos do WEBNAR ===")
for a in sorted(adsets, key=lambda x: x['name']):
    db = int(a.get('daily_budget') or 0)/100
    es = a.get('effective_status')
    print(f"  [{es:<20}] €{db:>5.2f}/d  | {a['name'][:60]}")
