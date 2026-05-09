import requests, os, time, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"

VIDEOS = [
    ("IMG_5319", "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/IMG_5319.MP4"),
    ("IMG_5320", "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/IMG_5320.MP4"),
    ("IMG_5321", "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/IMG_5321.MP4"),
    ("IMG_5322", "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/IMG_5322.MP4"),
    ("IMG_5325", "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/IMG_5325.MP4"),
    ("IMG_5326", "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/IMG_5326.MP4"),
]

def resolve_cdn(url):
    r = requests.head(url, allow_redirects=False, timeout=30)
    cdn = r.headers.get('location', '')
    return cdn if cdn else url

def upload_via_file_url(name, url):
    cdn = resolve_cdn(url)
    print(f"  [file_url] {name}...")
    r = requests.post(f"{BASE}/{ACCT}/advideos",
        data={'access_token': TOKEN, 'name': name, 'file_url': cdn}, timeout=60)
    data = r.json()
    vid_id = data.get('id') or data.get('video_id')
    if vid_id:
        print(f"  OK video_id: {vid_id}")
        return vid_id
    print(f"  ERR: {r.text[:300]}")
    return None

def upload_multipart(name, url):
    print(f"  [multipart] Baixando {name}...")
    tmp = f"/tmp/{name}.mp4"
    with requests.get(url, stream=True, timeout=600, allow_redirects=True) as dl:
        dl.raise_for_status()
        with open(tmp, 'wb') as f:
            for chunk in dl.iter_content(chunk_size=4*1024*1024):
                f.write(chunk)
    print(f"  Download OK. Uploading to Meta...")
    with open(tmp, 'rb') as f:
        r = requests.post(f"{BASE}/{ACCT}/advideos",
            data={'access_token': TOKEN, 'name': name},
            files={'source': (f"{name}.mp4", f, 'video/mp4')}, timeout=600)
    data = r.json()
    vid_id = data.get('id') or data.get('video_id')
    if vid_id:
        print(f"  OK video_id: {vid_id}")
        return vid_id
    print(f"  ERR: {r.text[:300]}")
    return None

# Find lowest budget active adset
print("=== Buscando conjuntos ativos com menor orcamento ===")
r = requests.get(f"{BASE}/{ACCT}/adsets", params={
    'fields': 'id,name,status,effective_status,daily_budget,lifetime_budget,campaign_id',
    'limit': 100, 'access_token': TOKEN
}, timeout=30)
adsets = r.json().get('data', [])
active = [a for a in adsets if a.get('effective_status') == 'ACTIVE']
active.sort(key=lambda x: int(x.get('daily_budget') or x.get('lifetime_budget') or 0))
print(f"Conjuntos ativos: {len(active)}")
for a in active[:5]:
    db = int(a.get('daily_budget') or 0)
    lb = int(a.get('lifetime_budget') or 0)
    print(f"  {a['name'][:50]} | daily=R${db/100:.2f} | lifetime=R${lb/100:.2f} | id={a['id']}")

if active:
    lowest = active[0]
    print(f"\nMENOR ORCAMENTO: {lowest['name']} (id={lowest['id']}, camp={lowest.get('campaign_id')})")

print("\n=== Upload dos 6 videos ===")
results = {}
for name, url in VIDEOS:
    vid_id = upload_via_file_url(name, url)
    if not vid_id:
        vid_id = upload_multipart(name, url)
    results[name] = vid_id
    time.sleep(2)

print("\n=== RESULTADO FINAL ===")
for name, vid_id in results.items():
    status = f"video_id={vid_id}" if vid_id else "FALHOU"
    print(f"  {name}: {status}")

print("\nJSON para criar ads:")
print(json.dumps(results, indent=2))
