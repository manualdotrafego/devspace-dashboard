import requests, os, json
from datetime import date, timedelta

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

# Use last 30 days for statistical relevance
today = date.today()
since = (today - timedelta(days=30)).isoformat()
until = today.isoformat()

def get_leads(actions):
    leads = lc = 0
    for act in actions or []:
        t = act.get('action_type','')
        v = int(act.get('value',0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': lc = v
    return leads, lc

def fetch_breakdown(bd_name, label):
    print(f"\n## BREAKDOWN: {label}")
    print(f"## HEADER: segment|spend|impressions|clicks|leads|cpm|ctr|cpc|cpl|pct_leads")
    r = requests.get(f"{BASE}/{CAMP}/insights", params={
        'fields':'spend,impressions,clicks,actions,cpm,ctr,cpc',
        'breakdowns': bd_name,
        'time_range': json.dumps({'since':since,'until':until}),
        'level':'campaign',
        'limit':200,
        'access_token':TOKEN
    }, timeout=40)
    data = r.json()
    if 'error' in data:
        print(f"## ERROR: {data['error'].get('message','')[:100]}")
        return
    rows = data.get('data', [])
    total_leads = sum(get_leads(d.get('actions',[]))[0] for d in rows)
    out = []
    for d in rows:
        seg_parts = []
        for k in ['age','gender','publisher_platform','platform_position','impression_device']:
            if k in d: seg_parts.append(str(d[k]))
        seg = ' / '.join(seg_parts) if seg_parts else 'unknown'
        spend = float(d.get('spend',0))
        imps = int(d.get('impressions',0))
        clicks = int(d.get('clicks',0))
        leads, lc = get_leads(d.get('actions',[]))
        cpm = float(d.get('cpm',0))
        ctr = float(d.get('ctr',0))
        cpc = float(d.get('cpc',0))
        cpl = spend/leads if leads > 0 else 0
        pct = (leads/total_leads*100) if total_leads else 0
        out.append((seg, spend, imps, clicks, leads, cpm, ctr, cpc, cpl, pct))
    # sort by leads desc
    out.sort(key=lambda x: -x[4])
    for o in out:
        cpl_s = f"{o[8]:.2f}" if o[4] > 0 else "0"
        print(f"##R|{o[0]}|{o[1]:.2f}|{o[2]}|{o[3]}|{o[4]}|{o[5]:.2f}|{o[6]:.2f}|{o[7]:.2f}|{cpl_s}|{o[9]:.1f}")

print(f"## PERIODO: {since} -> {until} (30 dias)")
fetch_breakdown('age', 'IDADE')
fetch_breakdown('gender', 'SEXO')
fetch_breakdown('publisher_platform', 'PLATAFORMA')
fetch_breakdown('platform_position', 'POSICIONAMENTO')
# combined age+gender
fetch_breakdown('age,gender', 'IDADE x SEXO')
print("\n## DONE")
