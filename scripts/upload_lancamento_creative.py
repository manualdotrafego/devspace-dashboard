import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"  # Mafra Lancamento
BASE_URL = "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/"

VIDEOS = [
    ("IMG_5678", "IMG_5678.MOV"),
    ("IMG_5679", "IMG_5679.MOV"),
]

results = []
for label, fname in VIDEOS:
    url = BASE_URL + fname
    print(f"\n=== {label} -> file_url upload ===")
    print(f"  url: {url[:90]}...")
    
    up = requests.post(f"{ACCT.split(':')[0] and BASE + '/' + ACCT}/advideos", data={
        'file_url': url,
        'name': label,
        'access_token': TOKEN
    }, timeout=300)
    resp = up.json()
    print(f"  resp: {json.dumps(resp, indent=2)}")
    if 'id' in resp:
        vid = resp['id']
        results.append({'label': label, 'video_id': vid})
        
        # Wait for processing
        print(f"  aguardando processamento...")
        for i in range(30):
            time.sleep(5)
            st = requests.get(f"{BASE}/{vid}", params={
                'fields': 'status',
                'access_token': TOKEN
            }, timeout=30).json()
            phase = st.get('status',{}).get('video_status','?')
            print(f"     [{i+1}] video_status={phase}")
            if phase == 'ready':
                print(f"     OK pronto!")
                break
            if phase == 'error':
                print(f"     FAILED: {st}")
                break
    time.sleep(1)

print(f"\n=== RESUMO ===")
print(f"Conta: {ACCT} (Mafra Lancamento)")
for r in results:
    print(f"  {r['label']} -> video_id: {r['video_id']}")
