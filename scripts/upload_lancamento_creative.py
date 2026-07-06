import requests, os, json, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"
URL="https://github.com/manualdotrafego/devspace-dashboard/releases/download/webnar-3006-v1/"
VIDEOS=[("estrategia_escala_servico","estrategia_escala_servico.mp4"),
        ("tela_escala_servico","tela_escala_servico.mp4")]
for label,fname in VIDEOS:
    print(f"\n=== {label} ===", flush=True)
    r=requests.post(f"{BASE}/{ACCT}/advideos",data={
        'file_url':URL+fname,'name':label,'access_token':TOKEN},timeout=300).json()
    vid=r.get('id')
    if not vid: print(f"  ERRO: {r}",flush=True); continue
    print(f"  video_id={vid}",flush=True)
    for i in range(60):
        time.sleep(8)
        st=requests.get(f"{BASE}/{vid}",params={'fields':'status','access_token':TOKEN},timeout=30).json()
        ph=st.get('status',{}).get('video_status','?')
        if ph=='ready': print(f"  ✅ ready",flush=True); break
        if ph=='error': print(f"  ❌ {st}",flush=True); break
