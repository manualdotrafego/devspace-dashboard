import requests, os, json
from datetime import date, timedelta
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"
ontem=(date.today()-timedelta(days=1)).isoformat()

# campanhas ativas
r=requests.get(f"{BASE}/{ACCT}/campaigns",params={
    'fields':'id,name,effective_status,daily_budget','limit':200,'access_token':TOKEN},timeout=40).json()
for c in r.get('data',[]):
    if c.get('effective_status')!='ACTIVE': continue
    cdb=int(c.get('daily_budget') or 0)/100
    print(f"\n## CAMPANHA: {c['name']} {'| CBO EUR'+format(cdb,'.2f')+'/dia' if cdb else '| ABO'}")
    # adsets
    ar=requests.get(f"{BASE}/{c['id']}/adsets",params={
        'fields':'id,name,effective_status,daily_budget','limit':100,'access_token':TOKEN},timeout=40).json()
    for a in ar.get('data',[]):
        if a.get('effective_status')!='ACTIVE': continue
        adb=int(a.get('daily_budget') or 0)/100
        print(f"  CONJUNTO: {a['name']} {'| EUR'+format(adb,'.2f')+'/dia' if adb else '| (verba da campanha CBO)'}")
        # ads
        adr=requests.get(f"{BASE}/{a['id']}/ads",params={
            'fields':'id,name,effective_status','limit':100,'access_token':TOKEN},timeout=40).json()
        for ad in adr.get('data',[]):
            if ad.get('effective_status')!='ACTIVE': continue
            # gasto de ontem do ad
            ins=requests.get(f"{BASE}/{ad['id']}/insights",params={
                'fields':'spend','time_range':json.dumps({'since':ontem,'until':ontem}),
                'access_token':TOKEN},timeout=30).json().get('data',[])
            sp=float(ins[0].get('spend',0)) if ins else 0
            print(f"    AD: {ad['name']} | gasto ontem: EUR{sp:.2f}")
