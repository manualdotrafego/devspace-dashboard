import requests, os, time, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"

CREATIVE_NAMES = [
    "1-pedro-completo",
    "1-pedro-simplificada",
    "2-robson-completa",
    "2-robson-simplificada",
    "3-aline-completo",
    "3-aline-simplificada",
    "4-vitor-geologo",
    "5-gabrielle-completo",
    "1-pedro-sem-caixinha",
    "2-robson-sem-caixinha",
    "3-aline-sem-caixinha",
]

def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

def api_post(url, data=None):
    d = dict(data or {}); d['access_token'] = TOKEN
    r = requests.post(url, data=d, timeout=30)
    if not r.ok:
        print(f"ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

# ─── 1. Acha os adsets pelo nome via filtering ────────────────────────────────
print("="*60)
print("BUSCANDO ADSETS DE [CAPTAÇÃO]-[0 AO EMPREGO]-[VALIDAÇÃO CRIATIVO]")
print("="*60)

# Busca adsets contendo "CRIATIVO" no nome (sem acento especial)
resp = api_get(f"{BASE}/{ACCT}/adsets", {
    'fields': 'id,name,campaign_id,created_time,effective_status',
    'filtering': json.dumps([{"field":"name","operator":"CONTAIN","value":"CRIATIVO"}]),
    'limit': 100
})

adsets_raw = resp.get('data', [])
print(f"Adsets com 'CRIATIVO' no nome: {len(adsets_raw)}")
for a in adsets_raw:
    print(f"  [{a.get('effective_status','?')[:6]}] {a['name']}  camp:{a.get('campaign_id','?')}")

if not adsets_raw:
    # fallback: busca por "Copia" ou "AD SET"
    resp2 = api_get(f"{BASE}/{ACCT}/adsets", {
        'fields': 'id,name,campaign_id,created_time,effective_status',
        'filtering': json.dumps([{"field":"name","operator":"CONTAIN","value":"AD SET 1"}]),
        'limit': 100
    })
    adsets_raw = resp2.get('data', [])
    print(f"\nFallback - adsets com 'AD SET 1': {len(adsets_raw)}")
    for a in adsets_raw:
        print(f"  [{a.get('effective_status','?')[:6]}] {a['name']}  camp:{a.get('campaign_id','?')}")

if not adsets_raw:
    print("❌ Nenhum adset encontrado. Verifique o nome da campanha.")
    exit(1)

# ─── 2. Descobre a campanha e confirma ───────────────────────────────────────
camp_ids = list(set(a['campaign_id'] for a in adsets_raw))
print(f"\nCampanhas associadas: {camp_ids}")

# Pega info da campanha
camp_info = api_get(f"{BASE}/{camp_ids[0]}", {
    'fields': 'id,name,effective_status'
})
print(f"Campanha: {camp_info.get('name')}  [{camp_info.get('effective_status')}]")

# Se tiver mais de 1 campanha, filtra pela que tem "EMPREGO" no nome
if len(camp_ids) > 1:
    for cid in camp_ids:
        ci = api_get(f"{BASE}/{cid}", {'fields': 'id,name'})
        print(f"  [{cid}] {ci.get('name')}")
        if 'EMPREGO' in ci.get('name','').upper():
            camp_info = ci
            break

# Filtra adsets apenas da campanha certa
targets = [a for a in adsets_raw if a['campaign_id'] == camp_info['id']]
targets.sort(key=lambda x: x.get('created_time',''))

print(f"\n{len(targets)} adsets da campanha [{camp_info['name']}]:")
for i, a in enumerate(targets, 1):
    print(f"  {i:2}. {a['name']}  (id:{a['id']})")

# ─── 3. Busca ads de cada adset ───────────────────────────────────────────────
print("\n" + "="*60)
print("ADS DENTRO DE CADA ADSET")
print("="*60)

adset_ads = {}
for a in targets:
    time.sleep(0.2)
    ads = api_get(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name,created_time',
        'limit': 50
    }).get('data', [])
    adset_ads[a['id']] = sorted(ads, key=lambda x: x.get('created_time',''))
    print(f"\n  [{a['name'][:55]}]")
    for ad in adset_ads[a['id']]:
        print(f"    → {ad['name']}  (id:{ad['id']})")

# ─── 4. Renomeia adsets ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("RENOMEANDO ADSETS")
print("="*60)

for i, adset in enumerate(targets, 1):
    new_name = f"[AD SET 1.{i}] - [VALIDA\u00c7\u00c3O CRIATIVO]"
    time.sleep(0.2)
    result = api_post(f"{BASE}/{adset['id']}", {'name': new_name})
    ok = result.get('success') or result.get('id')
    print(f"  {'✅' if ok else '❌'} {adset['name'][:55]}")
    print(f"       → {new_name}")

# ─── 5. Renomeia ads ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RENOMEANDO ADS")
print("="*60)

creative_idx = 0
for adset in targets:
    for ad in adset_ads[adset['id']]:
        if creative_idx >= len(CREATIVE_NAMES):
            print(f"  ⚠️  Mais ads do que nomes disponíveis (ad:{ad['id']})")
            continue
        new_ad_name = CREATIVE_NAMES[creative_idx]
        time.sleep(0.2)
        result = api_post(f"{BASE}/{ad['id']}", {'name': new_ad_name})
        ok = result.get('success') or result.get('id')
        print(f"  {'✅' if ok else '❌'} {ad['name'][:55]}")
        print(f"       → {new_ad_name}")
        creative_idx += 1

# ─── 6. Resultado final ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESULTADO FINAL")
print("="*60)
time.sleep(1)
final_adsets = api_get(f"{BASE}/{camp_info['id']}/adsets", {
    'fields': 'id,name',
    'limit': 50
}).get('data', [])
final_adsets.sort(key=lambda x: x.get('name',''))
for a in final_adsets:
    time.sleep(0.1)
    ads = api_get(f"{BASE}/{a['id']}/ads", {
        'fields': 'id,name', 'limit': 50
    }).get('data', [])
    print(f"\n  {a['name']}")
    for ad in ads:
        print(f"    └─ {ad['name']}")
