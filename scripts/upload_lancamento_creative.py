import requests, os, json
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
IG_USER="17841401176393733"  # IG @joaomafra (visto nos creatives)
MEDIA_ID="3942512571457372168"
SHORTCODE="Da2nkugOoAI"

# page token (mais permissoes para IG)
pg=requests.get(f"{BASE}/110278364765662",params={'access_token':TOKEN,'fields':'access_token'},timeout=30).json()
PT=pg.get('access_token', TOKEN)

# 1. Verificacao direta do media id
r=requests.get(f"{BASE}/{MEDIA_ID}",params={'fields':'id,permalink,media_type,caption','access_token':PT},timeout=30).json()
print("## Direto:", json.dumps(r, ensure_ascii=False)[:300])

# 2. Fallback: listar midias do IG user e achar pelo shortcode
if 'error' in r:
    url=f"{BASE}/{IG_USER}/media"
    params={'fields':'id,permalink,media_type,timestamp','limit':50,'access_token':PT}
    found=False
    for page in range(6):
        d=requests.get(url,params=params,timeout=30).json()
        if 'error' in d:
            print("## Lista erro:", d['error'].get('message','')[:150]); break
        for m in d.get('data',[]):
            if SHORTCODE in (m.get('permalink') or ''):
                print("## ENCONTRADO via lista:", json.dumps(m, ensure_ascii=False))
                found=True; break
        if found: break
        url=d.get('paging',{}).get('next','')
        params={}
        if not url: break
    if not found: print("## nao encontrado na lista")
