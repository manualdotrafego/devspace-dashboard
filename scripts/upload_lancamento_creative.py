import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

r = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend,impressions,clicks,reach,actions,ctr,cpc,cpm',
    'time_range': json.dumps({'since':'2026-06-17','until':'2026-06-23'}),
    'access_token':TOKEN
}, timeout=30)
data = r.json().get('data', [])
d = data[0] if data else {}

spend = float(d.get('spend',0))
imps = int(d.get('impressions',0))
clicks = int(d.get('clicks',0))
reach = int(d.get('reach',0))
ctr = float(d.get('ctr',0))
cpc_all = float(d.get('cpc',0))
cpm = float(d.get('cpm',0))

leads = lc = 0
for act in d.get('actions',[]):
    t = act.get('action_type','')
    v = int(act.get('value',0))
    if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
        leads = max(leads, v)
    elif t == 'link_click': lc = v

cpc_link = spend/lc if lc > 0 else 0
cvr = (leads/lc*100) if lc > 0 else 0
cpl = spend/leads if leads > 0 else 0

print("## REALDATA")
print(f"spend={spend:.2f}")
print(f"impressions={imps}")
print(f"clicks={clicks}")
print(f"link_clicks={lc}")
print(f"reach={reach}")
print(f"leads={leads}")
print(f"cpm={cpm:.2f}")
print(f"cpc_all={cpc_all:.2f}")
print(f"cpc_link={cpc_link:.2f}")
print(f"ctr={ctr:.2f}")
print(f"cvr={cvr:.2f}")
print(f"cpl={cpl:.2f}")
print("## END")
