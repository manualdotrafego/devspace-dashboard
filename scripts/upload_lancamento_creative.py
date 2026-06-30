import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMPS = ["120248546729160002", "120254908221730002"]  # antiga + nova CBO
since = "2026-01-01"; until = "2026-06-29"

def get_metrics(actions):
    leads = lc = 0
    for act in actions or []:
        t = act.get('action_type',''); v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
    return leads, lc

print("## CSVSTART")
print("ad_name|campaign|spend|impressions|clicks|link_clicks|leads|cpm|ctr|cpc_link|cpl|post_url")

for cid in CAMPS:
    cinfo = requests.get(f"{BASE}/{cid}", params={'fields':'name','access_token':TOKEN}, timeout=30).json()
    cname = cinfo.get('name','')
    # use ad-level insights directly with breakdown to capture ALL ads that ran this year
    # paginate through ads via insights endpoint at ad level
    url = f"{BASE}/{cid}/insights"
    params = {
        'level':'ad',
        'fields':'ad_id,ad_name,spend,impressions,clicks,actions,cpm,ctr',
        'time_range': json.dumps({'since':since,'until':until}),
        'limit':200,
        'access_token':TOKEN
    }
    while url:
        r = requests.get(url, params=params, timeout=60).json()
        if 'error' in r:
            print(f"## ERROR {cid}: {r['error'].get('message','')[:80]}"); break
        for d in r.get('data', []):
            sp = float(d.get('spend',0))
            if sp == 0: continue
            leads, lc = get_metrics(d.get('actions',[]))
            imps = int(d.get('impressions',0)); clicks = int(d.get('clicks',0))
            cpm = float(d.get('cpm',0)); ctr = float(d.get('ctr',0))
            cpc_link = sp/lc if lc else 0
            cpl = sp/leads if leads else 0
            # get post url from ad creative
            aid = d.get('ad_id')
            url2 = ""
            try:
                cr = requests.get(f"{BASE}/{aid}", params={'fields':'creative{effective_object_story_id}','access_token':TOKEN}, timeout=20).json()
                eosi = cr.get('creative',{}).get('effective_object_story_id','')
                if eosi and '_' in eosi:
                    pg, po = eosi.split('_',1); url2 = f"https://www.facebook.com/{pg}/posts/{po}"
            except: pass
            nm = d.get('ad_name','').replace('|','/').replace('\n',' ')
            cn = cname.replace('|','/')
            cpl_s = f"{cpl:.2f}" if leads else "0"
            print(f"{nm}|{cn}|{sp:.2f}|{imps}|{clicks}|{lc}|{leads}|{cpm:.2f}|{ctr:.2f}|{cpc_link:.2f}|{cpl_s}|{url2}")
        url = r.get('paging',{}).get('next','')
        params = {}
print("## CSVEND")
