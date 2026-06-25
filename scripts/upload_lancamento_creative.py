import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

r = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend,impressions,clicks,actions',
    'time_range': json.dumps({'since':'2026-06-17','until':'2026-06-23'}),
    'access_token':TOKEN
}, timeout=30)
d = r.json().get('data', [{}])[0]

# Extract ALL action types to see the full funnel
print("## ALL_ACTIONS")
for act in d.get('actions', []):
    print(f"  {act.get('action_type')}: {act.get('value')}")

# Key funnel metrics
clicks_all = int(d.get('clicks', 0))
link_clicks = lp_views = leads = 0
for act in d.get('actions', []):
    t = act.get('action_type','')
    v = int(act.get('value', 0))
    if t == 'link_click': link_clicks = v
    elif t == 'landing_page_view': lp_views = v
    elif t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
        leads = max(leads, v)

print("\n## FUNNEL")
print(f"clicks_all={clicks_all}")
print(f"link_clicks={link_clicks}")
print(f"lp_views={lp_views}")
print(f"leads={leads}")
# rates
print(f"\n## RATES")
print(f"click_to_lp={lp_views/link_clicks*100 if link_clicks else 0:.1f}")
print(f"lp_to_lead={leads/lp_views*100 if lp_views else 0:.1f}")
print(f"click_to_lead={leads/link_clicks*100 if link_clicks else 0:.1f}")
# perda absoluta
print(f"\n## PERDAS")
print(f"perdidos_click_to_lp={link_clicks - lp_views}")
print(f"perdidos_lp_to_lead={lp_views - leads}")
print("## END")
