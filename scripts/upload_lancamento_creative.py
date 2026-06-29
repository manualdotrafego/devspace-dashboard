import requests, os, unicodedata
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields':'id,name,status,effective_status,daily_budget,created_time,start_time',
    'limit':200,'access_token':TOKEN
}, timeout=30)
camps = r.json().get('data', [])

print("=== CAMPANHAS COM 'WEBNAR/WEBINAR' OU CAPTACAO ===\n")
for c in camps:
    nm = norm(c.get('name',''))
    if 'webnar' in nm or 'webinar' in nm or 'captac' in nm or 'capta' in nm:
        st = c.get('effective_status','')
        db = int(c.get('daily_budget') or 0)/100
        mark = "🟢 ATIVA" if st=='ACTIVE' else f"⏸️ {st}"
        print(f"{mark} | {c['name']}")
        print(f"   id={c['id']} | budget=€{db:.2f}/d | criada={c.get('created_time','')[:10]} | iniciada={c.get('start_time','')[:10]}")
        print()

print("\n=== TODAS AS ATIVAS NA CONTA ===")
for c in camps:
    if c.get('effective_status') == 'ACTIVE':
        db = int(c.get('daily_budget') or 0)/100
        print(f"  🟢 €{db:>6.2f}/d | {c['name']} (id={c['id']})")
