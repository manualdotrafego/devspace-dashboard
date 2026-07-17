import requests, os, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
MAFRA="120255355949960002"

r=requests.get(f"{BASE}/{MAFRA}/adsets",params={
    'fields':'id,name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
adsets=r.get('data',[])
def find(pat): return next((x for x in adsets if x['name'].startswith(pat)), None)

print("=== Ativar img7120 + reacomodar (alvo EUR19/d) ===")
# 1.22 -> ACTIVE + EUR4
a=find('[AD SET 1.22')
pr=requests.post(f"{BASE}/{a['id']}",data={'status':'ACTIVE','daily_budget':'400','access_token':TOKEN},timeout=30).json()
print(f"  {'✅' if pr.get('success') else '❌'} [1.22] img7120 ATIVADO -> EUR4/d")
time.sleep(0.4)
# 1.9 -> EUR5 (de 6)
a=find('[AD SET 1.9')
pr=requests.post(f"{BASE}/{a['id']}",data={'daily_budget':'500','access_token':TOKEN},timeout=30).json()
print(f"  {'✅' if pr.get('success') else '❌'} [1.9] img6623 -> EUR5/d")
time.sleep(0.4)
# 1.2 -> EUR3, 1.4 -> EUR3
for pat,lbl in [('[AD SET 1.2 ','escalar_no_digital'),('[AD SET 1.4','voce_freelancer')]:
    a=find(pat)
    pr=requests.post(f"{BASE}/{a['id']}",data={'daily_budget':'300','access_token':TOKEN},timeout=30).json()
    print(f"  {'✅' if pr.get('success') else '❌'} {lbl} -> EUR3/d")
    time.sleep(0.4)

print("\n=== FINAL ===")
tot=0
r2=requests.get(f"{BASE}/{MAFRA}/adsets",params={
    'fields':'name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
for a in r2.get('data',[]):
    if a.get('effective_status') in ('ACTIVE','IN_PROCESS'):
        db=int(a.get('daily_budget') or 0)/100; tot+=db
        print(f"  EUR{db:.0f}/d | {a['name'][:50]}")
c=requests.get(f"{BASE}/120254908221730002",params={'fields':'daily_budget','access_token':TOKEN},timeout=30).json()
cdb=int(c.get('daily_budget') or 0)/100; tot+=cdb
print(f"  EUR{cdb:.0f}/d | CBO WEBNAIR - ESCALA")
print(f"TOTAL=EUR{tot:.2f}/dia")
