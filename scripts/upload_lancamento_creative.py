import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP_ID = "120247963737730581"  # VALIDACAO CRIATIVO

# 1. Find [AD SET 1.21] in the campaign
print("=== Buscando [AD SET 1.21] ===")
r = requests.get(f"{BASE}/{CAMP_ID}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget,created_time,start_time',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])
target = None
for a in adsets:
    if '1.21' in a['name']:
        target = a
        break

if not target:
    print("ERRO: nao achei [AD SET 1.21]"); exit(1)

print(f"Conjunto: {target['name']}")
print(f"ID: {target['id']}")
print(f"Status: {target['effective_status']} | Daily: R${int(target.get('daily_budget',0))/100:.2f}")
print(f"Created: {target.get('created_time')}")
print(f"Start: {target.get('start_time')}")

AS_ID = target['id']

def fetch_insights(since, until, label):
    print(f"\n=== {label} ({since} -> {until}) ===")
    ins_r = requests.get(f"{BASE}/{AS_ID}/insights", params={
        'fields': 'spend,impressions,clicks,actions,cpc,cpm,ctr,reach,frequency',
        'time_range': json.dumps({'since': since, 'until': until}),
        'access_token': TOKEN
    }, timeout=30)
    data = ins_r.json().get('data', [])
    if not data:
        print("  sem dados"); return None
    d = data[0]
    spend = float(d.get('spend', 0))
    imps = int(d.get('impressions', 0))
    clicks = int(d.get('clicks', 0))
    reach = int(d.get('reach', 0))
    freq = float(d.get('frequency', 0))
    ctr = float(d.get('ctr', 0))
    cpc = float(d.get('cpc', 0))
    cpm = float(d.get('cpm', 0))
    
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
    print(f"  Gasto:  R${spend:.2f}")
    print(f"  Leads:  {leads}")
    print(f"  CPL:    R${cpl:.2f}")
    print(f"  Impres: {imps:,} | Reach: {reach:,} | Freq: {freq:.2f}")
    print(f"  Clicks: {clicks:,} | Link clicks: {link_clicks:,} | LP views: {lp_views:,}")
    print(f"  CTR:    {ctr:.2f}% | CPC: R${cpc:.2f} | CPM: R${cpm:.2f}")
    return {'spend': spend, 'leads': leads, 'cpl': cpl}

# Periods
today = date.today()
y7 = (today - timedelta(days=7)).isoformat()
y3 = (today - timedelta(days=3)).isoformat()
y1 = (today - timedelta(days=1)).isoformat()

fetch_insights(today.isoformat(), today.isoformat(), "HOJE")
fetch_insights(y1, today.isoformat(), "ULTIMOS 2 DIAS")
fetch_insights(y3, today.isoformat(), "ULTIMOS 4 DIAS")
fetch_insights(y7, today.isoformat(), "ULTIMOS 7 DIAS")

# Per day breakdown last 7 days
print(f"\n=== POR DIA — ULTIMOS 7 DIAS ===")
ins_r = requests.get(f"{BASE}/{AS_ID}/insights", params={
    'fields': 'spend,impressions,clicks,actions',
    'time_range': json.dumps({'since': y7, 'until': today.isoformat()}),
    'time_increment': 1,
    'access_token': TOKEN
}, timeout=30)
days = ins_r.json().get('data', [])
print(f"{'Data':<12} {'Gasto':>10} {'Leads':>7} {'CPL':>9}")
for d in days:
    sp = float(d.get('spend', 0))
    lds = 0
    for act in d.get('actions', []):
        if act.get('action_type') in ('onsite_conversion.lead_grouped', 'lead', 'offsite_conversion.fb_pixel_lead', 'onsite_web_lead'):
            lds = max(lds, int(act.get('value', 0)))
    cpl = sp/lds if lds > 0 else 0
    print(f"{d.get('date_start')}   R${sp:>7.2f}  {lds:>5}   R${cpl:>5.2f}")

# Active ads in this adset
print(f"\n=== ANUNCIOS ATIVOS no [AD SET 1.21] ===")
ads_r = requests.get(f"{BASE}/{AS_ID}/ads", params={
    'fields': 'id,name,effective_status',
    'limit': 50, 'access_token': TOKEN
}, timeout=30)
for ad in ads_r.json().get('data', []):
    print(f"  [{ad['effective_status']}] {ad['name'][:60]} | {ad['id']}")
