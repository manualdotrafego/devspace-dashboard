import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"  # DevSpace

CAMP_IDS = [
    "120247963737730581",  # VALIDAÇÃO CRIATIVO
    "120248610894960581",  # QUENTE CBO
]

print("=== DEVSPACE — Orcamentos diarios ativos ===\n")
total = 0
for cid in CAMP_IDS:
    # Get campaign info
    c_r = requests.get(f"{BASE}/{cid}", params={
        'fields': 'id,name,effective_status,daily_budget,lifetime_budget,bid_strategy',
        'access_token': TOKEN
    }, timeout=30)
    c = c_r.json()
    name = c.get('name', '')
    status = c.get('effective_status', '')
    c_daily = int(c.get('daily_budget') or 0) / 100
    
    print(f"[{status}] {name}")
    print(f"  ID: {cid}")
    
    if c_daily > 0:
        print(f"  Orcamento CAMPANHA (CBO): R${c_daily:.2f}/dia")
        total += c_daily
    else:
        # ABO: sum active adsets
        as_r = requests.get(f"{BASE}/{cid}/adsets", params={
            'fields': 'id,name,effective_status,daily_budget,lifetime_budget',
            'limit': 100, 'access_token': TOKEN
        }, timeout=30)
        adsets = as_r.json().get('data', [])
        sum_active = 0
        print(f"  ABO — somando conjuntos ativos:")
        for a in adsets:
            if a.get('effective_status') == 'ACTIVE':
                ab = int(a.get('daily_budget') or 0) / 100
                sum_active += ab
                print(f"    R${ab:.2f}/dia | {a['name'][:55]}")
        print(f"  Total conjuntos ativos: R${sum_active:.2f}/dia")
        total += sum_active
    print()

print(f"=== TOTAL DIARIO DEVSPACE: R${total:.2f} ===")
