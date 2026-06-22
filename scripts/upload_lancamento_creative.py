import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"  # [NOVA CAPTACAO] - [WEBNAR]

today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()

def get_leads(actions):
    leads = link_clicks = lp_views = 0
    for act in actions or []:
        t = act.get('action_type','')
        v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': link_clicks = v
        elif t == 'landing_page_view': lp_views = v
    return leads, link_clicks, lp_views

print(f"=== WEBNAR - RASTREIO ULTIMOS 7 DIAS ({since} -> {until}) ===\n")

# 1. TOTAL campanha
print("### TOTAL CAMPANHA ###")
r = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend,impressions,clicks,actions,reach,frequency,ctr,cpc,cpm',
    'time_range': json.dumps({'since':since,'until':until}),
    'access_token':TOKEN
}, timeout=30)
data = r.json().get('data', [])
if data:
    d = data[0]
    spend = float(d.get('spend',0))
    leads, link_clicks, lp_views = get_leads(d.get('actions',[]))
    cpl = spend/leads if leads > 0 else 0
    print(f"  Gasto:      EUR{spend:>8.2f}")
    print(f"  Leads:      {leads:>10}")
    print(f"  CPL:        EUR{cpl:>8.2f}")
    print(f"  Impressoes: {int(d.get('impressions',0)):>10,}")
    print(f"  Reach:      {int(d.get('reach',0)):>10,}")
    print(f"  Freq:       {float(d.get('frequency',0)):>10.2f}")
    print(f"  Clicks:     {int(d.get('clicks',0)):>10,}")
    print(f"  LinkClicks: {link_clicks:>10,}")
    print(f"  LP views:   {lp_views:>10,}")
    print(f"  CTR:        {float(d.get('ctr',0)):>10.2f}%")
    print(f"  CPC:        EUR{float(d.get('cpc',0)):>8.2f}")
    print(f"  CPM:        EUR{float(d.get('cpm',0)):>8.2f}")
    print(f"  Click>LP:   {(lp_views/link_clicks*100) if link_clicks else 0:>9.1f}%")
    print(f"  LP>Lead:    {(leads/lp_views*100) if lp_views else 0:>9.1f}%")

# 2. Dia a dia
print(f"\n### EVOLUCAO DIARIA ###")
r = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend,impressions,clicks,actions',
    'time_range': json.dumps({'since':since,'until':until}),
    'time_increment': 1,
    'access_token':TOKEN
}, timeout=30)
days = r.json().get('data', [])
print(f"  {'Data':<12} {'Dia':<5} {'Gasto':>9} {'Leads':>6} {'CPL':>8} {'Imps':>8} {'Clicks':>7}")
for d in days:
    sp = float(d.get('spend',0))
    leads, lc, lp = get_leads(d.get('actions',[]))
    cpl = f"EUR{sp/leads:.2f}" if leads > 0 else "-"
    dt = d.get('date_start','')
    # weekday name
    from datetime import datetime
    wd = datetime.strptime(dt,'%Y-%m-%d').strftime('%a')
    print(f"  {dt:<12} {wd:<5} EUR{sp:>5.2f} {leads:>6} {cpl:>8} {int(d.get('impressions',0)):>8,} {int(d.get('clicks',0)):>7,}")

# 3. Conjuntos
print(f"\n### CONJUNTOS ATIVOS NO PERIODO ###")
as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,effective_status,daily_budget',
    'limit':100,'access_token':TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])

rows = []
for a in adsets:
    aid = a['id']
    ins_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields':'spend,impressions,actions,ctr,cpc,frequency',
        'time_range': json.dumps({'since':since,'until':until}),
        'access_token':TOKEN
    }, timeout=30)
    ins = ins_r.json().get('data', [])
    if not ins: continue
    d = ins[0]
    sp = float(d.get('spend',0))
    if sp == 0: continue
    leads, lc, lp = get_leads(d.get('actions',[]))
    cpl = sp/leads if leads > 0 else 0
    rows.append({
        'name': a['name'],
        'status': a.get('effective_status'),
        'budget': int(a.get('daily_budget') or 0)/100,
        'spend': sp, 'leads': leads, 'cpl': cpl,
        'imps': int(d.get('impressions',0)),
        'ctr': float(d.get('ctr',0)),
        'cpc': float(d.get('cpc',0)),
        'freq': float(d.get('frequency',0)),
        'lc': lc, 'lp': lp,
    })

rows.sort(key=lambda x: -x['leads'])
print(f"  {'St':<4} {'Conjunto':<48} {'Bud':<8} {'Gasto':>9} {'Leads':>6} {'CPL':>8} {'CTR':>6} {'CPC':>6}")
print("  " + "-"*108)
for r in rows:
    st = 'A' if r['status']=='ACTIVE' else 'P'
    bud = f"EUR{r['budget']:.0f}/d" if r['budget'] else "-"
    cpl = f"EUR{r['cpl']:.2f}" if r['leads']>0 else "-"
    print(f"  {st:<4} {r['name'][:48]:<48} {bud:<8} EUR{r['spend']:>5.2f} {r['leads']:>6} {cpl:>8} {r['ctr']:>5.2f}% EUR{r['cpc']:>4.2f}")

# Best/Worst
ativos_com_leads = [r for r in rows if r['leads']>0]
if ativos_com_leads:
    best = min(ativos_com_leads, key=lambda x: x['cpl'])
    worst = max(ativos_com_leads, key=lambda x: x['cpl'])
    print(f"\n  MELHOR CPL: {best['name'][:50]} -> EUR{best['cpl']:.2f}")
    print(f"  PIOR CPL:   {worst['name'][:50]} -> EUR{worst['cpl']:.2f}")
