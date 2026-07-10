import requests, os, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
CAMPS=["120248546729160002","120254908221730002","120255355949960002"]
TARGETS={"estrategia_escala_servico","tela_escala_servico"}

print("=== PAUSAR criativos sem lead (ciclo 16) ===\n")
paused=[]
for cid in CAMPS:
    r=requests.get(f"{BASE}/{cid}/ads",params={
        'fields':'id,name,effective_status','limit':100,'access_token':TOKEN},timeout=40).json()
    for ad in r.get('data',[]):
        nm=ad.get('name','').strip()
        if nm in TARGETS and ad.get('effective_status')=='ACTIVE':
            pr=requests.post(f"{BASE}/{ad['id']}",data={'status':'PAUSED','access_token':TOKEN},timeout=30).json()
            ok=pr.get('success',False)
            print(f"  {'✅' if ok else '❌'} {nm} (ad {ad['id']}) -> {pr}")
            if ok: paused.append(nm)
            time.sleep(0.3)

print(f"\n=== Verificação ===")
for cid in CAMPS:
    r=requests.get(f"{BASE}/{cid}/ads",params={
        'fields':'name,effective_status','limit':100,'access_token':TOKEN},timeout=40).json()
    for ad in r.get('data',[]):
        if ad.get('name','').strip() in TARGETS:
            print(f"  {ad['name']}: {ad['effective_status']}")

print(f"\n=== Anúncios ATIVOS restantes (todas 3 campanhas) ===")
for cid in CAMPS:
    r=requests.get(f"{BASE}/{cid}/ads",params={
        'fields':'name,effective_status','limit':100,'access_token':TOKEN},timeout=40).json()
    for ad in r.get('data',[]):
        if ad.get('effective_status')=='ACTIVE':
            print(f"  🟢 {ad['name']}")
