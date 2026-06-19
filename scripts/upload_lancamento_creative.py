import requests, os, json, time

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"  # Joao Mafra Lancamento
BASE_URL = "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/"

VIDEOS = [
    ("IMG_6623", "IMG_6623.MP4"),
    ("IMG_6627", "IMG_6627.MP4"),
    ("IMG_6628", "IMG_6628.MP4"),
    ("IMG_6629", "IMG_6629.MP4"),
    ("IMG_6630", "IMG_6630.MP4"),
]

results = []
for label, fname in VIDEOS:
    url = BASE_URL + fname
    print(f"\n=== {label} -> file_url upload ===")
    print(f"  url: {url[:90]}...")
    
    up = requests.post(f"{BASE}/{ACCT}/advideos", data={
        'file_url': url,
        'name': label,
        'access_token': TOKEN
    }, timeout=600)
    resp = up.json()
    print(f"  resp: {json.dumps(resp, indent=2)}")
    if 'id' in resp:
        vid = resp['id']
        # Wait for processing
        print(f"  aguardando processamento...")
        for i in range(60):
            time.sleep(5)
            st = requests.get(f"{BASE}/{vid}", params={
                'fields': 'status',
                'access_token': TOKEN
            }, timeout=30).json()
            phase = st.get('status',{}).get('video_status','?')
            print(f"     [{i+1}] video_status={phase}")
            if phase == 'ready':
                print(f"     OK pronto!")
                results.append({'label': label, 'video_id': vid, 'status':'ready'})
                break
            if phase == 'error':
                print(f"     FAILED: {st}")
                results.append({'label': label, 'video_id': vid, 'status':'error'})
                break
        else:
            results.append({'label': label, 'video_id': vid, 'status':'timeout'})
    else:
        results.append({'label': label, 'video_id': None, 'status': 'failed', 'err': resp})
    time.sleep(1)

print(f"\n=== RESUMO ===")
print(f"Conta: {ACCT} (Joao Mafra Lancamento)")
for r in results:
    print(f"  {r['label']} -> video_id: {r['video_id']} [{r['status']}]")
