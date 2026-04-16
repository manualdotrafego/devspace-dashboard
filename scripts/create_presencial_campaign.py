import requests, json, os, sys, re
from datetime import datetime, timezone

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = 'https://graph.facebook.com/v19.0'
ACCT  = 'act_615338413578534'
LP    = 'https://noblankpage.com/presencial-nod-maio-2026/#offer'

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok: print(f'GET ERR {r.status_code}: {r.text[:400]}', file=sys.stderr); r.raise_for_status()
    return r.json()

def api_post(url, data):
    data['access_token'] = TOKEN
    r = requests.post(url, data=data, timeout=30)
    if not r.ok: print(f'POST ERR {r.status_code}: {r.text[:600]}', file=sys.stderr); r.raise_for_status()
    return r.json()

def paginate(url, params):
    results, data = [], api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next'):
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
    return results

# ─── 1. GET BEST CREATIVE IDs (from top ads) ─────────────────────────────────
TOP_AD_IDS = [
    ('120249001823240002', 'IMG_4583'),   # 13 leads, CPL €5.75
    ('120249005627130002', 'IMG_4585'),   # 9 leads,  CPL €5.50
    ('120249005624690002', 'IMG_4584'),   # 4 leads,  CPL €6.65
    ('120249005639330002', 'MIX ESTÁTICO'),  # CTR 3.54%
]

print("=== 1. BUSCANDO CREATIVE IDs ===")
creatives = []
for ad_id, ad_name in TOP_AD_IDS:
    d = api_get(f'{BASE}/{ad_id}', {'fields': 'id,name,creative{id,name,thumbnail_url}'})
    cr = d.get('creative', {})
    creatives.append({'ad_id': ad_id, 'ad_name': ad_name, 'creative_id': cr.get('id',''), 'thumb': cr.get('thumbnail_url','')})
    print(f"  {ad_name} → creative_id: {cr.get('id','')}")

# ─── 2. GET PIXEL for the account ────────────────────────────────────────────
print("\n=== 2. BUSCANDO PIXEL ===")
pixels = paginate(f'{BASE}/{ACCT}/adspixels', {'fields': 'id,name,last_fired_time', 'limit': 10})
pixel_id = None
for px in pixels:
    print(f"  Pixel: {px['name']} (id:{px['id']}, last_fired:{px.get('last_fired_time','never')})")
    if not pixel_id:
        pixel_id = px['id']

# ─── 3. GET TARGETING from original ad sets ───────────────────────────────────
print("\n=== 3. BUSCANDO TARGETING ORIGINAL ===")
VALIDACAO_CAMP = '120249001823230002'
original_adsets = paginate(f'{BASE}/{VALIDACAO_CAMP}/adsets', {
    'fields': 'id,name,targeting,bid_strategy,daily_budget,optimization_goal,billing_event,destination_type',
    'limit': 10
})
base_targeting = None
for ads in original_adsets:
    print(f"  Adset: {ads['name']}")
    if base_targeting is None:
        base_targeting = ads.get('targeting', {})

if base_targeting:
    print(f"  → Targeting capturado: geo={[g.get('name') for g in base_targeting.get('geo_locations',{}).get('countries',[])]}, age={base_targeting.get('age_min')}-{base_targeting.get('age_max')}")

# ─── 4. CREATE CAMPAIGN (ABO, PAUSED) ────────────────────────────────────────
print("\n=== 4. CRIANDO CAMPANHA ===")
camp_data = {
    'name': '[VENDAS] - [PRESENCIAL NOD MAIO 2026]',
    'objective': 'OUTCOME_SALES',
    'status': 'PAUSED',
    'special_ad_categories': json.dumps([]),
}
camp_resp = api_post(f'{BASE}/{ACCT}/campaigns', camp_data)
camp_id = camp_resp['id']
print(f"  ✅ Campanha criada: id={camp_id}")
print(f"     Nome: [VENDAS] - [PRESENCIAL NOD MAIO 2026]")
print(f"     Objetivo: OUTCOME_SALES | Budget: ABO | Status: PAUSED")

