import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"

CAMPS = [
    ("120247963737730581", "VALIDAÇÃO CRIATIVO (frio - ABO)"),
    ("120248610894960581", "QUENTE (CBO)"),
]

def fetch(cid, label, preset='maximum'):
    r = requests.get(f"{BASE}/{cid}/insights", params={
        'fields': 'spend,impressions,clicks,actions,cpc,cpm,ctr,reach,frequency,date_start,date_stop',
        'date_preset': preset,
        'access_token': TOKEN
    }, timeout=30)
    data = r.json().get('data', [])
    if not data: 
        return None
    d = data[0]
    spend = float(d.get('spend', 0))
    imps = int(d.get('impressions', 0))
    reach = int(d.get('reach', 0))
    freq = float(d.get('frequency', 0))
    ctr = float(d.get('ctr', 0))
    cpc = float(d.get('cpc', 0))
    cpm = float(d.get('cpm', 0))
    clicks = int(d.get('clicks', 0))
    
    leads = link_clicks = lp_views = 0
    for act in d.get('actions', []):
        t = act.get('action_type', '')
        v = int(act.get('value', 0))
        if t in ('onsite_conversion.lead_grouped', 'lead', 'offsite_conversion.fb_pixel_lead', 'onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click':
            link_clicks = v
        elif t == 'landing_page_view':
            lp_views = v
    cpl = (spend / leads) if leads > 0 else 0
    return {
        'spend': spend, 'leads': leads, 'cpl': cpl,
        'imps': imps, 'reach': reach, 'freq': freq,
        'clicks': clicks, 'link_clicks': link_clicks, 'lp_views': lp_views,
        'ctr': ctr, 'cpc': cpc, 'cpm': cpm,
        'date_start': d.get('date_start'), 'date_stop': d.get('date_stop'),
    }

# Get campaign metadata (created_time, status, daily_budget)
def fetch_meta(cid):
    r = requests.get(f"{BASE}/{cid}", params={
        'fields': 'id,name,effective_status,daily_budget,lifetime_budget,created_time,start_time,bid_strategy',
        'access_token': TOKEN
    }, timeout=30)
    return r.json()

# Per-period: today, last_7d, total
totals = {'spend': 0, 'leads': 0, 'imps': 0, 'clicks': 0, 'link_clicks': 0, 'lp_views': 0}

for cid, label in CAMPS:
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    meta = fetch_meta(cid)
    print(f"  ID: {cid}")
    print(f"  Status: {meta.get('effective_status')}")
    print(f"  Inicio: {meta.get('start_time')}")
    db = int(meta.get('daily_budget') or 0)/100
    if db:
        print(f"  Orcamento campanha: R${db:.2f}/dia (CBO)")
    
    for preset, plabel in [('today','Hoje (parcial)'), ('last_7d','Ultimos 7 dias'), ('maximum','TOTAL DESDE INICIO')]:
        d = fetch(cid, label, preset)
        if not d: 
            print(f"\n  {plabel}: sem dados"); continue
        print(f"\n  --- {plabel} ({d['date_start']} -> {d['date_stop']}) ---")
        print(f"     Gasto:    R${d['spend']:>10,.2f}")
        print(f"     Leads:    {d['leads']:>12,}")
        print(f"     CPL:      R${d['cpl']:>10,.2f}")
        print(f"     Impres:   {d['imps']:>12,}")
        print(f"     Reach:    {d['reach']:>12,}")
        print(f"     Freq:     {d['freq']:>12.2f}")
        print(f"     Clicks:   {d['clicks']:>12,} | Link clicks: {d['link_clicks']:,} | LP views: {d['lp_views']:,}")
        print(f"     CTR:      {d['ctr']:>11.2f}% | CPC: R${d['cpc']:.2f} | CPM: R${d['cpm']:.2f}")
        if preset == 'maximum':
            totals['spend'] += d['spend']
            totals['leads'] += d['leads']
            totals['imps'] += d['imps']
            totals['clicks'] += d['clicks']
            totals['link_clicks'] += d['link_clicks']
            totals['lp_views'] += d['lp_views']

print(f"\n{'#'*70}")
print(f"  RESUMO TOTAL DEVSPACE — CAPTACAO ATIVA (desde inicio)")
print(f"{'#'*70}")
print(f"  Gasto total:        R${totals['spend']:,.2f}")
print(f"  Leads totais:       {totals['leads']:,}")
print(f"  CPL medio:          R${(totals['spend']/totals['leads']) if totals['leads'] else 0:.2f}")
print(f"  Impressoes:         {totals['imps']:,}")
print(f"  Clicks totais:      {totals['clicks']:,}")
print(f"  Link clicks:        {totals['link_clicks']:,}")
print(f"  LP views:           {totals['lp_views']:,}")
