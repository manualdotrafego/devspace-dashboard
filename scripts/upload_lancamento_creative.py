import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
MAFRA="120255355949960002"; CBO="120254908221730002"

print("=== BUDGETS ATUAIS (apos ajuste manual) ===")
tot=0
r=requests.get(f"{BASE}/{MAFRA}/adsets",params={
    'fields':'name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
for a in r.get('data',[]):
    st=a.get('effective_status','')
    db=int(a.get('daily_budget') or 0)/100
    if st in ('ACTIVE','IN_PROCESS'):
        tot+=db
        print(f"  [ATIVO] EUR{db:>5.2f}/d | {a['name'][:55]}")
    elif db>0:
        print(f"  [{st[:6]}] EUR{db:>5.2f}/d | {a['name'][:55]}")
c=requests.get(f"{BASE}/{CBO}",params={'fields':'daily_budget,effective_status','access_token':TOKEN},timeout=30).json()
cdb=int(c.get('daily_budget') or 0)/100
if c.get('effective_status') in ('ACTIVE','IN_PROCESS'): tot+=cdb
print(f"  [{c.get('effective_status')[:6]}] EUR{cdb:>5.2f}/d | CBO WEBNAIR - ESCALA")
print(f"TOTAL_DIARIO={tot:.2f}")

# Gasto do ciclo ate agora
tot_sp=0
for cid in [MAFRA, CBO, "120248546729160002"]:
    d=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend',
        'time_range':json.dumps({'since':'2026-07-15','until':'2026-07-21'}),'access_token':TOKEN},timeout=30).json().get('data',[])
    if d: tot_sp+=float(d[0].get('spend',0))
print(f"GASTO_CICLO_ATE_AGORA={tot_sp:.2f}")
