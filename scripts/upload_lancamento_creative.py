import requests, os, json
from datetime import date
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
since="2026-07-01"; until=date.today().isoformat()
CAMPS=[("120248546729160002","[NOVA CAPTAÇÃO]-[WEBNAR]"),
       ("120254908221730002","[CBO WEBNAIR - ESCALA]"),
       ("120255355949960002","[CAMPANHA WEBNAIR]-[TESTE MAFRA]")]
def get(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc
tot={'spend':0,'imp':0,'clk':0,'lc':0,'leads':0}
print(f"## CICLO 15: {since} -> {until}\n")
for cid,nm in CAMPS:
    d=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend,impressions,clicks,actions',
        'time_range':json.dumps({'since':since,'until':until}),'access_token':TOKEN},timeout=30).json().get('data',[])
    if not d: print(f"  {nm:<38} sem entrega"); continue
    d=d[0]; sp=float(d.get('spend',0)); imp=int(d.get('impressions',0)); clk=int(d.get('clicks',0)); l,lc=get(d.get('actions',[]))
    print(f"  {nm:<38} EUR{sp:7.2f} | {l} leads")
    tot['spend']+=sp; tot['imp']+=imp; tot['clk']+=clk; tot['lc']+=lc; tot['leads']+=l
cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
print(f"\n## COMBINADO")
print(f"VALOR_USADO={tot['spend']:.2f}\nIMPRESSOES={tot['imp']}\nCLIQUES={tot['clk']}\nCPM={cpm:.2f}\nCTR={ctr:.2f}\nCPC_LINK={cpc:.2f}\nLEADS={tot['leads']}\nPCT_CONV={conv:.2f}\nCPL={cpl:.2f}")
