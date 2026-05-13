import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_592324092832640"  # DevSpace
IMG_URL = "https://github.com/manualdotrafego/devspace-dashboard/releases/download/joao-mafra-webnar-v1/Falta.5.dias.Trafego.Story.png"

# Download image and upload bytes to Meta
print(f"=== Baixando imagem ===")
r = requests.get(IMG_URL, timeout=60)
print(f"Status download: {r.status_code} | size: {len(r.content)/1024:.1f} KB")

if r.status_code != 200:
    print("ERRO no download"); exit(1)

import base64
img_b64 = base64.b64encode(r.content).decode()

print(f"\n=== Subindo no ad account {ACCT} ===")
up = requests.post(f"{BASE}/{ACCT}/adimages", data={
    'bytes': img_b64,
    'access_token': TOKEN
}, timeout=120)
resp = up.json()
print(json.dumps(resp, indent=2))

# Image hash
if 'images' in resp:
    for filename, info in resp['images'].items():
        print(f"\n=== UPLOAD OK ===")
        print(f"  filename: {filename}")
        print(f"  hash:     {info.get('hash')}")
        print(f"  url:      {info.get('url')}")
        print(f"  width:    {info.get('width')}")
        print(f"  height:   {info.get('height')}")
