import requests, os, json
from datetime import date

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMPS = ["120248546729160002", "120254908221730002", "120255355949960002"]
today = date.today()
since = "2026-07-08"
until = min(today.isoformat(), "2026-07-14")
n_days = (date.fromisoformat(until) - date.fromisoformat(since)).days + 1
partial = " (parcial)" if until < "2026-07-14" else ""
per = f"08/07 - 14/07{partial}"

def get_metrics(actions):
    leads = lc = 0
    for act in actions or []:
        t = act.get('action_type',''); v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
    return leads, lc

print(f"## HOJE: {today} | ciclo16: {since} -> {until} ({n_days} dias)")
print("## CSVSTART")
for cid in CAMPS:
    r = requests.get(f"{BASE}/{cid}/insights", params={
        'level':'ad','fields':'ad_name,spend,impressions,clicks,actions,cpm,ctr',
        'time_range': json.dumps({'since':since,'until':until}),
        'limit':200,'access_token':TOKEN}, timeout=60).json()
    for d in r.get('data', []):
        sp = float(d.get('spend',0))
        if sp == 0: continue
        leads, lc = get_metrics(d.get('actions',[]))
        imps=int(d.get('impressions',0)); clicks=int(d.get('clicks',0))
        cpm=float(d.get('cpm',0)); ctr=float(d.get('ctr',0))
        cpc=sp/lc if lc else 0; cpl=sp/leads if leads else 0
        nm=d.get('ad_name','').replace('|','/').replace('\n',' ')
        cpl_s=f"{cpl:.2f}" if leads else "0"
        print(f"16|{per}|{nm}|{sp:.2f}|{imps}|{clicks}|{lc}|{leads}|{cpm:.2f}|{ctr:.2f}|{cpc:.2f}|{cpl_s}")
print("## CSVEND")
