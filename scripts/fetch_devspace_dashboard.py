import requests, json, os, time
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import urllib.request

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"   # DevSpace

now   = datetime.now(timezone.utc)
UNTIL = now.strftime("%Y-%m-%d")
SINCE = (now - timedelta(days=6)).strftime("%Y-%m-%d")

print(f"DevSpace Dashboard — {SINCE} → {UNTIL}")
os.makedirs("docs/thumbnails", exist_ok=True)

# ── FIX: use ONLY onsite_conversion.lead_grouped  ─────────────────────────────
# Using both 'lead' AND 'onsite_conversion.lead_grouped' double-counts
# because they describe the same events. Meta Ads Manager shows
# onsite_conversion.lead_grouped as "Leads".
LEAD_TYPES = {
    'onsite_conversion.lead_grouped',
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

def extract_action(actions, atype):
    return sum(float(a.get('value', 0)) for a in (actions or [])
               if a.get('action_type') == atype)

def extract_video_views(actions):
    return sum(float(a.get('value', 0)) for a in (actions or [])
               if a.get('action_type') == 'video_view')

def extract_arr(arr):
    return sum(float(v.get('value', 0)) for v in (arr or []))

def safe_div(a, b, mult=1):
    return (a / b) * mult if b > 0 else 0

def proc(d, wa_action='contact'):
    spend  = float(d.get('spend', 0))
    impr   = int(d.get('impressions', 0))
    clicks = int(d.get('clicks', 0))
    reach  = int(d.get('reach', 0))
    acts    = d.get('actions', [])
    leads   = extract_leads(acts)
    vviews  = extract_video_views(acts)
    contact = extract_action(acts, wa_action)
    wishlist= extract_action(acts, 'add_to_wishlist')
    p25     = extract_arr(d.get('video_p25_watched_actions', []))
    p50     = extract_arr(d.get('video_p50_watched_actions', []))
    p75     = extract_arr(d.get('video_p75_watched_actions', []))
    p100    = extract_arr(d.get('video_p100_watched_actions', []))
    return {
        'spend':       round(spend, 2),
        'impressions': impr,
        'clicks':      clicks,
        'reach':       reach,
        'leads':       int(leads),
        'ctr':         round(float(d.get('ctr', 0)), 2),
        'cpc':         round(float(d.get('cpc', 0)), 2),
        'cpm':         round(float(d.get('cpm', 0)), 2),
        'cpl':         round(safe_div(spend, leads), 2),
        'lp_conv':     round(safe_div(leads, clicks, 100), 1),
        'hook_rate':   round(safe_div(vviews, impr, 100), 1),
        'vp25':        round(safe_div(p25, impr, 100), 1),
        'vp50':        round(safe_div(p50, impr, 100), 1),
        'vp75':        round(safe_div(p75, impr, 100), 1),
        'vp100':       round(safe_div(p100, impr, 100), 1),
        'wa_group':    int(contact),
        'cp_wa':       round(safe_div(spend, contact), 2),
        'form_thanks': int(wishlist),
        'cp_form':     round(safe_div(spend, wishlist), 2),
    }

INS_FIELDS = ('spend,impressions,clicks,reach,ctr,cpc,cpm,actions,'
              'video_p25_watched_actions,video_p50_watched_actions,'
              'video_p75_watched_actions,video_p100_watched_actions')

# ─── 1. Account info ──────────────────────────────────────────────────────────
print("1/6 Account info...")
acct = get(f"{BASE}/{ACCT}", {'fields': 'name,currency,account_status'})
print(f"   {acct.get('name')} | {acct.get('currency')}")

# ─── 2. Account daily + summary ───────────────────────────────────────────────
print("2/6 Daily account insights...")
raw_daily = get(f"{BASE}/{ACCT}/insights", {
    'fields': INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'time_increment': 1, 'level': 'account', 'limit': 10,
}).get('data', [])

raw_sum = get(f"{BASE}/{ACCT}/insights", {
    'fields': INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'account',
}).get('data', [{}])

# ── DIAGNOSTICS: print every action type returned by the API ──────────────────
all_acts = (raw_sum[0] if raw_sum else {}).get('actions', [])
if all_acts:
    print("   [DIAG] Todos action_types retornados pelo API (summary):")
    for a in sorted(all_acts, key=lambda x: -float(x.get('value', 0))):
        print(f"     {a['action_type']:60s}  value={a.get('value','?')}")
else:
    print("   [DIAG] Nenhuma action retornada no summary.")

# ── Build WA action name: look for best match ─────────────────────────────────
# Priority: onsite_conversion.messaging_* > contact > any with 'whatsapp'
WA_CANDIDATES = [
    'onsite_conversion.messaging_conversation_started_7d',
    'onsite_conversion.messaging_first_reply',
    'contact',
    'onsite_conversion.contact',
]
act_types_available = {a['action_type'] for a in all_acts}
wa_action = 'contact'  # default
for candidate in WA_CANDIDATES:
    if candidate in act_types_available:
        wa_action = candidate
        break
print(f"   [DIAG] WA action escolhida: {wa_action}")

# Also check in daily rows for any messaging action types
for dr in raw_daily:
    for a in dr.get('actions', []):
        if 'messaging' in a['action_type'] or 'whatsapp' in a['action_type'].lower():
            print(f"   [DIAG] Found in daily: {a['action_type']} = {a.get('value','?')}")
            wa_action = a['action_type']

# ── Build daily array (fill all 7 days, 0 for days with no spend) ─────────────
all_dates = []
for i in range(7):
    d = (now - timedelta(days=6-i)).strftime("%Y-%m-%d")
    all_dates.append(d)

daily_by_date = {d.get('date_start', ''): d for d in raw_daily}
daily = []
for date in all_dates:
    if date in daily_by_date:
        row = proc(daily_by_date[date], wa_action)
        row['date'] = date
    else:
        row = {'date': date, 'spend': 0, 'impressions': 0, 'clicks': 0,
               'reach': 0, 'leads': 0, 'ctr': 0, 'cpc': 0, 'cpm': 0,
               'cpl': 0, 'lp_conv': 0, 'hook_rate': 0,
               'vp25': 0, 'vp50': 0, 'vp75': 0, 'vp100': 0,
               'wa_group': 0, 'cp_wa': 0, 'form_thanks': 0, 'cp_form': 0}
    daily.append(row)

summary = proc(raw_sum[0] if raw_sum else {}, wa_action)
print(f"   Gasto 7d: R$ {summary['spend']} | Leads: {summary['leads']} | WA: {summary['wa_group']} | Forms: {summary['form_thanks']}")

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

camp_daily_map = defaultdict(dict)
for d in camp_daily_raw:
    cid  = d.get('campaign_id', '')
    date = d.get('date_start', '')
    row  = proc(d, wa_action); row['date'] = date
    camp_daily_map[cid][date] = row

# Get statuses
status_map = {}
camp_status_raw = get(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,effective_status', 'limit': 200,
}).get('data', [])
for c in camp_status_raw:
    status_map[c['id']] = c.get('effective_status', '?')

