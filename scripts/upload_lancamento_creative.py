import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

# Get all adsets
r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

def find(pat):
    for a in adsets:
        if pat in a['name']:
            return a
    return None

# 1. Reduce [1.7] to €50/d
print("=== REDUZIR [1.7] SO VIDEO para €50/dia ===")
a = find('[AD SET 1.7]')
if a:
    cur = int(a.get('daily_budget') or 0)/100
    print(f"  Atual: €{cur:.2f}/d")
    pr = requests.post(f"{BASE}/{a['id']}", data={
        'daily_budget': '5000', 'access_token': TOKEN
    }, timeout=30).json()
    print(f"  POST -> {pr}")
    # verify
    v = requests.get(f"{BASE}/{a['id']}", params={
        'fields': 'daily_budget,effective_status', 'access_token': TOKEN
    }, timeout=30).json()
    print(f"  Novo: €{int(v.get('daily_budget',0))/100:.2f}/d | status: {v.get('effective_status')}")
else:
    print("  NAO encontrado")

# 2. Get 7-day performance for [1.17], [1.16], [1.14], [1.12]
today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()
print(f"\n=== PERFORMANCE 7 DIAS ({since} -> {until}) ===")

targets = ['[AD SET 1.17]', '[AD SET 1.16]', '[AD SET 1.14]', '[AD SET 1.12]']
for pat in targets:
    a = find(pat)
    if not a:
        print(f"\n  {pat}: NAO encontrado"); continue
    aid = a['id']
    db = int(a.get('daily_budget') or 0)/100
    print(f"\n>>> {a['name']}")
    print(f"    id: {aid} | budget: €{db:.2f}/d | status: {a.get('effective_status')}")
    
    # Aggregated insights
    ins_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields': 'spend,impressions,clicks,actions,cpc,cpm,ctr,reach,frequency',
        'time_range': json.dumps({'since': since, 'until': until}),
        'access_token': TOKEN
    }, timeout=30)
    ins = ins_r.json().get('data', [])
    if ins:
        d = ins[0]
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
            t = act.get('action_type','')
            v = int(act.get('value', 0))
            if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                leads = max(leads, v)
            elif t == 'link_click': link_clicks = v
            elif t == 'landing_page_view': lp_views = v
        cpl = spend/leads if leads > 0 else 0
        print(f"    Gasto:    €{spend:.2f}")
        print(f"    Leads:    {leads}")
        print(f"    CPL:      €{cpl:.2f}")
        print(f"    Imps:     {imps:,} | Reach: {reach:,} | Freq: {freq:.2f}")
        print(f"    Clicks:   {clicks:,} | LinkCk: {link_clicks:,} | LP: {lp_views:,}")
        print(f"    CTR:      {ctr:.2f}% | CPC €{cpc:.2f} | CPM €{cpm:.2f}")
        # CR LP->Lead
        lp_lead = (leads/lp_views*100) if lp_views > 0 else 0
        click_lp = (lp_views/link_clicks*100) if link_clicks > 0 else 0
        print(f"    Click>LP: {click_lp:.1f}%  | LP>Lead: {lp_lead:.1f}%")
    else:
        print(f"    sem dados no periodo")

    # Day-by-day
    di_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields': 'spend,actions',
        'time_range': json.dumps({'since': since, 'until': until}),
        'time_increment': 1,
        'access_token': TOKEN
    }, timeout=30)
    days = di_r.json().get('data', [])
    if days:
        print(f"    Por dia:")
        for d in days:
            sp = float(d.get('spend', 0))
            lds = 0
            for act in d.get('actions', []):
                if act.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                    lds = max(lds, int(act.get('value', 0)))
            cpl = sp/lds if lds else 0
            print(f"      {d.get('date_start')}  €{sp:>5.2f} / {lds:>2} leads / CPL €{cpl:.2f}" if lds else f"      {d.get('date_start')}  €{sp:>5.2f} / 0 leads")
