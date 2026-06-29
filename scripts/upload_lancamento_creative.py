import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

since = "2026-06-24"
until = "2026-06-29"

r = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend,impressions,clicks,reach,actions,ctr,cpc,cpm',
    'time_range': json.dumps({'since':since,'until':until}),
    'access_token':TOKEN
}, timeout=30)
data = r.json().get('data', [])
d = data[0] if data else {}

spend = float(d.get('spend',0))
imps = int(d.get('impressions',0))
clicks = int(d.get('clicks',0))
ctr = float(d.get('ctr',0))
cpm = float(d.get('cpm',0))

leads = lc = lpv = 0
for act in d.get('actions',[]):
    t = act.get('action_type','')
    v = int(act.get('value',0))
    if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
        leads = max(leads, v)
    elif t == 'link_click': lc = v
    elif t == 'landing_page_view': lpv = v

cpc_link = spend/lc if lc > 0 else 0
cvr = (leads/lc*100) if lc > 0 else 0
cpl = spend/leads if leads > 0 else 0

print(f"## CICLO 14 (parcial): {since} -> {until} (6 de 7 dias)")
print(f"VALOR_USADO={spend:.2f}")
print(f"IMPRESSOES={imps}")
print(f"CLIQUES={clicks}")
print(f"CPM={cpm:.2f}")
print(f"CTR={ctr:.2f}")
print(f"CPC_LINK={cpc_link:.2f}")
print(f"LINK_CLICKS={lc}")
print(f"LP_VIEWS={lpv}")
print(f"LEADS={leads}")
print(f"PCT_CONV={cvr:.2f}")
print(f"CPL={cpl:.2f}")
