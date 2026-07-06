import requests, os, json
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
since="2026-07-01"; until=date.today().isoformat()
CAMPS=[("120248546729160002","NOVA CAPTACAO"),
       ("120254908221730002","CBO ESCALA"),
       ("120255355949960002","TESTE MAFRA")]
def get(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc
print(f"## {since} -> {until}")
rows=[]
for cid,cn in CAMPS:
    r=requests.get(f"{BASE}/{cid}/insights",params={
        'level':'ad','fields':'ad_name,spend,impressions,clicks,actions,cpm,ctr',
        'time_range':json.dumps({'since':since,'until':until}),'limit':100,
        'access_token':TOKEN},timeout=60).json()
    for d in r.get('data',[]):
        sp=float(d.get('spend',0))
        if sp==0: continue
        l,lc=get(d.get('actions',[]))
        imp=int(d.get('impressions',0)); clk=int(d.get('clicks',0))
        ctr=float(d.get('ctr',0)); cpm=float(d.get('cpm',0))
        cpc=sp/lc if lc else 0; cpl=sp/l if l else 0
        conv=l/lc*100 if lc else 0
        rows.append((l,cpl,sp,d.get('ad_name',''),cn,imp,clk,ctr,cpc,cpm,conv))
rows.sort(key=lambda x:(-x[0], x[1] if x[1] else 9999))
for l,cpl,sp,nm,cn,imp,clk,ctr,cpc,cpm,conv in rows:
    cpl_s=f"{cpl:.2f}" if l else "-"
    print(f"R|{nm}|{cn}|{sp:.2f}|{l}|{cpl_s}|{ctr:.2f}|{cpc:.2f}|{cpm:.2f}|{conv:.1f}|{imp}|{clk}")
