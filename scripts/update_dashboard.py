#!/usr/bin/env python3
"""
NBP Pontus Finance — Dashboard Auto-Updater
Fetches Meta Ads API and regenerates index.html for GitHub Pages
Runs every 10h via GitHub Actions
"""
import os, json, re, sys
from datetime import datetime, timedelta, timezone
try:
    import requests
except ImportError:
    import subprocess; subprocess.check_call([sys.executable,'-m','pip','install','requests','-q'])
    import requests

# ─── CONFIG ─────────────────────────────────────────────────────────────────
TOKEN      = os.environ['META_ACCESS_TOKEN']
ACCOUNT_ID = 'act_1664503901571256'
BASE       = 'https://graph.facebook.com/v19.0'
DAYS       = 10

# ─── API HELPERS ─────────────────────────────────────────────────────────────
def api_get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f'API error {r.status_code}: {r.text[:300]}', file=sys.stderr)
        r.raise_for_status()
    return r.json()

def paginate(url, params):
    results, data = [], api_get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next'):
        data = api_get(data['paging']['next'])
        results.extend(data.get('data', []))
    return results

def action_val(lst, atype):
    for a in (lst or []):
        if a.get('action_type') == atype:
            return int(float(a.get('value', 0)))
    return 0

def outbound_val(lst):
    for a in (lst or []):
        if a.get('action_type') == 'outbound_click':
            return int(float(a.get('value', 0)))
    return 0

# ─── DATE RANGE ──────────────────────────────────────────────────────────────
end_dt   = datetime.now(timezone.utc).date()
start_dt = end_dt - timedelta(days=DAYS - 1)
time_range = json.dumps({'since': str(start_dt), 'until': str(end_dt)})
print(f'Fetching {start_dt} → {end_dt}')

# ─── 1. GET ADS (name + thumbnail) ───────────────────────────────────────────
print('Fetching ads…')
ads_raw = paginate(f'{BASE}/{ACCOUNT_ID}/ads', {
    'effective_status': '["ACTIVE","PAUSED","CAMPAIGN_PAUSED","ADSET_PAUSED"]',
    'fields': 'id,name,creative{id,thumbnail_url}',
    'limit': 100
})
ad_meta = {}
for a in ads_raw:
    cr = a.get('creative', {})
    ad_meta[a['id']] = {
        'name':  a['name'],
        'thumb': cr.get('thumbnail_url', ''),
    }
print(f'  Found {len(ad_meta)} ads')

# ─── 2. GET PREVIEW LINKS ────────────────────────────────────────────────────
print('Fetching preview links…')
for ad_id, info in ad_meta.items():
    try:
        pv = api_get(f'{BASE}/{ad_id}/previews', {'ad_format': 'MOBILE_FEED_STANDARD'})
        body = pv.get('data', [{}])[0].get('body', '')
        m = re.search(r'src=[\'"](https://[^\'"]+)[\'"]', body)
        info['preview']      = m.group(1).replace('&amp;', '&') if m else ''
        info['preview_type'] = 'fb'
    except Exception as e:
        print(f'  preview failed for {ad_id}: {e}', file=sys.stderr)
        info['preview']      = ''
        info['preview_type'] = 'fb'

# ─── 3. FETCH INSIGHTS WITH AGE BREAKDOWN ────────────────────────────────────
print('Fetching insights…')
rows = paginate(f'{BASE}/{ACCOUNT_ID}/insights', {
    'fields': ','.join([
        'ad_id','ad_name','spend','impressions',
        'actions','outbound_clicks',
        'video_play_actions','video_thruplay_watched_actions'
    ]),
    'level':      'ad',
    'breakdowns': 'age',
    'time_range': time_range,
    'limit':      500
})
print(f'  {len(rows)} rows returned')

# ─── 4. AGGREGATE PER AD / AGE ───────────────────────────────────────────────
from collections import defaultdict
AGES_ORDER = ['18-24','25-34','35-44','45-54','55-64','65+']

def empty_agg():
    return {'spend':0.0,'leads':0,'imp':0,'cliques':0,'lpv':0,'ig_vis':0,'ig_fol':0,'reach':0}

ad_data = defaultdict(lambda: {
    'total':  empty_agg(),
    'by_age': defaultdict(empty_agg)
})

