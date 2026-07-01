import requests, os, json
from datetime import date

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMPS = ["120248546729160002", "120254908221730002"]
since = "2026-06-24"; until = date.today().isoformat()

def get(actions):
    leads=lc=lpv=0
    for a in actions or []:
        t=a.get('action_type',''); v=int(a.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): leads=max(leads,v)
        elif t=='link_click': lc=v
        elif t=='landing_page_view': lpv=v
    return leads,lc,lpv

tot={'spend':0,'imp':0,'clk':0,'lc':0,'leads':0,'lpv':0}
print(f"## CICLO 14: {since} -> {until}")
for cid in CAMPS:
    nm=requests.get(f"{BASE}/{cid}",params={'fields':'name','access_token':TOKEN},timeout=30).json().get('name','')
    r=requests.get(f"{BASE}/{cid}/insights",params={
        'fields':'spend,impressions,clicks,actions','time_range':json.dumps({'since':since,'until':until}),
        'access_token':TOKEN},timeout=30).json().get('data',[])
    if not r: 
        print(f"  {nm}: sem dados"); continue
    d=r[0]; sp=float(d.get('spend',0)); imp=int(d.get('impressions',0)); clk=int(d.get('clicks',0))
    leads,lc,lpv=get(d.get('actions',[]))
    print(f"  {nm}: EUR{sp:.2f} | {leads} leads")
    tot['spend']+=sp; tot['imp']+=imp; tot['clk']+=clk; tot['lc']+=lc; tot['leads']+=leads; tot['lpv']+=lpv

cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
print(f"\n## COMBINADO CICLO 14")
print(f"VALOR_USADO={tot['spend']:.2f}")
print(f"IMPRESSOES={tot['imp']}")
print(f"CLIQUES={tot['clk']}")
print(f"CPM={cpm:.2f}")
print(f"CTR={ctr:.2f}")
print(f"CPC_LINK={cpc:.2f}")
print(f"LEADS={tot['leads']}")
print(f"PCT_CONV={conv:.2f}")
print(f"CPL={cpl:.2f}")
