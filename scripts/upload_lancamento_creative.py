import requests, os, time, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"

# (id_type, id_or_pattern, action, value_cents, label)
ACTIONS = [
    # TESTE MAFRA adsets
    ("adset_name","[AD SET 1.9","budget","600","img6623 -> EUR6/d"),
    ("adset_name","[AD SET 1.4","budget","400","voce_freelancer -> EUR4/d"),
    ("adset_name","[AD SET 1.2 ","budget","400","escalar_no_digital -> EUR4/d"),
    ("adset_name","[AD SET 1.22","pause",None,"img7120 (teste adiado)"),
    ("adset_name","[AD SET 1.21","pause",None,"conjunto vazio"),
    ("adset_name","[AD SET 1.20","pause",None,"conjunto vazio"),
    # CBO campaign
    ("campaign_id","120254908221730002","budget","400","CBO ESCALA -> EUR4/d"),
]

MAFRA="120255355949960002"
r=requests.get(f"{BASE}/{MAFRA}/adsets",params={
    'fields':'id,name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
adsets=r.get('data',[])

print("=== REBALANCEAMENTO -> alvo EUR300 no ciclo ===\n")
for typ, key, act, val, label in ACTIONS:
    if typ=="adset_name":
        a=next((x for x in adsets if x['name'].startswith(key)), None)
        if not a: print(f"  ? nao achei: {key}"); continue
        tid=a['id']; cur=int(a.get('daily_budget') or 0)/100
        if act=="budget":
            pr=requests.post(f"{BASE}/{tid}",data={'daily_budget':val,'access_token':TOKEN},timeout=30).json()
            print(f"  {'✅' if pr.get('success') else '❌'} {label} (era EUR{cur:.0f}) {pr if not pr.get('success') else ''}")
        else:
            pr=requests.post(f"{BASE}/{tid}",data={'status':'PAUSED','access_token':TOKEN},timeout=30).json()
            print(f"  {'✅' if pr.get('success') else '❌'} PAUSE {label}")
    else:
        cur_r=requests.get(f"{BASE}/{key}",params={'fields':'daily_budget','access_token':TOKEN},timeout=30).json()
        cur=int(cur_r.get('daily_budget') or 0)/100
        pr=requests.post(f"{BASE}/{key}",data={'daily_budget':val,'access_token':TOKEN},timeout=30).json()
        print(f"  {'✅' if pr.get('success') else '❌'} {label} (era EUR{cur:.0f}) {pr if not pr.get('success') else ''}")
    time.sleep(0.4)

print("\n=== ESTADO FINAL ===")
tot=0
r2=requests.get(f"{BASE}/{MAFRA}/adsets",params={
    'fields':'name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
for a in r2.get('data',[]):
    if a.get('effective_status') in ('ACTIVE','IN_PROCESS'):
        db=int(a.get('daily_budget') or 0)/100; tot+=db
        print(f"  [{a.get('effective_status')[:3]}] EUR{db:.0f}/d | {a['name'][:50]}")
cbo=requests.get(f"{BASE}/120254908221730002",params={'fields':'daily_budget,effective_status','access_token':TOKEN},timeout=30).json()
cdb=int(cbo.get('daily_budget') or 0)/100; tot+=cdb
print(f"  [CBO] EUR{cdb:.0f}/d | [CBO WEBNAIR - ESCALA] ({cbo.get('effective_status')})")
print(f"\nTOTAL DIARIO WEBINAR: EUR{tot:.2f}/dia")
