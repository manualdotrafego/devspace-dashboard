import requests, json, os, time
from datetime import datetime, timedelta, timezone, date as date_cls
from collections import defaultdict
import urllib.request

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"   # DevSpace

now   = datetime.now(timezone.utc)
UNTIL = now.strftime("%Y-%m-%d")

os.makedirs("docs/thumbnails", exist_ok=True)

# ── Lead extraction: priority-based to avoid double-counting ──────────────────
LEAD_PRIORITY = [
    'onsite_conversion.lead_grouped',   # Ads Manager standard (OUTCOME_LEADS)
    'lead',                             # Universal native form leads
    'offsite_conversion.fb_pixel_lead', # Pixel-based leads (fallback)
    'onsite_web_lead',                  # Outcome leads specific
]

WA_ACTION   = 'omni_initiated_checkout'  # Entrou Grupo do WA
FORM_ACTION = 'add_to_wishlist'          # Clicou forms pág. obrigado

CAMP_KEYWORD = '0 ao emprego'           # Filter: only campaigns containing this

# ── Helpers ────────────────────────────────────────────────────────────────────
def get(url, params=None):
    p = dict(params or {}); p['access_token'] = TOKEN
    r = requests.get(url, params=p, timeout=30)
    if not r.ok:
        print(f"  ERR {r.status_code}: {r.text[:200]}")
        return {}
    return r.json()

def paginate(url, params=None, max_pages=30):
    results, page, data = [], 0, get(url, params)
    results.extend(data.get('data', []))
    while data.get('paging', {}).get('next') and page < max_pages:
        time.sleep(0.2)
        data = get(data['paging']['next'])
        results.extend(data.get('data', []))
        page += 1
    return results

def extract_leads(actions):
    acts = actions or []
    for atype in LEAD_PRIORITY:
        val = sum(float(a.get('value', 0)) for a in acts if a.get('action_type') == atype)
        if val > 0:
            return val
    return 0

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

def proc(d):
    spend  = float(d.get('spend', 0))
    impr   = int(d.get('impressions', 0))
    clicks = int(d.get('clicks', 0))
    reach  = int(d.get('reach', 0))
    acts   = d.get('actions', [])
    leads  = extract_leads(acts)
    vviews = extract_video_views(acts)
    contact  = extract_action(acts, WA_ACTION)
    wishlist = extract_action(acts, FORM_ACTION)
    p25  = extract_arr(d.get('video_p25_watched_actions',  []))
    p50  = extract_arr(d.get('video_p50_watched_actions',  []))
    p75  = extract_arr(d.get('video_p75_watched_actions',  []))
    p100 = extract_arr(d.get('video_p100_watched_actions', []))
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
        'vp25':        round(safe_div(p25,  impr, 100), 1),
        'vp50':        round(safe_div(p50,  impr, 100), 1),
        'vp75':        round(safe_div(p75,  impr, 100), 1),
        'vp100':       round(safe_div(p100, impr, 100), 1),
        'wa_group':    int(contact),
        'cp_wa':       round(safe_div(spend, contact), 2),
        'form_thanks': int(wishlist),
        'cp_form':     round(safe_div(spend, wishlist), 2),
    }

def empty_day(date_str):
    return {'date': date_str, 'spend': 0, 'impressions': 0, 'clicks': 0,
            'reach': 0, 'leads': 0, 'ctr': 0, 'cpc': 0, 'cpm': 0,
            'cpl': 0, 'lp_conv': 0, 'hook_rate': 0,
            'vp25': 0, 'vp50': 0, 'vp75': 0, 'vp100': 0,
            'wa_group': 0, 'cp_wa': 0, 'form_thanks': 0, 'cp_form': 0}

INS_FIELDS = ('spend,impressions,clicks,reach,ctr,cpc,cpm,actions,'
              'video_p25_watched_actions,video_p50_watched_actions,'
              'video_p75_watched_actions,video_p100_watched_actions')

# ─── 0. Account info ──────────────────────────────────────────────────────────
print("0/6 Account info...")
acct = get(f"{BASE}/{ACCT}", {'fields': 'name,currency,account_status'})
print(f"   {acct.get('name')} | {acct.get('currency')}")

# ─── 1. Find target campaigns (containing CAMP_KEYWORD) ───────────────────────
print(f"1/6 Buscando campanhas com '{CAMP_KEYWORD}'...")
all_camps_meta = paginate(f"{BASE}/{ACCT}/campaigns", {
    'fields': 'id,name,start_time,effective_status',
    'limit': 200,
})

target_camps = [c for c in all_camps_meta
                if CAMP_KEYWORD.lower() in c.get('name', '').lower()]

if not target_camps:
    print(f"   ⚠ Nenhuma campanha com '{CAMP_KEYWORD}' encontrada! Usando todas.")
    target_camp_ids = None  # fallback: no filter
    SINCE = (now - timedelta(days=6)).strftime("%Y-%m-%d")
else:
    target_camp_ids = [c['id'] for c in target_camps]
    # SINCE = earliest campaign start date
    start_dates = [c['start_time'][:10] for c in target_camps if c.get('start_time')]
    SINCE = min(start_dates) if start_dates else (now - timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"   {len(target_camps)} campanha(s) | Desde: {SINCE} → {UNTIL}")
    for c in target_camps:
        print(f"   [{c.get('effective_status','?')[:8]}] {c['name'][:80]}")

# Build filtering clause for insights queries
if target_camp_ids:
    CAMP_FILTER = json.dumps([{"field": "campaign.id", "operator": "IN",
                               "value": target_camp_ids}])
