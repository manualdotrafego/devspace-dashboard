import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"
WEBNAR_CAMP = "120248546729160002"

VIDEO_IDS = {
    "IMG_5319": "1386873113201033",
    "IMG_5320": "836070529048703",
    "IMG_5321": "827389087091531",
    "IMG_5322": "1371159888237890",
    "IMG_5325": "2343313536159134",
    "IMG_5326": "2057045791912745",
}

# 1. Get adsets in WEBNAR campaign
print("=== Conjuntos do [NOVA CAPTACAO] - [WEBNAR] ===")
r = requests.get(f"{BASE}/{WEBNAR_CAMP}/adsets", params={
    'fields': 'id,name,status,effective_status,daily_budget,lifetime_budget,targeting,optimization_goal,billing_event,bid_amount,bid_strategy,start_time,end_time,promoted_object',
    'limit': 50, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])
print(f"Total adsets: {len(adsets)}")
for a in adsets:
    db = int(a.get('daily_budget') or 0)
    lb = int(a.get('lifetime_budget') or 0)
    print(f"  [{a.get('effective_status')}] {a['name'][:55]} | daily=R${db/100:.2f} | id={a['id']}")

# Sort by daily_budget ascending (lowest first), prefer active
active = [a for a in adsets if a.get('effective_status') == 'ACTIVE']
if not active:
    active = adsets
active.sort(key=lambda x: int(x.get('daily_budget') or 999999))
source = active[0]
print(f"\nFONTE PARA DUPLICAR: {source['name']} (id={source['id']})")
print(json.dumps(source, indent=2, ensure_ascii=False))

# 2. Get existing ads to grab page_id and creative details
print("\n=== Ads existentes no conjunto fonte ===")
ads_r = requests.get(f"{BASE}/{source['id']}/ads", params={
    'fields': 'id,name,status,creative',
    'limit': 10, 'access_token': TOKEN
}, timeout=30)
existing_ads = ads_r.json().get('data', [])
print(f"Ads: {len(existing_ads)}")

page_id = None
cta_type = "LEARN_MORE"
link_url = None
message = None

if existing_ads:
    # Get first ad creative details
    first_ad = existing_ads[0]
    cr_id = first_ad.get('creative', {}).get('id')
    if cr_id:
        cr_r = requests.get(f"{BASE}/{cr_id}", params={
            'fields': 'object_story_spec,asset_feed_spec,body,title,call_to_action_type,link_url',
            'access_token': TOKEN
        }, timeout=30)
        cr_data = cr_r.json()
        print("Creative:", json.dumps(cr_data, indent=2, ensure_ascii=False))
        
        # Extract page_id and link
        oss = cr_data.get('object_story_spec', {})
        video_data = oss.get('video_data', {})
        page_id = oss.get('page_id')
        link_url = video_data.get('call_to_action', {}).get('value', {}).get('link', '')
        cta_type = video_data.get('call_to_action', {}).get('type', 'LEARN_MORE')
        message = video_data.get('message', '')
        print(f"\npage_id={page_id}, link={link_url}, cta={cta_type}")

# 3. Create duplicate adset
print("\n=== Criando novo conjunto (duplicata) ===")
new_adset_data = {
    'access_token': TOKEN,
    'campaign_id': WEBNAR_CAMP,
    'name': source['name'] + ' — Copia Webnar',
    'status': 'PAUSED',
    'optimization_goal': source.get('optimization_goal', 'LEAD_GENERATION'),
    'billing_event': source.get('billing_event', 'IMPRESSIONS'),
    'targeting': json.dumps(source.get('targeting', {})),
}
if source.get('daily_budget'):
    new_adset_data['daily_budget'] = source['daily_budget']
if source.get('lifetime_budget') and int(source.get('lifetime_budget',0)) > 0:
    new_adset_data['lifetime_budget'] = source['lifetime_budget']
if source.get('bid_amount'):
    new_adset_data['bid_amount'] = source['bid_amount']
if source.get('bid_strategy'):
    new_adset_data['bid_strategy'] = source['bid_strategy']
if source.get('end_time'):
    new_adset_data['end_time'] = source['end_time']

new_as_r = requests.post(f"{BASE}/{ACCT}/adsets", data=new_adset_data, timeout=30)
new_as = new_as_r.json()
print("Adset criado:", json.dumps(new_as, indent=2))
new_adset_id = new_as.get('id')

if not new_adset_id:
    print("ERRO criando adset!"); exit(1)

if not page_id:
    print("ERRO: page_id nao encontrado. Verifique o creative acima."); exit(1)

# 4. Create 6 ads
print(f"\n=== Criando 6 anuncios no adset {new_adset_id} ===")
for name, video_id in VIDEO_IDS.items():
    print(f"\n  [{name}] video_id={video_id}")
    
    # Create creative
    story_spec = {
        'page_id': page_id,
        'video_data': {
            'video_id': video_id,
            'message': message or 'Consultor, mentor que quer escalar para mais de 10k mes?',
            'call_to_action': {
                'type': cta_type or 'LEARN_MORE',
                'value': {'link': link_url or 'https://wa.me/'}
            }
        }
    }
    cr_r = requests.post(f"{BASE}/{ACCT}/adcreatives", data={
        'access_token': TOKEN,
        'name': f"creative-{name}",
        'object_story_spec': json.dumps(story_spec),
    }, timeout=30)
    cr_data = cr_r.json()
    print(f"  Creative: {cr_data}")
    cr_id = cr_data.get('id')
    
    if not cr_id:
        print(f"  ERRO criando creative para {name}"); continue
    
    # Create ad
    ad_r = requests.post(f"{BASE}/{ACCT}/ads", data={
        'access_token': TOKEN,
        'name': f"webnar-{name}",
        'adset_id': new_adset_id,
        'creative': json.dumps({'creative_id': cr_id}),
        'status': 'PAUSED',
    }, timeout=30)
    ad_data = ad_r.json()
    print(f"  Ad: {ad_data}")
    time.sleep(1)

print("\n=== CONCLUIDO ===")
print(f"Novo conjunto: {new_adset_id}")
print(f"Ative o conjunto quando estiver pronto para veicular")