# ─── 5. CREATE 4 AD SETS (one per creative) ──────────────────────────────────
print("\n=== 5. CRIANDO AD SETS (ABO) ===")

# Use base targeting or fallback to broad
if not base_targeting:
    base_targeting = {
        'age_min': 22,
        'age_max': 55,
        'geo_locations': {'countries': ['PT', 'BR']},
        'publisher_platforms': ['facebook', 'instagram'],
        'facebook_positions': ['feed', 'story', 'reels'],
        'instagram_positions': ['stream', 'story', 'reels'],
    }

# promoted_object
promo_obj = {}
if pixel_id:
    promo_obj = {'pixel_id': pixel_id, 'custom_event_type': 'COMPLETE_REGISTRATION'}

# opt goal & billing
opt_goal = 'OFFSITE_CONVERSIONS' if pixel_id else 'LINK_CLICKS'
billing  = 'IMPRESSIONS'
daily_budget_cents = 1500  # €15/day per ad set

ADSET_IDS = []
for i, cr in enumerate(creatives):
    adset_name = f"[ABO] - [{cr['ad_name']}] - [VENDAS PRESENCIAL]"
    adset_data = {
        'name':              adset_name,
        'campaign_id':       camp_id,
        'status':            'PAUSED',
        'daily_budget':      daily_budget_cents,
        'billing_event':     billing,
        'optimization_goal': opt_goal,
        'destination_type':  'WEBSITE',
        'targeting':         json.dumps(base_targeting),
        'start_time':        datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+0000'),
    }
    if promo_obj:
        adset_data['promoted_object'] = json.dumps(promo_obj)

    try:
        r = api_post(f'{BASE}/{ACCT}/adsets', adset_data)
        adset_id = r['id']
        ADSET_IDS.append((adset_id, cr))
        print(f"  ✅ Ad set {i+1}: {adset_name}")
        print(f"     id={adset_id} | budget=€15/dia | opt={opt_goal}")
    except Exception as e:
        print(f"  ❌ Falhou adset {adset_name}: {e}")
        ADSET_IDS.append((None, cr))

# ─── 6. CREATE ADS ───────────────────────────────────────────────────────────
print("\n=== 6. CRIANDO ANÚNCIOS ===")
AD_IDS = []
for adset_id, cr in ADSET_IDS:
    if not adset_id or not cr['creative_id']:
        print(f"  ⏭ Pulando {cr['ad_name']} (sem adset ou creative)")
        continue
    ad_data = {
        'name':       f"[AD] - [{cr['ad_name']}] - [NOD PRESENCIAL]",
        'adset_id':   adset_id,
        'creative':   json.dumps({'creative_id': cr['creative_id']}),
        'status':     'PAUSED',
        'tracking_specs': json.dumps([{'action.type': ['offsite_conversion'], 'fb_pixel': [pixel_id]}]) if pixel_id else json.dumps([]),
    }
    try:
        r = api_post(f'{BASE}/{ACCT}/ads', ad_data)
        AD_IDS.append(r['id'])
        print(f"  ✅ Ad criado: {ad_data['name']}")
        print(f"     id={r['id']} | creative={cr['creative_id']} | status=PAUSED")
    except Exception as e:
        print(f"  ❌ Falhou ad {cr['ad_name']}: {e}")

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("ESTRUTURA CRIADA — TUDO PAUSADO")
print("="*60)
print(f"CAMP ID:  {camp_id}")
print(f"AD SETS:  {len([x for x,_ in ADSET_IDS if x])}")
print(f"ADS:      {len(AD_IDS)}")
print(f"LP:       {LP}")
print(f"PIXEL:    {pixel_id or 'nenhum encontrado'}")
print(f"OPT GOAL: {opt_goal}")
print(f"BUDGET:   €15/dia por ad set (ABO) — total max €60/dia se ativado")
print(f"GER:      https://business.facebook.com/adsmanager/manage/campaigns?act={ACCT.replace('act_','')}")
