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

# Get source adset info to extract creative
print("=== Buscando adsets do WEBNAR ===")
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
print(f"Adset fonte: {source['name']} ({source['id']})")

# Get ads and creative from source adset
ads_r = requests.get(f"{BASE}/{source['id']}/ads", params={
    'fields': 'id,name,status,creative',
    'limit': 10, 'access_token': TOKEN
}, timeout=30)
existing_ads = ads_r.json().get('data', [])

page_id = None
cta_type = "SEE_DETAILS"
link_url = "https://go.joaomafra.pt/"
message = ""
instagram_user_id = None
image_hash = None

if existing_ads:
    cr_id = existing_ads[0].get('creative', {}).get('id')
    if cr_id:
        cr_r = requests.get(f"{BASE}/{cr_id}", params={
            'fields': 'object_story_spec',
            'access_token': TOKEN
        }, timeout=30)
        cr_data = cr_r.json()
        oss = cr_data.get('object_story_spec', {})
        video_data = oss.get('video_data', {})
        page_id = oss.get('page_id')
        instagram_user_id = oss.get('instagram_user_id')
        link_url = video_data.get('call_to_action', {}).get('value', {}).get('link', link_url)
        cta_type = video_data.get('call_to_action', {}).get('type', cta_type)
        message = video_data.get('message', message)
        image_hash = video_data.get('image_hash')
        print(f"page_id={page_id}, ig={instagram_user_id}, link={link_url}")
        print(f"cta={cta_type}, image_hash={image_hash}")

# For each video: get thumbnail from Meta API if image_hash missing
def get_video_thumbnail(video_id):
    r = requests.get(f"{BASE}/{video_id}", params={
        'fields': 'thumbnails',
        'access_token': TOKEN
    }, timeout=30)
    data = r.json()
    thumbs = data.get('thumbnails', {}).get('data', [])
    if thumbs:
        # Return first thumbnail URI
        return thumbs[0].get('uri', '')
    return None

# Create 6 ads using the existing adset
print(f"\n=== Criando 6 anuncios no adset {NEW_ADSET_ID} ===")
created = []
for name, video_id in VIDEO_IDS.items():
    print(f"\n  [{name}] video_id={video_id}")
    
    # Build video_data
    vdata = {
        'video_id': video_id,
        'message': message or 'Sua chance de mudar tudo está aqui!\nO que você vai fazer com ela?',
        'call_to_action': {
            'type': cta_type,
            'value': {'link': link_url}
        }
    }
    
    # Use image_hash from source creative as thumbnail (same page, valid)
    if image_hash:
        vdata['image_hash'] = image_hash
    else:
        # Fallback: get thumbnail from video
        thumb_url = get_video_thumbnail(video_id)
        if thumb_url:
            vdata['image_url'] = thumb_url
            print(f"  thumb_url={thumb_url[:60]}")
    
    story_spec = {
        'page_id': page_id,
        'video_data': vdata
    }
    if instagram_user_id:
        story_spec['instagram_user_id'] = instagram_user_id

    cr_payload = {
        'access_token': TOKEN,
        'name': f"creative-webnar-{name}",
        'object_story_spec': json.dumps(story_spec),
    }
    cr_r = requests.post(f"{BASE}/{ACCT}/adcreatives", data=cr_payload, timeout=30)
    cr_data = cr_r.json()
    print(f"  Creative resp: {cr_data}")
    cr_id = cr_data.get('id')
    
    if not cr_id:
        print(f"  ERRO criando creative {name} — pulando")
        continue
    
    ad_r = requests.post(f"{BASE}/{ACCT}/ads", data={
        'access_token': TOKEN,
        'name': f"webnar-{name}",
        'adset_id': NEW_ADSET_ID,
        'creative': json.dumps({'creative_id': cr_id}),
        'status': 'PAUSED',
    }, timeout=30)
    ad_data = ad_r.json()
    print(f"  Ad resp: {ad_data}")
    if ad_data.get('id'):
        created.append({'name': name, 'ad_id': ad_data['id'], 'creative_id': cr_id})
    time.sleep(1)

print(f"\n=== CONCLUIDO ===")
print(f"Adset: {NEW_ADSET_ID}")
print(f"Anuncios criados: {len(created)}/6")
for c in created:
    print(f"  {c['name']} → ad_id={c['ad_id']}")
