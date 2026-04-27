import requests, json, os
from datetime import datetime, timezone

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"

def get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"  ERR {r.status_code}: {r.text[:300]}")
        return {}
    return r.json()

def paginate(url, params=None, max_pages=20):
    results, page, data = [], 0, get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next') and page < max_pages:
        data = get(data['paging']['next'])
        results.extend(data.get('data', []))
        page += 1
    return results

# ─── Info da conta ─────────────────────────────────────────────────────────────
acct = get(f"{BASE}/{ACCT}", {'fields': 'name,currency,account_status,spend_cap,amount_spent'})
print("="*70)
print(f"CONTA: {acct.get('name')}  ({ACCT})")
print(f"Moeda: {acct.get('currency')} | Status: {acct.get('account_status')}")
total_spent = float(acct.get('amount_spent', 0)) / 100
print(f"Gasto total acumulado: {acct.get('currency')} {total_spent:.2f}")
print("="*70)

# ─── Insights por período ──────────────────────────────────────────────────────
periods = [
    ("Hoje",       "2026-04-27", "2026-04-27"),
    ("Ontem",      "2026-04-26", "2026-04-26"),
    ("Últimos 7d", "2026-04-21", "2026-04-27"),
    ("Últimos 30d","2026-03-29", "2026-04-27"),
    ("Mês atual",  "2026-04-01", "2026-04-27"),
]

print("\n📅 RESUMO POR PERÍODO (nível conta)")
print("-"*70)
for label, since, until in periods:
    ins = get(f"{BASE}/{ACCT}/insights", {
        'fields': 'spend,impressions,clicks,ctr,cpc,cpm,reach,actions',
        'time_range': json.dumps({'since': since, 'until': until}),
        'level': 'account'
    }).get('data', [{}])
    d = ins[0] if ins else {}
    spend = float(d.get('spend', 0))
    impr  = int(d.get('impressions', 0))
    reach = int(d.get('reach', 0))
    clicks= int(d.get('clicks', 0))
    ctr   = float(d.get('ctr', 0))
    cpc   = float(d.get('cpc', 0))
    cpm   = float(d.get('cpm', 0))
    acts  = d.get('actions', [])
    leads = sum(float(a.get('value',0)) for a in acts if 'lead' in a.get('action_type','').lower())
    lc    = spend / leads if leads > 0 else 0
    print(f"\n  {label} ({since} → {until})")
    print(f"    Gasto:  {acct.get('currency')} {spend:.2f}  |  Alcance: {reach:,}  |  Imp: {impr:,}")
    print(f"    Clicks: {clicks:,}  |  CTR: {ctr:.2f}%  |  CPC: {cpc:.2f}  |  CPM: {cpm:.2f}")
    if leads > 0:
        print(f"    Leads:  {leads:.0f}  |  CPL: {acct.get('currency')} {lc:.2f}")

# ─── Por campanha (lifetime) ───────────────────────────────────────────────────
print("\n" + "="*70)
print("📊 CAMPANHAS — Gasto lifetime (ordenado por spend)")
print("="*70)

camps_ins = paginate(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,name,effective_status,objective',
    'limit': 100
})

camp_data = []
for c in camps_ins:
    ins = get(f"{BASE}/{c['id']}/insights", {
        'fields': 'spend,impressions,clicks,ctr,cpc,actions,reach',
        'date_preset': 'maximum',
        'level': 'campaign'
    }).get('data', [{}])
    d = ins[0] if ins else {}
    spend = float(d.get('spend', 0))
    if spend > 0:
        acts  = d.get('actions', [])
        leads = sum(float(a.get('value',0)) for a in acts if 'lead' in a.get('action_type','').lower())
        camp_data.append({
            'name':   c['name'],
            'status': c.get('effective_status','?'),
            'spend':  spend,
            'impr':   int(d.get('impressions', 0)),
            'reach':  int(d.get('reach', 0)),
            'clicks': int(d.get('clicks', 0)),
            'ctr':    float(d.get('ctr', 0)),
            'cpc':    float(d.get('cpc', 0)),
            'leads':  leads,
        })

camp_data.sort(key=lambda x: x['spend'], reverse=True)
total_camp = sum(c['spend'] for c in camp_data)
print(f"\n  Total gasto em campanhas: {acct.get('currency')} {total_camp:.2f}\n")

for i, c in enumerate(camp_data, 1):
    pct = c['spend'] / total_camp * 100 if total_camp > 0 else 0
    cpl = c['spend'] / c['leads'] if c['leads'] > 0 else 0
    status_icon = '🟢' if c['status'] == 'ACTIVE' else '⏸️'
    print(f"  {i}. {status_icon} {c['name'][:55]}")
    print(f"     Gasto: {acct.get('currency')} {c['spend']:.2f} ({pct:.1f}%)  |  Imp: {c['impr']:,}  |  Reach: {c['reach']:,}")
    print(f"     Clicks: {c['clicks']:,}  |  CTR: {c['ctr']:.2f}%  |  CPC: {c['cpc']:.2f}")
    if c['leads'] > 0:
        print(f"     Leads: {c['leads']:.0f}  |  CPL: {acct.get('currency')} {cpl:.2f}")
    print()

# ─── Últimos 7 dias por dia ────────────────────────────────────────────────────
print("="*70)
print("📆 GASTO DIÁRIO — Últimos 7 dias")
print("="*70)
daily = get(f"{BASE}/{ACCT}/insights", {
    'fields': 'spend,impressions,reach,actions',
    'time_range': json.dumps({'since': '2026-04-21', 'until': '2026-04-27'}),
    'time_increment': 1,
    'level': 'account',
    'limit': 10
}).get('data', [])

for d in daily:
    spend = float(d.get('spend', 0))
    impr  = int(d.get('impressions', 0))
    reach = int(d.get('reach', 0))
    acts  = d.get('actions', [])
    leads = sum(float(a.get('value',0)) for a in acts if 'lead' in a.get('action_type','').lower())
    bar   = '█' * int(spend / max(float(x.get('spend',0.01)) for x in daily) * 20) if daily else ''
    leads_str = f" | leads: {leads:.0f}" if leads > 0 else ""
    print(f"  {d.get('date_start','')}  {bar:<20}  {acct.get('currency')} {spend:>8.2f}  |  imp: {impr:>6,}  |  reach: {reach:>6,}{leads_str}")
