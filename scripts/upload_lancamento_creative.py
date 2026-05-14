import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"  # [NOVA CAPTACAO] - [WEBNAR]

today = date.today()
since = (today - timedelta(days=6)).isoformat()
until = today.isoformat()

print(f"=== ATIVOS — Campanha [NOVA CAPTACAO] - [WEBNAR] ===")
print(f"Periodo: {since} -> {until} (ultimos 6 dias)")

as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget,lifetime_budget,optimization_goal',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])
active = [a for a in adsets if a.get('effective_status') == 'ACTIVE']
print(f"\nTotal conjuntos: {len(adsets)} | ATIVOS: {len(active)}\n")

results = []
for a in active:
    aid = a['id']
    name = a['name']
    db = int(a.get('daily_budget') or 0)/100
    lb = int(a.get('lifetime_budget') or 0)/100
    
    # insights
    ins_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields': 'spend,impressions,clicks,actions,cpc,cpm,ctr,reach,frequency',
        'time_range': json.dumps({'since': since, 'until': until}),
        'access_token': TOKEN
    }, timeout=30)
    ins = ins_r.json().get('data', [])
    
    if not ins:
        results.append({
            'name': name, 'id': aid, 'db': db, 'lb': lb,
            'spend': 0, 'leads': 0, 'cpl': 0, 'imps': 0, 'ctr': 0, 'cpc': 0
        })
        continue
    
    d = ins[0]
    spend = float(d.get('spend', 0))
    leads = link_clicks = lp_views = 0
    for act in d.get('actions', []):
        t = act.get('action_type', '')
        v = int(act.get('value', 0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': link_clicks = v
        elif t == 'landing_page_view': lp_views = v
    cpl = spend/leads if leads > 0 else 0
    results.append({
        'name': name, 'id': aid, 'db': db, 'lb': lb,
        'spend': spend, 'leads': leads, 'cpl': cpl,
        'imps': int(d.get('impressions',0)),
        'ctr': float(d.get('ctr',0)), 'cpc': float(d.get('cpc',0)),
        'reach': int(d.get('reach',0)), 'freq': float(d.get('frequency',0)),
        'link_clicks': link_clicks, 'lp_views': lp_views,
    })

# Sort by leads desc
results.sort(key=lambda x: -x['leads'])

print(f"{'#':<3} {'Conjunto':<50} {'Budget':<12} {'Gasto':>9} {'Leads':>6} {'CPL':>8} {'CTR':>6} {'CPC':>6}")
print("-" * 120)
total_sp = total_lds = total_imps = 0
for i, r in enumerate(results, 1):
    bud = f"€{r['db']:.0f}/d" if r['db'] else (f"€{r['lb']:.0f} lt" if r['lb'] else "--")
    print(f"{i:<3} {r['name'][:50]:<50} {bud:<12} €{r['spend']:>7.2f} {r['leads']:>6} €{r['cpl']:>6.2f} {r['ctr']:>5.2f}% €{r['cpc']:>4.2f}")
    total_sp += r['spend']; total_lds += r['leads']; total_imps += r['imps']

print("-" * 120)
total_cpl = total_sp/total_lds if total_lds else 0
print(f"{'TOTAIS':<54} {'':<12} €{total_sp:>7.2f} {total_lds:>6} €{total_cpl:>6.2f}")
print(f"\nImpressoes totais: {total_imps:,}")
