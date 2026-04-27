import requests, os, time, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"   # CA - João Mafra lançamento

# GitHub Release URL (estável) — o script resolve o redirect em runtime
GH_URL  = "https://github.com/manualdotrafego/Contas-de-anuncio/releases/download/lancamento-creatives-v1/Depoimentos.Compilado.mp4"
AD_NAME = "depoimentos-compilado"

def get_cdn_url(gh_url):
    """Resolve o redirect do GitHub para pegar a URL direta do CDN."""
    r = requests.head(gh_url, allow_redirects=False, timeout=30)
    cdn = r.headers.get('location', '')
    if cdn:
        print(f"  ✅ CDN URL resolvida: {cdn[:80]}...")
        return cdn
    print(f"  ⚠️  Sem redirect, usando URL original")
    return gh_url

def upload_via_file_url(name, cdn_url):
    """Tenta upload via file_url (Meta baixa do CDN)."""
    print(f"\n  [file_url] Enviando '{name}'...")
    r = requests.post(
        f"{BASE}/{ACCT}/advideos",
        data={
            'access_token': TOKEN,
            'name': name,
            'file_url': cdn_url,
        },
        timeout=60
    )
    if r.ok:
        data = r.json()
        vid_id = data.get('id') or data.get('video_id')
        if vid_id:
            print(f"  ✅ Upload iniciado! video_id: {vid_id}")
            return vid_id
    print(f"  ERR {r.status_code}: {r.text[:400]}")
    return None

def upload_multipart(name, gh_url):
    """Fallback: baixa o arquivo localmente e faz upload multipart."""
    print(f"\n  [multipart] Baixando '{name}' localmente (~626MB)...")
    tmp = f"/tmp/{name}.mp4"
    with requests.get(gh_url, stream=True, timeout=600) as dl:
        dl.raise_for_status()
        total = int(dl.headers.get('content-length', 0))
        done  = 0
        with open(tmp, 'wb') as f:
            for chunk in dl.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct = done / total * 100
                    if done % (50*1024*1024) < 1024*1024:
                        print(f"    {pct:.0f}% ({done//1024//1024}MB/{total//1024//1024}MB)")
    print(f"  Download concluído ({done//1024//1024}MB). Iniciando upload Meta...")
    with open(tmp, 'rb') as f:
        r = requests.post(
            f"{BASE}/{ACCT}/advideos",
            data={'access_token': TOKEN, 'name': name},
            files={'source': (f"{name}.mp4", f, 'video/mp4')},
            timeout=600
        )
    if r.ok:
        data = r.json()
        vid_id = data.get('id') or data.get('video_id')
        if vid_id:
            print(f"  ✅ Upload multipart concluído! video_id: {vid_id}")
            return vid_id
    print(f"  ERR {r.status_code}: {r.text[:400]}")
    return None

def wait_video_ready(vid_id, max_wait=300):
    """Aguarda o vídeo terminar de processar."""
    print(f"\n  Aguardando processamento do vídeo {vid_id}...")
    for i in range(max_wait // 10):
        time.sleep(10)
        r = requests.get(
            f"{BASE}/{vid_id}",
            params={'access_token': TOKEN, 'fields': 'id,status,title,picture,length'}
        )
        if r.ok:
            d = r.json()
            status = d.get('status', {})
            pstatus = status.get('processing_progress', status) if isinstance(status, dict) else status
            vstatus = d.get('status', {}).get('video_status', '?') if isinstance(d.get('status'), dict) else d.get('status','?')
            print(f"    [{i*10+10}s] status: {vstatus} | progress: {pstatus}")
            if vstatus in ('ready', 'READY', 'LIVE'):
                print(f"  ✅ Vídeo pronto!")
                return True
    print(f"  ⚠️  Timeout aguardando vídeo. Pode ainda estar processando.")
    return False

# ─── MAIN ─────────────────────────────────────────────────────────────────────
print("="*65)
print(f"UPLOAD CRIATIVO — {ACCT}")
print(f"Arquivo: Depoimentos Compilado.mp4 (~626MB)")
print("="*65)

# 1. Resolver CDN URL
cdn_url = get_cdn_url(GH_URL)

# 2. Tentar upload via file_url
vid_id = upload_via_file_url(AD_NAME, cdn_url)

# 3. Fallback multipart se file_url falhar
if not vid_id:
    print("\n  file_url falhou. Tentando upload multipart...")
    vid_id = upload_multipart(AD_NAME, GH_URL)

# 4. Resultado
print("\n" + "="*65)
if vid_id:
    print(f"✅ SUCESSO! video_id: {vid_id}")
    print(f"   Conta: {ACCT}")
    print(f"   Nome: {AD_NAME}")
    wait_video_ready(vid_id)
    print(f"\n   Use este video_id ao criar anúncio:")
    print(f"   video_id = {vid_id}")
else:
    print("❌ FALHA no upload. Verifique os erros acima.")
print("="*65)
