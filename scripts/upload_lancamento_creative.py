import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name,daily_budget,effective_status,created_time',
    'limit':100,'access_token':TOKEN
}, timeout=30)
adsets = r.json().get('data', [])

targets = ['[AD SET 1.7', '[AD SET 1.4]']  # match 1.7 alt and 1.4 (use [ to avoid 1.10,1.17 etc)
today = date.today()
since = (today - timedelta(days=14)).isoformat()
until = today.isoformat()

for pat in targets:
    a = next((x for x in adsets if x['name'].startswith(pat)), None)
    if not a:
        print(f"NAO ACHEI: {pat}"); continue
    aid = a['id']
    db = int(a.get('daily_budget') or 0)/100
    print(f"\n=== {a['name']} ===")
    print(f"  id={aid} | budget atual: €{db:.2f}/d | criado: {a.get('created_time')}")
    
    # Daily breakdown
    ins_r = requests.get(f"{BASE}/{aid}/insights", params={
        'fields':'spend,impressions,actions',
        'time_range': json.dumps({'since':since,'until':until}),
        'time_increment': 1,
        'access_token':TOKEN
    }, timeout=30)
    days = ins_r.json().get('data', [])
    if not days:
        print(f"  sem dados nos ultimos 14 dias"); continue
    
    print(f"\n  Data         Gasto    Leads   CPL")
    print(f"  ----------   ------   -----   -----")
    total_sp = 0; total_lds = 0
    for d in days:
        sp = float(d.get('spend',0))
        lds = 0
        for act in d.get('actions',[]):
            if act.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                lds = max(lds, int(act.get('value',0)))
        cpl_s = f"€{sp/lds:.2f}" if lds > 0 else "—"
        print(f"  {d.get('date_start')}   €{sp:>5.2f}   {lds:>5}   {cpl_s}")
        total_sp += sp; total_lds += lds
    print(f"  ----------   ------   -----   -----")
    cpl_t = f"€{total_sp/total_lds:.2f}" if total_lds > 0 else "—"
    print(f"  TOTAL        €{total_sp:>5.2f}   {total_lds:>5}   {cpl_t}")
