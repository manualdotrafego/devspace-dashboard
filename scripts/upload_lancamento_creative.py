import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

# Start: 26/mar/2026
start = date(2026, 3, 26)
today = date.today()

def get_metrics(actions, action_values=None):
    leads = lc = 0
    for act in actions or []:
        t = act.get('action_type','')
        v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
    return leads, lc

print("## CSVSTART")
print("cycle|since|until|days|spend|impressions|reach|clicks|link_clicks|leads|cpm|cpc_all|cpc_link|ctr|cvr_link_to_lead|cpl")

# Generate 7-day cycles
cur = start
i = 0
while cur <= today:
    i += 1
    end = min(cur + timedelta(days=6), today)
    n_days = (end - cur).days + 1
    
    r = requests.get(f"{BASE}/{CAMP}/insights", params={
        'fields':'spend,impressions,clicks,reach,actions,ctr,cpc,cpm',
        'time_range': json.dumps({'since': cur.isoformat(), 'until': end.isoformat()}),
        'access_token':TOKEN
    }, timeout=30)
    data = r.json().get('data', [])
    if not data:
        print(f"{i}|{cur}|{end}|{n_days}|0|0|0|0|0|0|0|0|0|0|0|0")
    else:
        d = data[0]
        spend = float(d.get('spend', 0))
        imps = int(d.get('impressions', 0))
        reach = int(d.get('reach', 0))
        clicks = int(d.get('clicks', 0))
        ctr = float(d.get('ctr', 0))
        cpc_all = float(d.get('cpc', 0))
        cpm = float(d.get('cpm', 0))
        leads, lc = get_metrics(d.get('actions', []))
        cpc_link = spend/lc if lc > 0 else 0
        cvr = (leads/lc*100) if lc > 0 else 0
        cpl = spend/leads if leads > 0 else 0
        print(f"{i}|{cur}|{end}|{n_days}|{spend:.2f}|{imps}|{reach}|{clicks}|{lc}|{leads}|"
              f"{cpm:.2f}|{cpc_all:.2f}|{cpc_link:.2f}|{ctr:.2f}|{cvr:.2f}|{cpl:.2f}")
    
    cur = end + timedelta(days=1)

print("## CSVEND")
