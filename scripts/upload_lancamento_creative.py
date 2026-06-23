import requests, os, json, sys

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"

# Get page token
pg_r = requests.get(f"{BASE}/110278364765662", params={
    'access_token':TOKEN, 'fields':'access_token'
}, timeout=30).json()
PAGE_TOKEN = pg_r.get('access_token')
print(f"## PAGE_TOKEN_OK: {PAGE_TOKEN is not None}", flush=True)

# Hardcoded list of posts (embedded from seed)
POSTS = [
    {"eosi":"110278364765662_1034974682379637","ad_name":"img6623","adset":"[AD SET ] - [novos videos] — Cópia","leads":"4","spend":"16.95"},
    {"eosi":"110278364765662_1034974602379645","ad_name":"img6627","adset":"[AD SET ] - [novos videos]","leads":"2","spend":"13.12"},
    {"eosi":"110278364765662_1034974482379657","ad_name":"img6628","adset":"[AD SET ] - [novos videos]","leads":"1","spend":"11.10"},
    {"eosi":"110278364765662_1034974462379659","ad_name":"img6629","adset":"[AD SET ] - [novos videos]","leads":"1","spend":"11.64"},
    {"eosi":"110278364765662_1034974615712977","ad_name":"img6630","adset":"[AD SET ] - [novos videos]","leads":"6","spend":"17.70"},
    {"eosi":"110278364765662_1000476912496081","ad_name":"img5360","adset":"[AD SET 1.19] - [vd-teste]","leads":"24","spend":"126.48"},
    {"eosi":"110278364765662_1000476642496108","ad_name":"img5359","adset":"[AD SET 1.18] - [vd-teste]","leads":"5","spend":"27.96"},
    {"eosi":"110278364765662_1000476952496077","ad_name":"img5326","adset":"[AD SET 1.17] - [vd-teste]","leads":"1","spend":"10.83"},
    {"eosi":"110278364765662_1000476839162755","ad_name":"img5325","adset":"[AD SET 1.16] - [vd-teste]","leads":"0","spend":"7.47"},
    {"eosi":"110278364765662_1000476869162752","ad_name":"img5322","adset":"[AD SET 1.15] - [vd-teste]","leads":"0","spend":"6.81"},
    {"eosi":"110278364765662_1000476739162765","ad_name":"img5321","adset":"[AD SET 1.14] - [vd-teste]","leads":"0","spend":"5.17"},
    {"eosi":"110278364765662_1000476979162741","ad_name":"img5320","adset":"[AD SET 1.13] - [vd-teste]","leads":"0","spend":"8.24"},
    {"eosi":"110278364765662_1000476682496104","ad_name":"img5319","adset":"[AD SET 1.12] - [vd-teste]","leads":"1","spend":"6.43"},
    {"eosi":"110278364765662_996847462859026","ad_name":"remold_nativo_story","adset":"[AD SET 1.11] - [REMOLD ADAPTA] +[story]","leads":"0","spend":"8.66"},
    {"eosi":"110278364765662_987056023838170","ad_name":"[framework_remold] — Cópia","adset":"[AD SET 1.10] - [REMOLD] 2 ESTÁTICO","leads":"9","spend":"45.85"},
    {"eosi":"110278364765662_964896589387447","ad_name":"[NBP01VD]","adset":"[AD SET 1.9] - [SÓ VIDEO]","leads":"1","spend":"12.09"},
    {"eosi":"110278364765662_964896626054110","ad_name":"[NBP03VD]","adset":"[AD SET 1.8] - [SÓ VIDEO]","leads":"2","spend":"12.22"},
    {"eosi":"110278364765662_967561635787609","ad_name":"[MDL3]","adset":"[AD SET 1.6] - [ESTÁTICO MODELADO]  [TESTE]","leads":"1","spend":"10.60"},
    {"eosi":"110278364765662_964150126128760","ad_name":"[MDL1]","adset":"[AD SET 1.5] - [ESTÁTICO $1EUR  [TESTE]","leads":"0","spend":"0.16"},
    {"eosi":"110278364765662_964149896128783","ad_name":"[MDL2]","adset":"[AD SET 1.5] - [ESTÁTICO $1EUR  [TESTE]","leads":"1","spend":"11.71"},
    {"eosi":"110278364765662_964150066128766","ad_name":"[AD02]","adset":"[AD SET 1.3] - [E_AD02]  + [VD01] [TESTE]","leads":"0","spend":"6.54"},
    {"eosi":"110278364765662_964896626054110","ad_name":"[NBP03VD]","adset":"[AD SET 1.3] - [E_AD02]  + [VD01] [TESTE]","leads":"0","spend":"2.04"},
    {"eosi":"110278364765662_964896582720781","ad_name":"[NBP02VD]","adset":"[AD SET 1.2 alterado dia 12] - [E_AD03] - [v\VIDEO ATIVO P TESTE]","leads":"16","spend":"93.00"},
    {"eosi":"110278364765662_964150049462101","ad_name":"[AD05]","adset":"[AD SET 1.1] - [E_AD05]","leads":"0","spend":"10.31"},
]
print(f"## POSTS: {len(POSTS)}", flush=True)
print("## CSVSTART", flush=True)
print("post_id|ad_name|adset|leads|spend|comments|likes|love|haha|wow|sorry|anger|shares|post_url", flush=True)

for p in POSTS:
    eosi = p['eosi']
    try:
        # comments count
        cr = requests.get(f"{BASE}/{eosi}/comments", params={
            'summary':'true','filter':'stream','limit':0,'access_token':PAGE_TOKEN
        }, timeout=15).json()
        comments_count = cr.get('summary',{}).get('total_count', 0)
        
        # reactions total
        lr = requests.get(f"{BASE}/{eosi}/reactions", params={
            'summary':'true','limit':0,'access_token':PAGE_TOKEN
        }, timeout=15).json()
        likes_count = lr.get('summary',{}).get('total_count', 0)
        
        # by type
        reactions = {}
        for rt in ['LOVE','HAHA','WOW','SORRY','ANGER']:
            rr = requests.get(f"{BASE}/{eosi}/reactions", params={
                'summary':'true','type':rt,'limit':0,'access_token':PAGE_TOKEN
            }, timeout=15).json()
            reactions[rt] = rr.get('summary',{}).get('total_count', 0)
        
        # shares
        shares = 0
        try:
            pr = requests.get(f"{BASE}/{eosi}", params={
                'fields':'shares','access_token':PAGE_TOKEN
            }, timeout=15).json()
            shares = pr.get('shares',{}).get('count', 0)
        except: pass
        
        page_id, post_id = eosi.split('_', 1)
        url = f"https://www.facebook.com/{page_id}/posts/{post_id}"
        print(f"{eosi}|{p['ad_name']}|{p['adset']}|{p['leads']}|{p['spend']}|"
              f"{comments_count}|{likes_count}|{reactions.get('LOVE',0)}|{reactions.get('HAHA',0)}|"
              f"{reactions.get('WOW',0)}|{reactions.get('SORRY',0)}|{reactions.get('ANGER',0)}|"
              f"{shares}|{url}", flush=True)
    except Exception as e:
        print(f"## ERR {eosi}: {e}", flush=True)
print("## CSVEND", flush=True)