campaigns = []
seen_camps = set()
for d in camp_7d:
    cid = d.get('campaign_id', '')
    if cid in seen_camps:
        print(f"   ⚠ campanha duplicada ignorada: {cid}")
        continue
    seen_camps.add(cid)
    row = proc(d, wa_action)
    row['id']     = cid
    row['name']   = d.get('campaign_name', '')
    row['status'] = status_map.get(cid, '?')
    # Fill all 7 days for this campaign too
    camp_days = []
    for date in all_dates:
        if date in camp_daily_map[cid]:
            camp_days.append(camp_daily_map[cid][date])
        else:
            camp_days.append({'date': date, 'spend': 0, 'leads': 0, 'ctr': 0,
                              'lp_conv': 0, 'cpm': 0, 'impressions': 0,
                              'wa_group': 0, 'form_thanks': 0, 'cpl': 0})
    row['daily'] = camp_days
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
seen_ads = set()
for d in ad_7d:
    aid = d.get('ad_id', '')
    if aid in seen_ads:
        print(f"   ⚠ ad duplicado ignorado: {aid}")
        continue
    seen_ads.add(aid)
    row = proc(d, wa_action)
    row.update({
        'id':            aid,
        'name':          d.get('ad_name', ''),
        'campaign_id':   d.get('campaign_id', ''),
        'campaign_name': d.get('campaign_name', ''),
        'adset_name':    d.get('adset_name', ''),
        'thumbnail':     '',
        'video_id':      '',
    })

    time.sleep(0.1)
    cr = get(f"{BASE}/{aid}", {'fields': 'creative{thumbnail_url,video_id}'})
    creative  = cr.get('creative', {})
    thumb_url = creative.get('thumbnail_url', '')
    video_id  = creative.get('video_id', '')
    row['video_id'] = video_id or ''

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

# ─── 6. Integrity check + Save JSON ───────────────────────────────────────────
print("6/6 Salvando JSON...")

camp_ids  = [c['id'] for c in campaigns]
ad_ids    = [a['id'] for a in ads]
dupes = []
if len(camp_ids) != len(set(camp_ids)): dupes.append('campanhas')
if len(ad_ids)   != len(set(ad_ids)):   dupes.append('ads')
if dupes:
    print(f"   ⚠ DUPLICIDADE DETECTADA em: {', '.join(dupes)}")
else:
    active_days  = [d for d in daily if d['spend'] > 0]
    daily_sum    = round(sum(d['spend'] for d in active_days), 2)
    delta        = abs(daily_sum - summary['spend'])
    status_emoji = '✅' if delta <= 0.05 else '⚠'
    print(f"   {status_emoji} daily_sum={daily_sum} | summary={summary['spend']} | WA={summary['wa_group']} | Forms={summary['form_thanks']}")

data = {
    'last_updated':  now.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'account':       {'id': ACCT, 'name': acct.get('name', 'DevSpace'),
                      'currency': acct.get('currency', 'BRL')},
    'date_range':    {'since': SINCE, 'until': UNTIL},
    'wa_action':     wa_action,
    'summary':       summary,
    'daily':         daily,
    'campaigns':     campaigns,
    'ads':           ads,
}
with open('docs/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n✅ docs/data.json salvo")
print(f"   {len(campaigns)} campanhas | {len(ads)} ads | {len(daily)} dias (7 fixos)")
print(f"   Gasto 7d: {acct.get('currency','BRL')} {summary['spend']} | Leads: {summary['leads']} | CPL: {summary['cpl']}")
