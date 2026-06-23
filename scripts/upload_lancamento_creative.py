import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()

# 1. Get all ads with their post IDs
print(f"## PERIODO: {since} -> {until}")
print("## STARTING COMMENT FETCH")

as_r = requests.get(f"{BASE}/{CAMP}/adsets", params={
    'fields':'id,name','limit':100,'access_token':TOKEN
}, timeout=30)
adsets = as_r.json().get('data', [])

# Get unique post_ids with ad metadata
posts = {}  # post_id -> [{ad_name, adset_name, leads, spend}]
for ads_obj in adsets:
    asid = ads_obj['id']; asname = ads_obj['name']
    ads_r = requests.get(f"{BASE}/{asid}/ads", params={
        'fields':'id,name,creative{effective_object_story_id}',
        'limit':100,'access_token':TOKEN
    }, timeout=30)
    for ad in ads_r.json().get('data', []):
        eosi = ad.get('creative', {}).get('effective_object_story_id', '')
        if not eosi: continue
        # Get leads from insights
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
            posts[eosi] = {'ad_names':[], 'adset_names':[], 'spend':sp, 'leads':lds}
        posts[eosi]['ad_names'].append(ad['name'])
        posts[eosi]['adset_names'].append(asname)

print(f"## POSTS_FOUND: {len(posts)}")

# 2. For each post, fetch ALL comments (paginated)
all_data = []
PAGE_ID = "110278364765662"

for eosi, meta in posts.items():
    page_id, post_id = eosi.split('_', 1)
    print(f"\n## POST: {eosi} | {meta['leads']} leads | gasto EUR{meta['spend']:.2f}")
    print(f"## AD_NAMES: {','.join(meta['ad_names'][:3])}")
    
    # Fetch comments
    url = f"{BASE}/{eosi}/comments"
    params = {
        'fields':'id,message,created_time,like_count,from,comment_count,is_hidden',
        'order':'reverse_chronological',
        'limit':100,
        'filter':'stream',
        'access_token':TOKEN
    }
    
    total_comments = 0
    while url:
        try:
            r = requests.get(url, params=params, timeout=30)
            data = r.json()
            if 'error' in data:
                print(f"##  ERROR: {data['error'].get('message','')[:80]}")
                break
            comments = data.get('data', [])
            for c in comments:
                msg = c.get('message','').replace('\n',' ').replace('\r','').replace('|','/')
                from_name = c.get('from',{}).get('name','?').replace('|','/')
                created = c.get('created_time','')
                likes = c.get('like_count',0)
                replies = c.get('comment_count',0)
                hidden = c.get('is_hidden', False)
                print(f"##C|{eosi}|{from_name}|{created}|{likes}|{replies}|{hidden}|{msg[:300]}")
                total_comments += 1
            
            url = data.get('paging',{}).get('next','')
            params = {}  # next URL has params baked in
        except Exception as e:
            print(f"##  EXCEPTION: {e}")
            break
    print(f"##  total_comments={total_comments}")
