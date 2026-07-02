import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"  # Joao Mafra Lancamento
BASEURL = "https://github.com/manualdotrafego/devspace-dashboard/releases/download/webnar-3006-v1/"

VIDEOS = [
    ("escalar_no_digital", "escalar_no_digital.mp4"),
    ("voce_e_agencia", "voce_e_agencia.mp4"),
    ("voce_mentor", "voce_mentor.mp4"),
    ("voce_freelancer", "voce_freelancer.mp4"),
    ("pergunta_escalar_servico", "pergunta_escalar_servico.mp4"),
    ("pergunta_parar_vender_horas", "pergunta_parar_vender_horas.mp4"),
    ("dono_de_agencia", "dono_de_agencia.mp4"),
]

results = []
for label, fname in VIDEOS:
    url = BASEURL + fname
    print(f"\n=== {label} ===", flush=True)
    up = requests.post(f"{BASE}/{ACCT}/advideos", data={
        'file_url': url, 'name': label, 'access_token': TOKEN
    }, timeout=300)
    resp = up.json()
    vid = resp.get('id')
    if not vid:
        print(f"  ERRO: {resp}", flush=True); continue
    print(f"  video_id={vid} — aguardando processamento...", flush=True)
    for i in range(40):
        time.sleep(6)
        st = requests.get(f"{BASE}/{vid}", params={'fields':'status','access_token':TOKEN}, timeout=30).json()
        ph = st.get('status',{}).get('video_status','?')
        if ph == 'ready':
            print(f"  ✅ ready", flush=True); break
        if ph == 'error':
            print(f"  ❌ FAILED: {st}", flush=True); break
    results.append((label, vid))

print(f"\n=== RESUMO ({len(results)}/7) — conta {ACCT} ===")
for lbl,vid in results:
    print(f"  {lbl:<30} video_id={vid}")
