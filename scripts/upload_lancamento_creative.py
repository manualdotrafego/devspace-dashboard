import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMPS = ["120248546729160002", "120254908221730002"]

CICLOS = [
    (1,"26/03","01/04","2026-03-26","2026-04-01"),
    (2,"02/04","08/04","2026-04-02","2026-04-08"),
    (3,"09/04","15/04","2026-04-09","2026-04-15"),
    (4,"16/04","22/04","2026-04-16","2026-04-22"),
    (5,"23/04","29/04","2026-04-23","2026-04-29"),
    (6,"30/04","06/05","2026-04-30","2026-05-06"),
    (7,"07/05","13/05","2026-05-07","2026-05-13"),
    (8,"14/05","20/05","2026-05-14","2026-05-20"),
    (9,"21/05","27/05","2026-05-21","2026-05-27"),
    (10,"28/05","03/06","2026-05-28","2026-06-03"),
    (11,"04/06","10/06","2026-06-04","2026-06-10"),
    (12,"11/06","17/06","2026-06-11","2026-06-17"),
    (13,"18/06","23/06","2026-06-18","2026-06-23"),
    (14,"24/06","30/06","2026-06-24","2026-06-29"),
]

def get_metrics(actions):
    leads = lc = 0
    for act in actions or []:
        t = act.get('action_type',''); v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
    return leads, lc

print("## CSVSTART")
print("ciclo|periodo|ad_name|spend|impressions|clicks|link_clicks|leads|cpm|ctr|cpc_link|cpl")
for (cnum, d1, d2, since, until) in CICLOS:
    per = f"{d1} - {d2}"
    for cid in CAMPS:
        r = requests.get(f"{BASE}/{cid}/insights", params={
            'level':'ad',
            'fields':'ad_name,spend,impressions,clicks,actions,cpm,ctr',
            'time_range': json.dumps({'since':since,'until':until}),
            'limit':200,'access_token':TOKEN
        }, timeout=60).json()
        for d in r.get('data', []):
            sp = float(d.get('spend',0))
            if sp == 0: continue
            leads, lc = get_metrics(d.get('actions',[]))
            imps=int(d.get('impressions',0)); clicks=int(d.get('clicks',0))
            cpm=float(d.get('cpm',0)); ctr=float(d.get('ctr',0))
            cpc=sp/lc if lc else 0; cpl=sp/leads if leads else 0
            nm=d.get('ad_name','').replace('|','/').replace('\n',' ')
            cpl_s=f"{cpl:.2f}" if leads else "0"
            print(f"{cnum}|{per}|{nm}|{sp:.2f}|{imps}|{clicks}|{lc}|{leads}|{cpm:.2f}|{ctr:.2f}|{cpc:.2f}|{cpl_s}")
print("## CSVEND")
