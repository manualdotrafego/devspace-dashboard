import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMPS = ["120248546729160002", "120254908221730002"]

print("## THUMBSTART")
seen = set()
for cid in CAMPS:
    as_r = requests.get(f"{BASE}/{cid}/adsets", params={'fields':'id','limit':100,'access_token':TOKEN}, timeout=30)
    for ao in as_r.json().get('data', []):
        ads = requests.get(f"{BASE}/{ao['id']}/ads", params={
            'fields':'name,creative{thumbnail_url,image_url,effective_object_story_id}',
            'limit':100,'access_token':TOKEN
        }, timeout=30).json().get('data', [])
        for ad in ads:
            nm = ad.get('name','').strip()
            if nm in seen: continue
            cr = ad.get('creative',{})
            thumb = cr.get('thumbnail_url','') or cr.get('image_url','')
            eosi = cr.get('effective_object_story_id','')
            url = ""
            if eosi and '_' in eosi:
                pg,po = eosi.split('_',1); url=f"https://www.facebook.com/{pg}/posts/{po}"
            if thumb:
                seen.add(nm)
                print(f"##T|{nm}|{thumb}|{url}")
print("## THUMBEND")
