import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"
since="2026-07-01"; until="2026-07-07"
def get(a):
    l=0
    for x in a or []:
        t=x.get('action_type','')
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            l=max(l,int(x.get('value',0)))
    return l
r=requests.get(f"{BASE}/{ACCT}/insights",params={
    'fields':'spend,actions,campaign_name,campaign_id','level':'campaign','limit':100,
    'time_range':json.dumps({'since':since,'until':until}),'access_token':TOKEN},timeout=40).json()
rows=[]
for d in r.get('data',[]):
    sp=float(d.get('spend',0))
    if sp>0: rows.append((sp,get(d.get('actions',[])),d.get('campaign_name',''),d.get('campaign_id','')))
rows.sort(reverse=True)
print(f"## Campanhas com gasto {since} -> {until}:")
for sp,l,nm,cid in rows:
    cpl=sp/l if l else 0
    print(f"R|{nm}|{cid}|{sp:.2f}|{l}|{cpl:.2f}" if l else f"R|{nm}|{cid}|{sp:.2f}|0|-")