for row in rows:
    aid   = row['ad_id']
    age   = row.get('age', 'unknown')
    spend = float(row.get('spend', 0))
    imp   = int(row.get('impressions', 0))
    acts  = row.get('actions', [])
    ob    = row.get('outbound_clicks', [])

    leads   = action_val(acts, 'lead') or action_val(acts, 'onsite_conversion.lead_grouped')
    lpv     = action_val(acts, 'landing_page_view')
    cliques = outbound_val(ob)
    ig_vis  = action_val(acts, 'instagram_profile_visit') or action_val(acts, 'visit_instagram_profile')
    ig_fol  = action_val(acts, 'follow')

    for d in [ad_data[aid]['total'], ad_data[aid]['by_age'][age]]:
        d['spend']   += spend
        d['leads']   += leads
        d['imp']     += imp
        d['cliques'] += cliques
        d['lpv']     += lpv
        d['ig_vis']  += ig_vis
        d['ig_fol']  += ig_fol

# ─── 5. BUILD ADS ARRAY ──────────────────────────────────────────────────────
AGES_DISPLAY = {
    '18-24':'18\u201324','25-34':'25\u201334','35-44':'35\u201344',
    '45-54':'45\u201354','55-64':'55\u201364','65+':'65+'
}

def badge(total):
    l, s = total['leads'], total['spend']
    cpl  = s / l if l > 0 else 9999
    if l >= 30 and cpl <= 8:   return 'TOP',     'bg'
    if l >= 10 and cpl <= 12:  return 'BOM',     'by'
    if l >  0  and cpl > 12:   return 'REVISAR', 'br'
    if l == 0  and s  < 50:    return 'NOVO',    'bn'
    return 'TESTE', 'by'

def round_total(d):
    return {k: round(v,2) if k=='spend' else int(v) for k,v in d.items()}

# Sort by spend desc
sorted_ids = sorted(ad_data, key=lambda x: ad_data[x]['total']['spend'], reverse=True)

ADS = []
for i, aid in enumerate(sorted_ids):
    info   = ad_meta.get(aid, {'name': f'Ad {aid}', 'thumb': '', 'preview': '', 'preview_type': 'fb'})
    data   = ad_data[aid]
    total  = round_total(data['total'])
    bdg, bclass = badge(total)

    by_age_list = []
    for ak in AGES_ORDER:
        raw = data['by_age'].get(ak, empty_agg())
        by_age_list.append({'age': AGES_DISPLAY.get(ak, ak), **round_total(raw)})

    name = info['name']
    short = name if len(name) <= 22 else name[:20] + '…'

    ADS.append({
        'id':          aid,
        'key':         f'ad{i}',
        'badge':       bdg,
        'badgeClass':  bclass,
        'name':        name,
        'shortName':   short,
        'preview':     info.get('preview', ''),
        'previewType': info.get('preview_type', 'fb'),
        'thumb':       info.get('thumb', ''),
        'total':       total,
        'by_age':      by_age_list
    })

print(f'Built {len(ADS)} ad entries')

# ─── 6. INJECT INTO TEMPLATE ─────────────────────────────────────────────────
tmpl_path = os.path.join(os.path.dirname(__file__), 'dashboard_template.html')
with open(tmpl_path, 'r', encoding='utf-8') as f:
    html = f.read()

ads_json = json.dumps(ADS, ensure_ascii=False, indent=2)

new_data = (
    f'// __DATA_START__\n'
    f'const META_PERIOD = {{"since":"{start_dt}","until":"{end_dt}","days":{DAYS}}};\n'
    f'const AGES = [\'18\u201324\',\'25\u201334\',\'35\u201344\',\'45\u201354\',\'55\u201364\',\'65+\'];\n'
    f'const ADS = {ads_json};\n'
    f'// __DATA_END__'
)

html = re.sub(
    r'// __DATA_START__.*?// __DATA_END__',
    new_data,
    html,
    flags=re.DOTALL
)

out_path = os.path.join(os.path.dirname(__file__), '..', 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Written → index.html  ({len(html):,} bytes)')
print(f'Totals: spend={sum(a["total"]["spend"] for a in ADS):.2f}  leads={sum(a["total"]["leads"] for a in ADS)}')
