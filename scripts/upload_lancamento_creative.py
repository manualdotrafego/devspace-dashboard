import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

today = date.today()
since = (today - timedelta(days=7)).isoformat()
until = today.isoformat()

# 1. Get Page Access Token for Joao Mafra (110278364765662)
pg_r = requests.get(f"{BASE}/110278364765662", params={
    'access_token':TOKEN, 'fields':'access_token'
}, timeout=30).json()
PAGE_TOKEN = pg_r.get('access_token')
print(f"## PAGE_TOKEN: {'OK' if PAGE_TOKEN else 'MISSING'}")
if not PAGE_TOKEN:
    print(f"## ERROR: {pg_r}"); exit(1)

# 2. Get all ads with post_ids from WEBNAR campaign
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
            posts[eosi] = {'ad_names':[], 'leads':lds, 'spend':sp}
        posts[eosi]['ad_names'].append(ad['name'])

print(f"## POSTS_FOUND: {len(posts)}")
print(f"## PERIODO: {since} -> {until}")

# 3. Fetch comments for each post using PAGE TOKEN
total_comments = 0
for eosi, meta in posts.items():
    print(f"\n## POST: {eosi}")
    print(f"## META: ads={meta['ad_names'][:2]} | leads={meta['leads']} | spend={meta['spend']:.2f}")
    
    url = f"{BASE}/{eosi}/comments"
    params = {
        'fields':'id,message,created_time,like_count,from{id,name},comment_count,is_hidden,is_private',
        'order':'reverse_chronological',
        'limit':100,
        'filter':'stream',
        'access_token':PAGE_TOKEN
    }
    
    post_total = 0
    page_count = 0
    while url and page_count < 20:
        try:
            r = requests.get(url, params=params, timeout=30)
            data = r.json()
            if 'error' in data:
                print(f"##  ERROR: {data['error'].get('message','')[:120]}")
                break
            comments = data.get('data', [])
            for c in comments:
                msg = c.get('message','').replace('\n',' ').replace('\r','').replace('|','/')
                from_name = c.get('from',{}).get('name','Anonymous').replace('|','/')
                created = c.get('created_time','')
                likes = c.get('like_count',0)
                replies = c.get('comment_count',0)
                hidden = c.get('is_hidden', False)
                priv = c.get('is_private', False)
                print(f"##C|{eosi}|{from_name}|{created}|{likes}|{replies}|{hidden}|{priv}|{msg[:400]}")
                post_total += 1
            url = data.get('paging',{}).get('next','')
            params = {}
            page_count += 1
        except Exception as e:
            print(f"##  EXCEPTION: {e}")
            break
    print(f"##  comments_total={post_total}")
    total_comments += post_total

print(f"\n## GRAND_TOTAL: {total_comments} comentarios")
