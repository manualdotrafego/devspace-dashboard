import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"  # DevSpace

# Get all active campaigns
print("=== DEVSPACE — Orcamentos diarios (campanhas ativas) ===\n")
r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields': 'id,name,effective_status,daily_budget,lifetime_budget,bid_strategy',
    'limit': 100,
    'effective_status': '["ACTIVE"]',
    'access_token': TOKEN
}, timeout=30)
camps = r.json().get('data', [])

total = 0
for c in camps:
    cid = c['id']
    name = c.get('name', '')
    status = c.get('effective_status', '')
    c_daily = int(c.get('daily_budget') or 0) / 100
    
    print(f"[{status}] {name}")
    print(f"  ID: {cid}")
    
    if c_daily > 0:
        print(f"  >> CBO: R${c_daily:.2f}/dia (orcamento na campanha)")
        total += c_daily
    else:
        # ABO: sum active adsets
        as_r = requests.get(f"{BASE}/{cid}/adsets", params={
            'fields': 'id,name,effective_status,daily_budget,lifetime_budget',
            'limit': 100, 'access_token': TOKEN
        }, timeout=30)
        adsets = as_r.json().get('data', [])
        sum_active = 0
        active_adsets = []
        for a in adsets:
            if a.get('effective_status') == 'ACTIVE':
                ab = int(a.get('daily_budget') or 0) / 100
                sum_active += ab
                active_adsets.append((a['name'], ab))
        print(f"  >> ABO — {len(active_adsets)} conjuntos ativos:")
        for n, ab in sorted(active_adsets, key=lambda x: -x[1]):
            print(f"     R${ab:>7.2f}/dia | {n[:60]}")
        print(f"  >> Total: R${sum_active:.2f}/dia")
        total += sum_active
    print()

print(f"{'='*60}")
print(f"TOTAL DIARIO DEVSPACE: R${total:.2f}")
print(f"{'='*60}")
