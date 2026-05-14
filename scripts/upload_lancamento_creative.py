import requests, os, json, base64

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"  # DevSpace
BASE_URL = "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/"

IMAGES = [
    ("3 dias", "Faltam.3.dias.Trafego.Story.png"),
    ("4 dias", "Falta.4.dias.Trafego.Story.png"),
]

results = []
for label, filename in IMAGES:
    print(f"\n=== {label} — {filename} ===")
    url = BASE_URL + filename
    r = requests.get(url, timeout=60)
    print(f"  download: {r.status_code} ({len(r.content)/1024:.0f} KB)")
    if r.status_code != 200:
        print(f"  ERRO download"); continue
    
    img_b64 = base64.b64encode(r.content).decode()
    up = requests.post(f"{BASE}/{ACCT}/adimages", data={
        'bytes': img_b64,
        'access_token': TOKEN
    }, timeout=120)
    resp = up.json()
    
    if 'images' in resp:
        for fn, info in resp['images'].items():
            print(f"  OK")
            print(f"    hash:   {info.get('hash')}")
            print(f"    dim:    {info.get('width')}x{info.get('height')}")
            results.append({'label': label, 'filename': filename, 'hash': info.get('hash')})
    else:
        print(f"  ERRO: {resp}")

print(f"\n=== RESUMO FINAL ===")
print(f"Conta: {ACCT} (DevSpace)")
for r in results:
    print(f"  {r['label']:8} -> hash: {r['hash']}")
