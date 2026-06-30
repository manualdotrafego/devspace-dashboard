import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMPS = ["120248546729160002", "120254908221730002"]  # antiga + nova CBO
since = "2026-06-23"; until = "2026-06-29"

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
    # get all adsets -> ads
    as_r = requests.get(f"{BASE}/{cid}/adsets", params={'fields':'id','limit':100,'access_token':TOKEN}, timeout=30)
    for ads_obj in as_r.json().get('data', []):
        ads_r = requests.get(f"{BASE}/{ads_obj['id']}/ads", params={
            'fields':'id,name,creative{effective_object_story_id}','limit':100,'access_token':TOKEN
        }, timeout=30)
        for ad in ads_r.json().get('data', []):
            ins = requests.get(f"{BASE}/{ad['id']}/insights", params={
                'fields':'spend,impressions,clicks,actions,cpm,ctr',
                'time_range': json.dumps({'since':since,'until':until}),
                'access_token':TOKEN
            }, timeout=30).json().get('data', [])
            if not ins: continue
            d = ins[0]; sp = float(d.get('spend',0))
            if sp == 0: continue
            leads, lc = get_metrics(d.get('actions',[]))
            imps = int(d.get('impressions',0)); clicks = int(d.get('clicks',0))
            cpm = float(d.get('cpm',0)); ctr = float(d.get('ctr',0))
            cpc_link = sp/lc if lc else 0
            cpl = sp/leads if leads else 0
            # post url
            eosi = ad.get('creative',{}).get('effective_object_story_id','')
            url = ""
            if eosi and '_' in eosi:
                pg, po = eosi.split('_',1)
                url = f"https://www.facebook.com/{pg}/posts/{po}"
            nm = ad['name'].replace('|','/').replace('\n',' ')
            cn = cname.replace('|','/')
            cpl_s = f"{cpl:.2f}" if leads else "0"
            print(f"{nm}|{cn}|{sp:.2f}|{imps}|{clicks}|{lc}|{leads}|{cpm:.2f}|{ctr:.2f}|{cpc_link:.2f}|{cpl_s}|{url}")
print("## CSVEND")