else:
    CAMP_FILTER = json.dumps([{"field": "spend", "operator": "GREATER_THAN", "value": 0}])

# Build full date list from SINCE to UNTIL (all days, no gaps)
since_date = date_cls.fromisoformat(SINCE)
until_date = date_cls.fromisoformat(UNTIL)
all_dates = []
d = since_date
while d <= until_date:
    all_dates.append(d.isoformat())
    d += timedelta(days=1)
print(f"   Janela: {len(all_dates)} dias ({SINCE} → {UNTIL})")

# ─── 2. Account daily + summary ───────────────────────────────────────────────
print("2/6 Daily insights (lifetime)...")
raw_daily = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'time_increment': 1, 'level': 'account',
    'filtering': CAMP_FILTER,
    'limit': 100,
})

raw_sum = get(f"{BASE}/{ACCT}/insights", {
    'fields': INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'account',
    'filtering': CAMP_FILTER,
}).get('data', [{}])

# Fill all dates (0 for days without spend)
daily_by_date = {d.get('date_start', ''): d for d in raw_daily}
daily = []
for date in all_dates:
    if date in daily_by_date:
        row = proc(daily_by_date[date]); row['date'] = date
    else:
        row = empty_day(date)
    daily.append(row)

summary = proc(raw_sum[0] if raw_sum else {})
print(f"   Gasto total: R$ {summary['spend']} | Leads: {summary['leads']} | "
      f"WA: {summary['wa_group']} | Forms: {summary['form_thanks']}")

# ─── 3. Campaign insights ─────────────────────────────────────────────────────
print("3/6 Campaign insights...")
camp_sum_raw = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'campaign_id,campaign_name,' + INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'campaign',
    'filtering': CAMP_FILTER,
    'limit': 100,
})

camp_daily_raw = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'campaign_id,' + INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'time_increment': 1, 'level': 'campaign',
    'filtering': CAMP_FILTER,
    'limit': 500,
})

camp_daily_map = defaultdict(dict)
for d in camp_daily_raw:
    cid  = d.get('campaign_id', '')
    date = d.get('date_start', '')
    row  = proc(d); row['date'] = date
    camp_daily_map[cid][date] = row

# Get statuses
status_map = {c['id']: c.get('effective_status', '?') for c in all_camps_meta}

campaigns = []
seen_camps = set()
for d in camp_sum_raw:
    cid = d.get('campaign_id', '')
    if cid in seen_camps:
        print(f"   ⚠ campanha duplicada ignorada: {cid}")
        continue
    seen_camps.add(cid)
    row = proc(d)
    row['id']     = cid
    row['name']   = d.get('campaign_name', '')
    row['status'] = status_map.get(cid, '?')
    # Fill all days
    row['daily'] = [camp_daily_map[cid].get(date, empty_day(date))
                    for date in all_dates]
    campaigns.append(row)
campaigns.sort(key=lambda x: x['spend'], reverse=True)
print(f"   {len(campaigns)} campanhas")

# ─── 4. Ad insights ───────────────────────────────────────────────────────────
print("4/6 Ad insights...")
ad_raw = paginate(f"{BASE}/{ACCT}/insights", {
    'fields': 'ad_id,ad_name,campaign_id,campaign_name,adset_name,' + INS_FIELDS,
    'time_range': json.dumps({'since': SINCE, 'until': UNTIL}),
    'level': 'ad',
    'filtering': CAMP_FILTER,
    'limit': 200,
})
print(f"   {len(ad_raw)} ads com gasto")

# ─── 5. Creative thumbnails ───────────────────────────────────────────────────
print("5/6 Thumbnails...")
ads = []
seen_ads = set()
for d in ad_raw:
    aid = d.get('ad_id', '')
    if aid in seen_ads:
        print(f"   ⚠ ad duplicado ignorado: {aid}")
        continue
    seen_ads.add(aid)
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
            sep    = '&' if '?' in thumb_url else '?'
            dl_url = thumb_url + sep + f'access_token={TOKEN}'
            req    = urllib.request.Request(dl_url, headers={'User-Agent': 'Mozilla/5.0'})
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

camp_ids = [c['id'] for c in campaigns]
ad_ids   = [a['id'] for a in ads]
dupes    = []
if len(camp_ids) != len(set(camp_ids)): dupes.append('campanhas')
if len(ad_ids)   != len(set(ad_ids)):   dupes.append('ads')
if dupes:
    print(f"   ⚠ DUPLICIDADE: {', '.join(dupes)}")
else:
    active_days = [d for d in daily if d['spend'] > 0]
    daily_sum   = round(sum(d['spend'] for d in active_days), 2)
    delta       = abs(daily_sum - summary['spend'])
    emoji       = '✅' if delta <= 0.05 else '⚠'
    print(f"   {emoji} daily_sum={daily_sum} | summary={summary['spend']} | "
          f"WA={summary['wa_group']} | Forms={summary['form_thanks']}")

data = {
    'last_updated':   now.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'account':        {'id': ACCT, 'name': acct.get('name', 'DevSpace'),
                       'currency': acct.get('currency', 'BRL')},
    'date_range':     {'since': SINCE, 'until': UNTIL},
    'camp_filter':    CAMP_KEYWORD,
    'summary':        summary,
    'daily':          daily,
    'campaigns':      campaigns,
    'ads':            ads,
}
with open('docs/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ docs/data.json salvo")
print(f"   {len(campaigns)} campanhas | {len(ads)} ads | {len(daily)} dias")
print(f"   Lifetime: {acct.get('currency','BRL')} {summary['spend']} | "
      f"Leads: {summary['leads']} | CPL: {summary['cpl']}")
