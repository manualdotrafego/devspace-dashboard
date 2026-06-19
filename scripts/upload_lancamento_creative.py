import requests, os, json
TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"  # Joao Mafra Lancamento (EUR)

def fetch(since, until, label, level='account'):
    r = requests.get(f"{BASE}/{ACCT}/insights", params={
        'fields': 'spend,impressions,clicks,actions,cpm,cpc,ctr,reach',
        'time_range': json.dumps({'since': since, 'until': until}),
        'level': level,
        'access_token': TOKEN
    }, timeout=30)
    data = r.json().get('data', [])
    if not data:
        print(f"  sem dados"); return None
    d = data[0]
    spend = float(d.get('spend', 0))
    leads = link_clicks = lp_views = 0
    for act in d.get('actions', []):
        t = act.get('action_type','')
        v = int(act.get('value', 0))
        if t in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
            leads = max(leads, v)
        elif t == 'link_click': link_clicks = v
        elif t == 'landing_page_view': lp_views = v
    cpl = spend/leads if leads > 0 else 0
    print(f"\n--- {label} ({since} -> {until}) ---")
    print(f"  Gasto:       €{spend:>10,.2f}")
    print(f"  Leads:       {leads:>12,}")
    print(f"  CPL:         €{cpl:>10,.2f}")
    print(f"  Impressoes:  {int(d.get('impressions',0)):>12,}")
    print(f"  Reach:       {int(d.get('reach',0)):>12,}")
    print(f"  Clicks:      {int(d.get('clicks',0)):>12,} | LinkClicks: {link_clicks:,} | LP: {lp_views:,}")
    print(f"  CTR/CPC/CPM: {float(d.get('ctr',0)):.2f}% / €{float(d.get('cpc',0)):.2f} / €{float(d.get('cpm',0)):.2f}")
    return d

def fetch_camp_breakdown(since, until, label):
    r = requests.get(f"{BASE}/{ACCT}/insights", params={
        'fields': 'spend,impressions,actions,campaign_name',
        'time_range': json.dumps({'since': since, 'until': until}),
        'level': 'campaign',
        'limit': 50,
        'access_token': TOKEN
    }, timeout=30)
    data = r.json().get('data', [])
    if not data: return
    print(f"\n>> Breakdown por campanha ({label}):")
    rows = []
    for d in data:
        sp = float(d.get('spend', 0))
        lds = 0
        for act in d.get('actions', []):
            if act.get('action_type') in ('onsite_conversion.lead_grouped','lead','offsite_conversion.fb_pixel_lead','onsite_web_lead'):
                lds = max(lds, int(act.get('value', 0)))
        rows.append((sp, lds, d.get('campaign_name','')))
    rows.sort(reverse=True)
    for sp, lds, nm in rows:
        if sp > 0:
            cpl = sp/lds if lds > 0 else 0
            cpl_str = f"€{cpl:.2f}" if lds > 0 else "—"
            print(f"   €{sp:>8.2f}  {lds:>4} leads  CPL {cpl_str:>7}  | {nm[:55]}")

print("=" * 70)
print("  GASTO MENSAL — Joao Mafra Lancamento (EUR)")
print("=" * 70)

fetch("2026-05-01", "2026-05-31", "MAIO 2026 (mes completo)")
fetch_camp_breakdown("2026-05-01", "2026-05-31", "Maio")

fetch("2026-06-01", "2026-06-12", "JUNHO 2026 (ate hoje, 12/jun)")
fetch_camp_breakdown("2026-06-01", "2026-06-12", "Junho")
