import requests, json, os, time
from datetime import datetime, timedelta, timezone
import urllib.request

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"   # DevSpace

now   = datetime.now(timezone.utc)
UNTIL = now.strftime("%Y-%m-%d")
SINCE = (now - timedelta(days=6)).strftime("%Y-%m-%d")

print(f"DevSpace Dashboard — {SINCE} → {UNTIL}")
os.makedirs("docs/thumbnails", exist_ok=True)

LEAD_TYPES = {
    'lead', 'onsite_conversion.lead_grouped',
    'offsite_conversion.fb_pixel_lead',
}

def get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"  ERR {r.status_code}: {r.text[:200]}")
        return {}
    return r.json()

def paginate(url, params=None, max_pages=20):
    results, page, data = [], 0, get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next') and page < max_pages:
        time.sleep(0.2)
        data = get(data['paging']['next'])
        results.extend(data.get('data', []))
        page += 1
    return results

def extract_leads(actions):
    return sum(float(a.get('value', 0)) for a in (actions or [])
               if a.get('action_type', '') in LEAD_TYPES)

def extract_video_views(actions):
    return sum(float(a.get('value', 0)) for a in (actions or [])
               if a.get('action_type') == 'video_view')

def extract_arr(arr):
    return sum(float(v.get('value', 0)) for v in (arr or []))

def safe_div(a, b, mult=1):
    return (a / b) * mult if b > 0 else 0

def proc(d):
    spend  = float(d.get('spend', 0))
    impr   = int(d.get('impressions', 0))
    clicks = int(d.get('clicks', 0))
    reach  = int(d.get('reach', 0))
    acts   = d.get('actions', [])
    leads  = extract_leads(acts)
    vviews = extract_video_views(acts)
    p25    = extract_arr(d.get('video_p25_watched_actions', []))
    p50    = extract_arr(d.get('video_p50_watched_actions', []))
    p75    = extract_arr(d.get('video_p75_watched_actions', []))
    p100   = extract_arr(d.get('video_p100_watched_actions', []))
    return {
        'spend':    round(spend, 2),
        'impressions': impr,
        'clicks':   clicks,
        'reach':    reach,
        'leads':    int(leads),
        'ctr':      round(float(d.get('ctr', 0)), 2),
        'cpc':      round(float(d.get('cpc', 0)), 2),
        'cpm':      round(float(d.get('cpm', 0)), 2),
        'cpl':      round(safe_div(spend, leads), 2),
        'lp_conv':  round(safe_div(leads, clicks, 100), 1),
        'hook_rate':round(safe_div(vviews, impr, 100), 1),
        'vp25':     round(safe_div(p25, impr, 100), 1),
        'vp50':     round(safe_div(p50, impr, 100), 1),
        'vp75':     round(safe_div(p75, impr, 100), 1),
        'vp100':    round(safe_div(p100, impr, 100), 1),
    }

INS_FIELDS = ('spend,impressions,clicks,reach,ctr,cpc,cpm,actions,'
              'video_p25_watched_actions,video_p50_watched_actions,'
              'video_p75_watched_actions,video_p100_watched_actions')

# ─── 1. Account info ──────────────────────────────────────────────────────────
print("1/6 Account info...")
acct = get(f"{BASE}/{ACCT}", {'fields': 'name,currency,account_status'})
print(f"   {acct.get('name')} | {acct.get('currency')}")

# ─── 2. Account daily ─────────────────────────────────────────────────────────
print("2/6 Daily account insights...")
raw_daily = get(f"{BASE}/{ACCT}/insights", {
    'fields': INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'time_increment': 1, 'level': 'account', 'limit': 10,
}).get('data', [])
daily = []
for d in raw_daily:
    row = proc(d); row['date'] = d.get('date_start', ''); daily.append(row)

raw_sum = get(f"{BASE}/{ACCT}/insights", {
    'fields': INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'account',
}).get('data', [{}])
summary = proc(raw_sum[0] if raw_sum else {})
print(f"   Gasto 7d: R$ {summary['spend']} | Leads: {summary['leads']}")

# ─── 3. Campaign insights ─────────────────────────────────────────────────────
print("3/6 Campaign insights...")
camp_7d = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'campaign_id,campaign_name,' + INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'campaign',
    'filtering': json.dumps([{"field": "spend", "operator": "GREATER_THAN", "value": 0}]),
    'limit': 100,
})

