import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP_ID = "120248610894960581"  # QUENTE CBO

def insights(since, until, label):
    r = requests.get(f"{BASE}/{CAMP_ID}/insights", params={
        'fields': 'spend,impressions,clicks,actions,cpc,cpm,ctr,reach,frequency',
        'time_range': json.dumps({'since': since, 'until': until}),
        'access_token': TOKEN
    }, timeout=30)
    data = r.json().get('data', [])
    if not data: 
        print(f"\n--- {label}: sem dados"); return None
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
    cpl = spend/leads if leads > 0 else 0
    print(f"\n--- {label} ({since} -> {until}) ---")
    print(f"  Gasto:  R${spend:>8.2f}")
    print(f"  Leads:  {leads:>10}")
    print(f"  CPL:    R${cpl:>8.2f}")
    print(f"  Imps:   {imps:>10,} | Reach: {reach:,} | Freq: {freq:.2f}")
    print(f"  Clicks: {clicks:>10,} | LinkCk: {link_clicks:,} | LP: {lp_views:,}")
    print(f"  CTR:    {ctr:>8.2f}% | CPC R${cpc:.2f} | CPM R${cpm:.2f}")
    return {'spend': spend, 'leads': leads, 'cpl': cpl}

today = date.today()
print(f"=== CAMPANHA QUENTE [CBO] — {CAMP_ID} ===")
print(f"Data referencia: {today}")
print(f"Orcamento atual: R$220/dia (aumentado de R$140 em 11/mai)")

# Periods
insights(today.isoformat(),                       today.isoformat(),       "HOJE (13/05, parcial)")
insights((today - timedelta(days=1)).isoformat(), (today - timedelta(days=1)).isoformat(), "ONTEM (12/05) — 1o dia full c/ R$220")
insights((today - timedelta(days=2)).isoformat(), (today - timedelta(days=2)).isoformat(), "11/05 (dia do aumento, parcial novo budget)")
insights((today - timedelta(days=3)).isoformat(), (today - timedelta(days=3)).isoformat(), "10/05 (R$140/dia)")
insights((today - timedelta(days=4)).isoformat(), (today - timedelta(days=4)).isoformat(), "09/05 (R$140/dia)")
insights((today - timedelta(days=5)).isoformat(), (today - timedelta(days=5)).isoformat(), "08/05 (R$140/dia)")
insights((today - timedelta(days=2)).isoformat(), today.isoformat(),       "POS-AUMENTO (11-13)")
insights((today - timedelta(days=5)).isoformat(), (today - timedelta(days=3)).isoformat(), "PRE-AUMENTO (08-10)")

# Lifetime
r = requests.get(f"{BASE}/{CAMP_ID}/insights", params={
    'fields': 'spend,impressions,actions,date_start,date_stop',
    'date_preset': 'maximum',
    'access_token': TOKEN
}, timeout=30)
d = r.json().get('data', [{}])[0]
leads = 0
for act in d.get('actions', []):
    if act.get('action_type') in ('onsite_conversion.lead_grouped', 'lead', 'offsite_conversion.fb_pixel_lead', 'onsite_web_lead'):
        leads = max(leads, int(act.get('value', 0)))
spend = float(d.get('spend', 0))
print(f"\n=== LIFETIME ({d.get('date_start')} -> {d.get('date_stop')}) ===")
print(f"  Gasto total: R${spend:.2f} | Leads: {leads} | CPL R${spend/leads if leads else 0:.2f}")

# Adsets ativos
print(f"\n=== CONJUNTOS ATIVOS NO QUENTE ===")
as_r = requests.get(f"{BASE}/{CAMP_ID}/adsets", params={
    'fields': 'id,name,effective_status',
    'limit': 50, 'access_token': TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])
for a in adsets:
    if a.get('effective_status') == 'ACTIVE':
        # get insights last 3 days for each
        ai_r = requests.get(f"{BASE}/{a['id']}/insights", params={
            'fields': 'spend,actions',
            'time_range': json.dumps({'since': (today - timedelta(days=2)).isoformat(), 'until': today.isoformat()}),
            'access_token': TOKEN
        }, timeout=30)
        ai_data = ai_r.json().get('data', [{}])
        if ai_data:
            ai = ai_data[0]
            sp = float(ai.get('spend', 0))
            lds = 0
            for act in ai.get('actions', []):
                if act.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                    lds = max(lds, int(act.get('value', 0)))
            cpl = sp/lds if lds else 0
            print(f"  {a['name'][:60]}")
            print(f"     ult 3d: R${sp:.2f} / {lds} leads / CPL R${cpl:.2f}")
