import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
since = "2026-06-24"; until = "2026-06-29"

CAMPS = [
    ("120248546729160002", "[NOVA CAPTACAO] - [WEBNAR] (antiga ABO)"),
    ("120254908221730002", "[CBO WEBNAIR - ESCALA] (nova CBO)"),
]

def fetch(cid):
    r = requests.get(f"{BASE}/{cid}/insights", params={
        'fields':'spend,impressions,clicks,actions,ctr,cpm,created_time',
        'time_range': json.dumps({'since':since,'until':until}),
        'access_token':TOKEN
    }, timeout=30)
    data = r.json().get('data', [])
    if not data: return None
    d = data[0]
    spend = float(d.get('spend',0))
    imps = int(d.get('impressions',0))
    clicks = int(d.get('clicks',0))
    ctr = float(d.get('ctr',0))
    cpm = float(d.get('cpm',0))
    leads = lc = lpv = 0
    for act in d.get('actions',[]):
        t = act.get('action_type',''); v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
        elif t == 'landing_page_view': lpv = v
    return {'spend':spend,'imps':imps,'clicks':clicks,'ctr':ctr,'cpm':cpm,'leads':leads,'lc':lc,'lpv':lpv}

# Campaign meta for the new one
nc = requests.get(f"{BASE}/120254908221730002", params={
    'fields':'name,created_time,start_time,effective_status,daily_budget','access_token':TOKEN
}, timeout=30).json()
print(f"## NOVA CAMPANHA: {nc.get('name')}")
print(f"   criada={nc.get('created_time','')[:16]} | iniciada={nc.get('start_time','')[:16]} | status={nc.get('effective_status')} | budget=EUR{int(nc.get('daily_budget') or 0)/100:.2f}/d")

print(f"\n## CICLO 14 PARCIAL (24-29/jun, 6 dias)\n")
tot = {'spend':0,'imps':0,'clicks':0,'leads':0,'lc':0,'lpv':0}
for cid, name in CAMPS:
    m = fetch(cid)
    if not m:
        print(f"### {name}: SEM DADOS"); continue
    cpc_link = m['spend']/m['lc'] if m['lc'] else 0
    cvr = m['leads']/m['lc']*100 if m['lc'] else 0
    cpl = m['spend']/m['leads'] if m['leads'] else 0
    print(f"### {name}")
    print(f"  VALOR={m['spend']:.2f} | IMPRESSOES={m['imps']} | CLIQUES={m['clicks']} | CPM={m['cpm']:.2f} | CTR={m['ctr']:.2f}")
    print(f"  CPC_LINK={cpc_link:.2f} | LEADS={m['leads']} | CONV={cvr:.2f} | CPL={cpl:.2f}")
    for k in tot: tot[k] += m[k]

# combined
cpc_link = tot['spend']/tot['lc'] if tot['lc'] else 0
cvr = tot['leads']/tot['lc']*100 if tot['lc'] else 0
cpl = tot['spend']/tot['leads'] if tot['leads'] else 0
cpm = tot['spend']/tot['imps']*1000 if tot['imps'] else 0
ctr = tot['clicks']/tot['imps']*100 if tot['imps'] else 0
print(f"\n### >>> TOTAL COMBINADO (duas campanhas) <<<")
print(f"  VALOR={tot['spend']:.2f} | IMPRESSOES={tot['imps']} | CLIQUES={tot['clicks']} | CPM={cpm:.2f} | CTR={ctr:.2f}")
print(f"  CPC_LINK={cpc_link:.2f} | LINK_CLICKS={tot['lc']} | LP_VIEWS={tot['lpv']} | LEADS={tot['leads']} | CONV={cvr:.2f} | CPL={cpl:.2f}")
