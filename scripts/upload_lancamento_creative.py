import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"  # [NOVA CAPTACAO] - [WEBNAR]

today = date.today()
# Monday this week (today is 2026-06-12, Friday)
days_since_mon = today.weekday()  # Mon=0, Fri=4
monday = today - timedelta(days=days_since_mon)
since = monday.isoformat()
until = today.isoformat()

print(f"=== WEBNAR — Resultados esta semana ({since} -> {until}) ===\n")

# Get all adsets
as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])

results = []
for a in adsets:
    aid = a['id']
    ins_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields':'spend,impressions,clicks,actions,cpc,cpm,ctr,reach,frequency',
        'time_range': json.dumps({'since':since,'until':until}),
        'access_token':TOKEN
    }, timeout=30)
    ins = ins_r.json().get('data', [])
    if not ins:
        continue
    d = ins[0]
    spend = float(d.get('spend',0))
    if spend == 0:
        continue
    leads = link_clicks = lp_views = 0
    for act in d.get('actions',[]):
        t = act.get('action_type','')
        v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads,v)
        elif t == 'link_click': link_clicks = v
        elif t == 'landing_page_view': lp_views = v
    cpl = spend/leads if leads > 0 else 0
    results.append({
        'name': a['name'],
        'status': a.get('effective_status'),
        'budget': int(a.get('daily_budget') or 0)/100,
        'spend': spend, 'leads': leads, 'cpl': cpl,
        'imps': int(d.get('impressions',0)),
        'ctr': float(d.get('ctr',0)),
        'cpc': float(d.get('cpc',0)),
        'link_clicks': link_clicks, 'lp_views': lp_views,
        'reach': int(d.get('reach',0)), 'freq': float(d.get('frequency',0)),
    })

results.sort(key=lambda x: -x['leads'])
total_sp = total_lds = total_imps = 0
print(f"{'Conjunto':<50} {'St':<4} {'Bud':<7} {'Gasto':>9} {'Lds':>5} {'CPL':>8} {'CTR':>6}")
print("-" * 110)
for r in results:
    st = 'A' if r['status']=='ACTIVE' else 'P'
    bud = f"€{r['budget']:.0f}/d" if r['budget'] else "—"
    cpl = f"€{r['cpl']:.2f}" if r['leads']>0 else "—"
    print(f"{r['name'][:50]:<50} {st:<4} {bud:<7} €{r['spend']:>6.2f} {r['leads']:>5} {cpl:>8} {r['ctr']:>5.2f}%")
    total_sp += r['spend']; total_lds += r['leads']; total_imps += r['imps']

print("-" * 110)
total_cpl = total_sp/total_lds if total_lds > 0 else 0
print(f"{'TOTAIS':<54}     €{total_sp:>6.2f} {total_lds:>5} €{total_cpl:>5.2f}")
print(f"\nImpressoes: {total_imps:,}")
