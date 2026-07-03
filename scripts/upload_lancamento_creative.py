import requests, os, json, unicodedata
from datetime import date

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"
since = "2026-07-01"; until = date.today().isoformat()

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn').lower()

# Find all active campaigns + spend in period to identify the 3 webinar ones
r = requests.get(f"{BASE}/{ACCT}/campaigns", params={
    'fields':'id,name,effective_status','limit':200,'access_token':TOKEN}, timeout=30)
camps = r.json().get('data', [])

def get(actions):
    leads=lc=0
    for a in actions or []:
        t=a.get('action_type',''); v=int(a.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'): leads=max(leads,v)
        elif t=='link_click': lc=v
    return leads,lc

print(f"## PERIODO CICLO 15: {since} -> {until}\n")
print("## Campanhas webinar com entrega no periodo:")
webinar_camps = []
for c in camps:
    nm = norm(c.get('name',''))
    if not ('webnar' in nm or 'webinar' in nm or 'escala' in nm or 'captac' in nm): continue
    ins = requests.get(f"{BASE}/{c['id']}/insights", params={
        'fields':'spend','time_range':json.dumps({'since':since,'until':until}),
        'access_token':TOKEN}, timeout=30).json().get('data',[])
    sp = float(ins[0].get('spend',0)) if ins else 0
    if sp > 0:
        webinar_camps.append(c)
        print(f"  [{c.get('effective_status')}] {c['name']} | gasto={sp:.2f} | id={c['id']}")

tot={'spend':0,'imp':0,'clk':0,'lc':0,'leads':0}
print(f"\n## Detalhe por campanha:")
for c in webinar_camps:
    d = requests.get(f"{BASE}/{c['id']}/insights", params={
        'fields':'spend,impressions,clicks,actions','time_range':json.dumps({'since':since,'until':until}),
        'access_token':TOKEN}, timeout=30).json().get('data',[{}])[0]
    sp=float(d.get('spend',0)); imp=int(d.get('impressions',0)); clk=int(d.get('clicks',0))
    leads,lc=get(d.get('actions',[]))
    print(f"  {c['name'][:40]:<40} EUR{sp:7.2f} | {leads} leads")
    tot['spend']+=sp; tot['imp']+=imp; tot['clk']+=clk; tot['lc']+=lc; tot['leads']+=leads

cpm=tot['spend']/tot['imp']*1000 if tot['imp'] else 0
ctr=tot['clk']/tot['imp']*100 if tot['imp'] else 0
cpc=tot['spend']/tot['lc'] if tot['lc'] else 0
conv=tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl=tot['spend']/tot['leads'] if tot['leads'] else 0
print(f"\n## COMBINADO CICLO 15 ({len(webinar_camps)} campanhas)")
print(f"VALOR_USADO={tot['spend']:.2f}")
print(f"IMPRESSOES={tot['imp']}")
print(f"CLIQUES={tot['clk']}")
print(f"CPM={cpm:.2f}")
print(f"CTR={ctr:.2f}")
print(f"CPC_LINK={cpc:.2f}")
print(f"LEADS={tot['leads']}")
print(f"PCT_CONV={conv:.2f}")
print(f"CPL={cpl:.2f}")
