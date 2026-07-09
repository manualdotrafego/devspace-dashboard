import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
CID="120255355949960002"
print("## THUMBSTART")
# via /ads direto da campanha (nao por adset)
r=requests.get(f"{BASE}/{CID}/ads",params={
    'fields':'name,creative{thumbnail_url,image_url,effective_object_story_id},status',
    'limit':100,'access_token':TOKEN},timeout=40).json()
if 'error' in r: print("## ERR:", r['error'].get('message','')[:100])
seen=set()
for ad in r.get('data',[]):
    nm=ad.get('name','').strip()
    if nm in seen: continue
    cr=ad.get('creative',{})
    thumb=cr.get('thumbnail_url','') or cr.get('image_url','')
    eosi=cr.get('effective_object_story_id','')
    url=""
    if eosi and '_' in eosi:
        pg,po=eosi.split('_',1); url=f"https://www.facebook.com/{pg}/posts/{po}"
    seen.add(nm)
    print(f"##T|{nm}|{thumb}|{url}")
print("## THUMBEND")
