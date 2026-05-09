import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"
WEBNAR_CAMP = "120248546729160002"
NEW_ADSET_ID = "120251175301650002"  # already created

VIDEO_IDS = {
    "IMG_5319": "1386873113201033",
    "IMG_5320": "836070529048703",
    "IMG_5321": "827389087091531",
    "IMG_5322": "1371159888237890",
    "IMG_5325": "2343313536159134",
    "IMG_5326": "2057045791912745",
}

# Get source adset creative for page_id, link, image_hash
r = requests.get(f"{BASE}/{WEBNAR_CAMP}/adsets", params={
    'fields': 'id,name,effective_status,daily_budget',
    'limit': 50, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])
active = [a for a in adsets if a.get('effective_status') == 'ACTIVE']
if not active:
    active = adsets
active.sort(key=lambda x: int(x.get('daily_budget') or 999999))
source = active[0]
print(f"Fonte: {source['name']} ({source['id']})")

ads_r = requests.get(f"{BASE}/{source['id']}/ads", params={
    'fields': 'id,creative', 'limit': 10, 'access_token': TOKEN
}, timeout=30)
existing_ads = ads_r.json().get('data', [])

page_id = "110278364765662"
cta_type = "SEE_DETAILS"
link_url = "https://go.joaomafra.pt/"
message = "Sua chance de mudar tudo está aqui!\nO que você vai fazer com ela?"
image_hash = None

if existing_ads:
    cr_id = existing_ads[0].get('creative', {}).get('id')
    if cr_id:
        cr_r = requests.get(f"{BASE}/{cr_id}", params={
            'fields': 'object_story_spec',
            'access_token': TOKEN
        }, timeout=30)
        oss = cr_r.json().get('object_story_spec', {})
        vd = oss.get('video_data', {})
        page_id = oss.get('page_id', page_id)
        link_url = vd.get('call_to_action', {}).get('value', {}).get('link', link_url)
        cta_type = vd.get('call_to_action', {}).get('type', cta_type)
        message = vd.get('message', message)
        image_hash = vd.get('image_hash')  # <-- reuse thumbnail from source
        print(f"page_id={page_id}, link={link_url}, cta={cta_type}, image_hash={image_hash}")
        # instagram_user_id intentionally OMITTED to avoid dev-mode app error

# Create 6 ads
print(f"\n=== Criando 6 anuncios no adset {NEW_ADSET_ID} ===")
created = []
for name, video_id in VIDEO_IDS.items():
    print(f"\n  [{name}] video_id={video_id}")

    vdata = {
        'video_id': video_id,
        'message': message,
        'call_to_action': {
            'type': cta_type,
            'value': {'link': link_url}
        }
    }
    if image_hash:
        vdata['image_hash'] = image_hash
        print(f"  Using image_hash={image_hash}")

    story_spec = {
        'page_id': page_id,
        'video_data': vdata
        # NO instagram_user_id
    }

    cr_r = requests.post(f"{BASE}/{ACCT}/adcreatives", data={
        'access_token': TOKEN,
        'name': f"creative-webnar-{name}",
        'object_story_spec': json.dumps(story_spec),
    }, timeout=30)
    cr_data = cr_r.json()
    print(f"  Creative: {cr_data}")
    cr_id = cr_data.get('id')
    
    if not cr_id:
        print(f"  ERRO creative {name}"); continue
    
    ad_r = requests.post(f"{BASE}/{ACCT}/ads", data={
        'access_token': TOKEN,
        'name': f"webnar-{name}",
        'adset_id': NEW_ADSET_ID,
        'creative': json.dumps({'creative_id': cr_id}),
        'status': 'PAUSED',
    }, timeout=30)
    ad_data = ad_r.json()
    print(f"  Ad: {ad_data}")
    if ad_data.get('id'):
        created.append({'name': name, 'ad_id': ad_data['id']})
    time.sleep(1)

print(f"\n=== CONCLUIDO ===")
print(f"Adset: {NEW_ADSET_ID}")
print(f"Anuncios criados: {len(created)}/6")
for c in created:
    print(f"  {c['name']} → ad_id={c['ad_id']}")
