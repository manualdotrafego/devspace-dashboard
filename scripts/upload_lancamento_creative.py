import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()

def get_leads(actions):
    leads = lc = lpv = 0
    for act in actions or []:
        t = act.get('action_type','')
        v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
        elif t == 'landing_page_view': lpv = v
    return leads, lc, lpv

print(f"## PERIODO: {since} -> {until}")
print("## CSVSTART")
print("ad_id|ad_name|adset_name|status|spend|impressions|link_clicks|leads|cpl|ctr|cpc|post_url")

as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name','limit':100,'access_token':TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])

for ads_obj in adsets:
    asid = ads_obj['id']
    asname = ads_obj['name']
    ads_r = requests.get(f"{BASE}/{asid}/ads", params={
        'fields':'id,name,status,effective_status,creative{id,effective_object_story_id,object_story_id,instagram_permalink_url,object_type}',
        'limit':100,'access_token':TOKEN
    }, timeout=30)
    ads = ads_r.json().get('data', [])
    
    for ad in ads:
        aid = ad['id']
        ins_r = requests.get(f"{BASE}/{aid}/insights", params={
            'fields':'spend,impressions,actions,ctr,cpc',
            'time_range': json.dumps({'since':since,'until':until}),
            'access_token':TOKEN
        }, timeout=30)
        ins = ins_r.json().get('data', [])
        if not ins: continue
        d = ins[0]
        sp = float(d.get('spend',0))
        if sp == 0: continue
        leads, lc, lpv = get_leads(d.get('actions',[]))
        cpl = sp/leads if leads > 0 else 0
        imps = int(d.get('impressions',0))
        ctr = float(d.get('ctr',0))
        cpc = float(d.get('cpc',0))
        
        # Build post URL (Facebook public post with comments)
        post_url = ""
        cr = ad.get('creative', {})
        eosi = cr.get('effective_object_story_id') or cr.get('object_story_id', '')
        ig_url = cr.get('instagram_permalink_url', '')
        
        if eosi and '_' in eosi:
            page_id, post_id = eosi.split('_', 1)
            post_url = f"https://www.facebook.com/{page_id}/posts/{post_id}"
        elif ig_url:
            post_url = ig_url
        
        # Fallback: also include IG link if exists in addition
        if not post_url and ig_url:
            post_url = ig_url
        
        clean = lambda s: str(s).replace('|','/').replace('\n',' ').replace('\r','')
        cpl_s = f"{cpl:.2f}" if leads > 0 else "0"
        print(f"{aid}|{clean(ad['name'])}|{clean(asname)}|{ad.get('effective_status','')}|"
              f"{sp:.2f}|{imps}|{lc}|{leads}|{cpl_s}|{ctr:.2f}|{cpc:.2f}|{post_url}")

print("## CSVEND")
