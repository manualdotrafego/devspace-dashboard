import requests, os, json, time
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()

def get_leads(actions):
    leads = 0
    for act in actions or []:
        t = act.get('action_type','')
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, int(act.get('value',0)))
    return leads

# Get all adsets
r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

# For each ACTIVE adset, get its 7d CPL
print(f"=== AVALIANDO CONJUNTOS ATIVOS (CPL ult 7d) ===\n")
to_pause = []
keep = []
for a in adsets:
    if a.get('effective_status') != 'ACTIVE': continue
    aid = a['id']
    ins_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields':'spend,actions',
        'time_range': json.dumps({'since':since,'until':until}),
        'access_token':TOKEN
    }, timeout=30)
    ins = ins_r.json().get('data', [])
    if not ins:
        print(f"  [SEM DADOS] {a['name'][:55]} — mantido")
        keep.append(a); continue
    d = ins[0]
    sp = float(d.get('spend',0))
    lds = get_leads(d.get('actions',[]))
    cpl = sp/lds if lds > 0 else float('inf') if sp > 0 else 0
    if cpl > 5.0:
        cpl_str = f"€{cpl:.2f}" if cpl != float('inf') else f"€{sp:.2f}/0 leads"
        print(f"  PAUSAR  CPL {cpl_str:>8}  | €{sp:.2f} / {lds} leads | {a['name']}")
        to_pause.append(a)
    else:
        cpl_str = f"€{cpl:.2f}" if lds > 0 else "—"
        print(f"  MANTER  CPL {cpl_str:>8}  | €{sp:.2f} / {lds} leads | {a['name']}")
        keep.append(a)

print(f"\n=== EXECUTANDO PAUSE em {len(to_pause)} conjuntos ===\n")
paused = 0
for a in to_pause:
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'status':'PAUSED','access_token':TOKEN
    }, timeout=30).json()
    if pr.get('success'):
        paused += 1
        print(f"  ✓ {a['name'][:60]}")
    else:
        print(f"  ✗ {a['name'][:60]} -> {pr}")
    time.sleep(0.3)

print(f"\n=== ESTADO FINAL: {paused}/{len(to_pause)} pausados ===\n")
# Re-fetch and show only ACTIVE
r2 = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
total_active = 0
print("Conjuntos ATIVOS restantes:")
for a in sorted(r2.json().get('data',[]), key=lambda x: -int(x.get('daily_budget',0))):
    if a.get('effective_status') == 'ACTIVE':
        db = int(a.get('daily_budget') or 0)/100
        total_active += db
        print(f"  €{db:>5.2f}/d | {a['name']}")
print(f"\nTotal ativo: €{total_active:.2f}/dia")
