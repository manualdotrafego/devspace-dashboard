import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"

def get(actions):
    l=0
    for a in actions or []:
        t=a.get('action_type','')
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            l=max(l,int(a.get('value',0)))
    return l

PERIODOS=[("ABRIL","2026-04-01","2026-04-30"),
          ("MAIO","2026-05-01","2026-05-31"),
          ("JUNHO","2026-06-01","2026-06-30"),
          ("JULHO (parcial ate 03)","2026-07-01","2026-07-03")]

tot_sp=0; tot_ld=0
for nome,since,until in PERIODOS:
    d=requests.get(f"{BASE}/{ACCT}/insights",params={
        'fields':'spend,impressions,actions',
        'time_range':json.dumps({'since':since,'until':until}),
        'access_token':TOKEN},timeout=30).json().get('data',[])
    if not d:
        print(f"{nome}: sem dados"); continue
    d=d[0]; sp=float(d.get('spend',0)); ld=get(d.get('actions',[]))
    cpl=sp/ld if ld else 0
    print(f"{nome}|{sp:.2f}|{ld}|{cpl:.2f}")
    tot_sp+=sp; tot_ld+=ld

print(f"TOTAL|{tot_sp:.2f}|{tot_ld}|{tot_sp/tot_ld if tot_ld else 0:.2f}")

# breakdown por campanha no periodo todo
print("\n## POR CAMPANHA (abr-jul):")
r=requests.get(f"{BASE}/{ACCT}/insights",params={
    'fields':'spend,actions,campaign_name','level':'campaign','limit':100,
    'time_range':json.dumps({'since':'2026-04-01','until':'2026-07-03'}),
    'access_token':TOKEN},timeout=30).json().get('data',[])
rows=[]
for d in r:
    sp=float(d.get('spend',0)); ld=get(d.get('actions',[]))
    if sp>0: rows.append((sp,ld,d.get('campaign_name','')))
rows.sort(reverse=True)
for sp,ld,nm in rows:
    print(f"C|{nm[:48]}|{sp:.2f}|{ld}")
