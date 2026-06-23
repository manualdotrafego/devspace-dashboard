import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()

pg_r = requests.get(f"{BASE}/110278364765662", params={
    'access_token':TOKEN, 'fields':'access_token'
}, timeout=30).json()
PAGE_TOKEN = pg_r.get('access_token')

# Get all ads with post_ids
as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name','limit':100,'access_token':TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])

posts = {}
for ads_obj in adsets:
    asid = ads_obj['id']; asname = ads_obj['name']
    ads_r = requests.get(f"{BASE}/{asid}/ads", params={
        'fields':'id,name,creative{effective_object_story_id}',
        'limit':100,'access_token':TOKEN
    }, timeout=30)
    for ad in ads_r.json().get('data', []):
        eosi = ad.get('creative', {}).get('effective_object_story_id', '')
        if not eosi: continue
        ins_r = requests.get(f"{BASE}/{ad['id']}/insights", params={
            'fields':'spend,actions',
            'time_range': json.dumps({'since':since,'until':until}),
            'access_token':TOKEN
        }, timeout=30)
        ins = ins_r.json().get('data', [])
        if not ins: continue
        d = ins[0]; sp = float(d.get('spend',0))
        if sp == 0: continue
        lds = 0
        for act in d.get('actions',[]):
            if act.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                lds = max(lds, int(act.get('value',0)))
        if eosi not in posts:
            posts[eosi] = {'ad_name':ad['name'], 'adset':asname, 'leads':lds, 'spend':sp}

print("## CSVSTART")
print("post_id|ad_name|adset|leads|spend|comments|likes|shares|reach|reactions_love|reactions_haha|reactions_wow|reactions_sorry|reactions_anger|post_url")

# Get engagement counts using summary=true (works with pages_read_engagement)
for eosi, m in posts.items():
    # Comments summary
    cr = requests.get(f"{BASE}/{eosi}/comments", params={
        'summary':'true','filter':'stream','limit':0,'access_token':PAGE_TOKEN
    }, timeout=20).json()
    comments_count = cr.get('summary',{}).get('total_count', 0)
    
    # Likes/reactions
    lr = requests.get(f"{BASE}/{eosi}/reactions", params={
        'summary':'true','limit':0,'access_token':PAGE_TOKEN
    }, timeout=20).json()
    likes_count = lr.get('summary',{}).get('total_count', 0)
    
    # Reactions by type
    reactions = {}
    for rt in ['LOVE','HAHA','WOW','SORRY','ANGER']:
        rr = requests.get(f"{BASE}/{eosi}/reactions", params={
            'summary':'true','type':rt,'limit':0,'access_token':PAGE_TOKEN
        }, timeout=15).json()
        reactions[rt] = rr.get('summary',{}).get('total_count', 0)
    
    # Try shares (via insights or direct)
    shares = 0
    try:
        pr = requests.get(f"{BASE}/{eosi}", params={
            'fields':'shares,full_picture','access_token':PAGE_TOKEN
        }, timeout=20).json()
        shares = pr.get('shares',{}).get('count', 0)
    except: pass
    
    page_id, post_id = eosi.split('_', 1)
    url = f"https://www.facebook.com/{page_id}/posts/{post_id}"
    clean = lambda s: str(s).replace('|','/').replace('\n',' ')
    print(f"{eosi}|{clean(m['ad_name'])}|{clean(m['adset'])}|{m['leads']}|{m['spend']:.2f}|"
          f"{comments_count}|{likes_count}|{shares}|0|"
          f"{reactions.get('LOVE',0)}|{reactions.get('HAHA',0)}|{reactions.get('WOW',0)}|"
          f"{reactions.get('SORRY',0)}|{reactions.get('ANGER',0)}|{url}")

print("## CSVEND")
