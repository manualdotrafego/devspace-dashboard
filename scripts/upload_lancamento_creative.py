import requests, os, unicodedata
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"
def norm(s): return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn').lower()

r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields':'id,name,effective_status,created_time,start_time,daily_budget','limit':300,'access_token':TOKEN}, timeout=30)
camps = r.json().get('data', [])
print(f"Total campanhas na conta: {len(camps)}\n")
print("=== ATIVAS (qualquer) ===")
for c in camps:
    if c.get('effective_status')=='ACTIVE':
        db=int(c.get('daily_budget') or 0)/100
        print(f"  🟢 EUR{db:.0f}/d | {c['name']} | criada {c.get('created_time','')[:10]} | id={c['id']}")
print("\n=== Webinar/masterclass/escala/A-B-C (todas, ordenadas por criacao) ===")
rel=[c for c in camps if any(k in norm(c['name']) for k in ['webnar','webinar','masterclass','escala','captac','[a]','[b]','[c]',' a ',' b ',' c '])]
for c in sorted(rel, key=lambda x:x.get('created_time',''), reverse=True):
    print(f"  [{c.get('effective_status'):<14}] {c['name']} | criada {c.get('created_time','')[:16]} | id={c['id']}")
