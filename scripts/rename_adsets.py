import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"

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

def paginate(url, params):
    results, data = [], api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next'):
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
    return results

# ─── Busca todos os adsets da conta ──────────────────────────────────────────
print("Buscando ad sets da conta DevSpace...")
adsets = paginate(f"{BASE}/{ACCT}/adsets", {
    'fields': 'id,name,campaign_id,created_time,status,effective_status',
    'limit': 100
})

print(f"Total ad sets encontrados: {len(adsets)}")
for a in adsets:
    print(f"  [{a.get('effective_status','?')[:6]}] {a['name']}  (id:{a['id']}, criado:{a.get('created_time','')[:19]})")

# ─── Filtra os que têm VALIDAÇÃO CRIATIVO no nome ────────────────────────────
targets = [a for a in adsets if 'VALIDAÇÃO CRIATIVO' in a['name'] or 'VALIDACAO CRIATIVO' in a['name'].upper()]
print(f"\nAd sets com 'VALIDAÇÃO CRIATIVO': {len(targets)}")

# Ordena por data de criação (crescente)
targets.sort(key=lambda x: x.get('created_time', ''))

print("\nOrdem antes do rename:")
for i, a in enumerate(targets, 1):
    print(f"  {i:2}. {a['name']}  (id:{a['id']}, criado:{a.get('created_time','')[:19]})")

# ─── Renomeia: [AD SET 1.N] - [VALIDAÇÃO CRIATIVO] ───────────────────────────
print("\n" + "="*60)
print("RENOMEANDO...")
print("="*60)

for i, adset in enumerate(targets, 1):
    new_name = f"[AD SET 1.{i}] - [VALIDAÇÃO CRIATIVO]"
    old_name = adset['name']

    result = api_post(f"{BASE}/{adset['id']}", {'name': new_name})

    if result.get('success') or result.get('id'):
        print(f"  ✅ {old_name}")
        print(f"     → {new_name}")
    else:
        print(f"  ❌ ERRO em {old_name}: {result}")

print("\n" + "="*60)
print("VERIFICAÇÃO FINAL")
print("="*60)
updated = paginate(f"{BASE}/{ACCT}/adsets", {
    'fields': 'id,name,created_time',
    'limit': 100
})
updated.sort(key=lambda x: x.get('created_time',''))
valids = [a for a in updated if 'VALIDAÇÃO CRIATIVO' in a['name']]
for a in valids:
    print(f"  {a['name']}  (id:{a['id']})")
