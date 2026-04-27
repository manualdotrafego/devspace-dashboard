import requests, json, os
from datetime import datetime, timezone

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"   # CA - João Mafra lançamento

SINCE_STR = "2026-04-25"
UNTIL_STR = "2026-04-27"
# Brasil = UTC-3 → sábado 00h BRT = sábado 03h UTC
TS_FROM = int(datetime(2026, 4, 25, 3, 0, 0, tzinfo=timezone.utc).timestamp())
TS_TO   = int(datetime(2026, 4, 28, 3, 0, 0, tzinfo=timezone.utc).timestamp())

def get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"  ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

def paginate(url, params=None, max_pages=30):
    results, page, data = [], 0, get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next') and page < max_pages:
        data = get(data['paging']['next'])
        results.extend(data.get('data', []))
        page += 1
    return results

# ─── 0. Permissões do token ───────────────────────────────────────────────────
print("="*65)
print("PERMISSÕES DO TOKEN")
print("="*65)
perms = get(f"{BASE}/me/permissions")
granted = [p['permission'] for p in perms.get('data', []) if p.get('status') == 'granted']
print(f"  Granted: {', '.join(granted)}")
has_leads = 'leads_retrieval' in granted
print(f"  leads_retrieval: {'✅ SIM' if has_leads else '❌ NÃO'}")

# ─── 1. Campanhas LEAD_GEN ────────────────────────────────────────────────────
print("\n" + "="*65)
print("CAMPANHAS DE CAPTAÇÃO")
print("="*65)
camps = paginate(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,name,objective,effective_status,promoted_object',
    'filtering': json.dumps([{"field":"objective","operator":"IN",
                              "value":["LEAD_GENERATION","OUTCOME_LEADS"]}]),
    'limit': 100
})

# Coleta page_ids via promoted_object (muito mais simples)
page_ids = set()
for c in camps:
    po = c.get('promoted_object', {})
    pid = po.get('page_id')
    if pid:
        page_ids.add(pid)
    print(f"  [{c.get('effective_status','?')[:6]}] {c['name']} → page_id: {pid or '?'}")

print(f"\n  Total campanhas: {len(camps)} | Pages encontradas: {page_ids}")

# ─── 2. Ads das campanhas ATIVAS ─────────────────────────────────────────────
print("\n" + "="*65)
print("ADS DAS CAMPANHAS ATIVAS")
print("="*65)

all_ads = []
active = [c for c in camps if c.get('effective_status') == 'ACTIVE']
print(f"  {len(active)} campanhas ativas")

for camp in active:
    ads = get(f"{BASE}/{camp['id']}/ads", {
        'fields': 'id,name,adset_name',
        'limit': 100
    }).get('data', [])
    print(f"  [{camp['name'][:50]}] → {len(ads)} ads")
    for ad in ads:
        ad['campaign_name'] = camp['name']
        all_ads.append(ad)

print(f"  Total ads: {len(all_ads)}")

# ─── 3. Tenta /{ad_id}/leads direto ──────────────────────────────────────────
print("\n" + "="*65)
print(f"MÉTODO 1: /" + "{ad_id}/leads — " + f"{SINCE_STR} → {UNTIL_STR}")
print("="*65)

all_leads = []
filter_param = json.dumps([
    {"field":"time_created","operator":"GREATER_THAN","value": TS_FROM},
    {"field":"time_created","operator":"LESS_THAN",   "value": TS_TO},
])

for ad in all_ads:
    leads = paginate(f"{BASE}/{ad['id']}/leads", {
        'fields': 'id,created_time,field_data',
        'filtering': filter_param,
        'limit': 100
    })
    if leads:
        print(f"\n  ✅ [{ad.get('campaign_name','')[:40]}]")
        print(f"     Ad: {ad['name']} → {len(leads)} leads")
        for lead in leads:
            row = {
                'lead_id':  lead.get('id',''),
                'data_hora': lead.get('created_time','')[:19],
                'campanha': ad.get('campaign_name',''),
                'conjunto': ad.get('adset_name',''),
                'anuncio':  ad.get('name',''),
            }
            for field in lead.get('field_data', []):
                vals = field.get('values', [])
                row[field['name']] = ', '.join(vals) if isinstance(vals, list) else str(vals)
            all_leads.append(row)

print(f"\n  Subtotal via ad_id: {len(all_leads)} leads")

# ─── 4. Fallback: /{page_id}/leadgen_forms ───────────────────────────────────
if not all_leads and page_ids:
    print("\n" + "="*65)
    print("MÉTODO 2: /{page_id}/leadgen_forms")
    print("="*65)

    for pid in page_ids:
        print(f"\n  Page {pid}:")
        forms = paginate(f"{BASE}/{pid}/leadgen_forms", {
            'fields': 'id,name,status,leads_count',
            'limit': 100
        })
        print(f"  {len(forms)} formulários encontrados")

        for f in forms:
            fstatus = f.get('status','?')
            fname   = f['name']
            fcount  = f.get('leads_count','?')
            print(f"    [{fstatus}] {fname}  total_acumulado:{fcount}")

            leads = paginate(f"{BASE}/{f['id']}/leads", {
                'fields': 'id,created_time,field_data',
                'filtering': filter_param,
                'limit': 100
            })
            if leads:
                print(f"      ✅ {len(leads)} leads no período!")
                for lead in leads:
                    row = {
                        'lead_id':   lead.get('id',''),
                        'data_hora': lead.get('created_time','')[:19],
                        'formulario': fname,
                        'campanha':  '',
                    }
                    for field in lead.get('field_data', []):
                        vals = field.get('values', [])
                        row[field['name']] = ', '.join(vals) if isinstance(vals, list) else str(vals)
                    all_leads.append(row)
            else:
                print(f"      ○ 0 leads no período")

# ─── 5. Resultado ─────────────────────────────────────────────────────────────
print("\n" + "="*65)
print(f"TOTAL: {len(all_leads)} leads  |  {SINCE_STR} → {UNTIL_STR}")
print("="*65)

if all_leads:
    all_keys = []
    for r in all_leads:
        for k in r.keys():
            if k not in all_keys: all_keys.append(k)
    print(f"Colunas: {', '.join(all_keys)}\n")
    print("─── LEADS ───")
    for lead in all_leads:
        nome  = lead.get('full_name','') or lead.get('nome','') or ''
        email = lead.get('email','') or ''
        phone = lead.get('phone_number','') or lead.get('telefone','') or ''
        camp  = lead.get('campanha','') or lead.get('formulario','')
        print(f"  {lead.get('data_hora','')} | {camp[:35]} | {nome} | {email} | {phone}")
else:
    print("\n❌ Nenhum lead encontrado. Causas possíveis:")
    print("  1. Token sem permissão 'leads_retrieval'")
    print("  2. Não houve leads neste período nas campanhas ativas")
    print("  3. Os formulários pertencem a uma página diferente")
