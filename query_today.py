import os
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from datetime import date
import json

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

token      = os.getenv("META_ACCESS_TOKEN")
account_id = os.getenv("META_ACCOUNT_ID")
FacebookAdsApi.init(access_token=token)
account = AdAccount(f"act_{account_id}")

today = date.today().strftime("%Y-%m-%d")

fields = [
    "ad_id", "ad_name", "adset_name", "campaign_name",
    "spend", "impressions", "reach", "inline_link_clicks",
    "inline_link_click_ctr", "cpm",
    "actions", "cost_per_action_type",
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking",
]

params = {
    "level": "ad",
    "time_range": {"since": today, "until": today},
    "limit": 500,
}

rows = list(account.get_insights(fields=fields, params=params))
print(f"Anuncios com dados hoje: {len(rows)}")

WHATSAPP_ACTIONS = [
    "onsite_conversion.messaging_conversation_started_7d",
    "onsite_conversion.total_messaging_connection",
    "onsite_conversion.messaging_first_reply",
]
LEAD_ACTIONS = ["lead", "onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead"]

def extract_action(actions, types):
    if not isinstance(actions, list):
        return 0.0
    for item in actions:
        if item.get("action_type") in types:
            return float(item.get("value", 0))
    return 0.0

def extract_cpa(cpa_list, types):
    if not isinstance(cpa_list, list):
        return None
    for item in cpa_list:
        if item.get("action_type") in types:
            v = float(item.get("value", 0))
            return v if v > 0 else None
    return None

results = []
for r in rows:
    d = dict(r)
    spend  = float(d.get("spend", 0))
    wa     = extract_action(d.get("actions"), WHATSAPP_ACTIONS)
    leads  = extract_action(d.get("actions"), LEAD_ACTIONS)
    result = wa if wa > 0 else leads
    cpr    = (extract_cpa(d.get("cost_per_action_type"), WHATSAPP_ACTIONS) or
              extract_cpa(d.get("cost_per_action_type"), LEAD_ACTIONS))

    results.append({
        "ad_name":      d.get("ad_name"),
        "adset_name":   d.get("adset_name"),
        "campaign_name":d.get("campaign_name"),
        "spend":        spend,
        "resultados":   result,
        "cpr":          cpr,
        "wa_starts":    wa,
        "leads":        leads,
        "impressions":  float(d.get("impressions", 0)),
        "reach":        float(d.get("reach", 0)),
        "link_clicks":  float(d.get("inline_link_clicks", 0)),
        "ctr":          float(d.get("inline_link_click_ctr", 0)),
        "cpm":          float(d.get("cpm", 0)),
        "quality_ranking":         d.get("quality_ranking", ""),
        "engagement_rate_ranking": d.get("engagement_rate_ranking", ""),
        "conversion_rate_ranking": d.get("conversion_rate_ranking", ""),
    })

with_results = [r for r in results if r["resultados"] > 0 and r["cpr"]]
without_results = [r for r in results if r["resultados"] == 0]
with_results.sort(key=lambda x: x["cpr"])

print("\nTOP 2 - MENOR CUSTO POR RESULTADO:")
print(json.dumps(with_results[:2], ensure_ascii=False, indent=2))
print(f"\nAnuncios sem resultado hoje: {len(without_results)}")
