import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
since="2026-07-01"; until="2026-07-07"
CAMPS=[("120248546729160002","NOVA CAPTACAO",True),
       ("120254908221730002","CBO ESCALA",True),
       ("120255355949960002","TESTE MAFRA",False)]
def get(a):
    l=lc=0
    for x in a or []:
        t=x.get('action_type',''); v=int(x.get('value',0))
        if t in('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): l=max(l,v)
        elif t=='link_click': lc=v
    return l,lc
tot={'spend':0,'imp':0,'clk':0,'lc':0,'leads':0}
print(f"## CICLO 15 FECHADO: {since} -> {until}")
for cid,nm,inc in CAMPS:
    d=requests.get(f"{BASE}/{cid}/insights",params={'fields':'spend,impressions,clicks,actions',
        'time_range':json.dumps({'since':since,'until':until}),'access_token':TOKEN},timeout=30).json().get('data',[])
    if not d:
        print(f"  [{'IN' if inc else 'OUT'}] {nm}: sem dados"); continue
    d=d[0]; sp=float(d.get('spend',0)); l,lc=get(d.get('actions',[]))
    print(f"  [{'IN' if inc else 'OUT'}] {nm:<15} EUR{sp:7.2f} | {l} leads")
    if inc:
        tot['spend']+=sp; tot['imp']+=int(d.get('impressions',0)); tot['clk']+=int(d.get('clicks',0)); tot['lc']+=lc; tot['leads']+=l
cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
print(f"## SO AS 2 DE SEMPRE:")
print(f"V={tot['spend']:.2f}|I={tot['imp']}|C={tot['clk']}|CPM={cpm:.2f}|CTR={ctr:.2f}|CPC={cpc:.2f}|L={tot['leads']}|CV={conv:.2f}|CPL={cpl:.2f}")