camp_daily_raw = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'campaign_id,' + INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'time_increment': 1, 'level': 'campaign',
    'filtering': json.dumps([{"field": "spend", "operator": "GREATER_THAN", "value": 0}]),
    'limit': 500,
})

from collections import defaultdict
camp_daily_map = defaultdict(list)
for d in camp_daily_raw:
    row = proc(d); row['date'] = d.get('date_start', '')
    camp_daily_map[d.get('campaign_id', '')].append(row)

# Get statuses
status_map = {}
camp_status_raw = get(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,effective_status', 'limit': 200,
}).get('data', [])
for c in camp_status_raw:
    status_map[c['id']] = c.get('effective_status', '?')

campaigns = []
for d in camp_7d:
    cid = d.get('campaign_id', '')
    row = proc(d)
    row['id']     = cid
    row['name']   = d.get('campaign_name', '')
    row['status'] = status_map.get(cid, '?')
    row['daily']  = sorted(camp_daily_map.get(cid, []), key=lambda x: x['date'])
    campaigns.append(row)
campaigns.sort(key=lambda x: x['spend'], reverse=True)
print(f"   {len(campaigns)} campanhas com gasto")

# ─── 4. Ad insights ───────────────────────────────────────────────────────────
print("4/6 Ad insights...")
ad_7d = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'ad_id,ad_name,campaign_id,campaign_name,adset_name,' + INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'ad',
    'filtering': json.dumps([{"field": "spend", "operator": "GREATER_THAN", "value": 0}]),
    'limit': 200,
})
print(f"   {len(ad_7d)} ads com gasto")

# ─── 5. Creative thumbnails ───────────────────────────────────────────────────
print("5/6 Thumbnails...")
ads = []
for d in ad_7d:
    aid = d.get('ad_id', '')
    row = proc(d)
    row.update({
        'id':            aid,
        'name':          d.get('ad_name', ''),
        'campaign_id':   d.get('campaign_id', ''),
        'campaign_name': d.get('campaign_name', ''),
        'adset_name':    d.get('adset_name', ''),
        'thumbnail':     '',
        'video_id':      '',
    })

    # Fetch creative
    time.sleep(0.1)
    cr = get(f"{BASE}/{aid}", {'fields': 'creative{thumbnail_url,video_id}'})
    creative  = cr.get('creative', {})
    thumb_url = creative.get('thumbnail_url', '')
    video_id  = creative.get('video_id', '')
    row['video_id'] = video_id or ''

    # Try public thumbnail from video
    if not thumb_url and video_id:
        vid = get(f"{BASE}/{video_id}", {'fields': 'thumbnails'})
        thumbs = vid.get('thumbnails', {}).get('data', [])
        if thumbs:
            thumb_url = thumbs[0].get('uri', '')

    if thumb_url:
        fname = f"docs/thumbnails/{aid}.jpg"
        try:
            sep = '&' if '?' in thumb_url else '?'
            dl_url = thumb_url + sep + f'access_token={TOKEN}'
            req = urllib.request.Request(dl_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                with open(fname, 'wb') as f:
                    f.write(resp.read())
            row['thumbnail'] = f'thumbnails/{aid}.jpg'
        except Exception as e:
            print(f"   ⚠ thumb {aid}: {e}")

    ads.append(row)

ads.sort(key=lambda x: x['spend'], reverse=True)
print(f"   {sum(1 for a in ads if a['thumbnail'])} thumbnails baixadas")

# ─── 6. Save JSON ─────────────────────────────────────────────────────────────
print("6/6 Salvando JSON...")
data = {
    'last_updated':  now.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'account':       {'id': ACCT, 'name': acct.get('name', 'DevSpace'),
                      'currency': acct.get('currency', 'BRL')},
    'date_range':    {'since': SINCE, 'until': UNTIL},
    'summary':       summary,
    'daily':         daily,
    'campaigns':     campaigns,
    'ads':           ads,
}
with open('docs/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n✅ docs/data.json salvo")
print(f"   {len(campaigns)} campanhas | {len(ads)} ads | {len(daily)} dias")
print(f"   Gasto 7d: {acct.get('currency','BRL')} {summary['spend']} | CPL: {summary['cpl']}")
