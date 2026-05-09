import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ACCT  = "act_615338413578534"
PAGE_ID = "110278364765662"
VIDEO_ID = "1386873113201033"

# 1. Get thumbnail from Meta video API
print("=== Buscando thumbnail do video ===")
r = requests.get(f"{BASE}/{VIDEO_ID}", params={
    'fields': 'thumbnails,picture,status',
    'access_token': TOKEN
}, timeout=30)
v = r.json()
print(json.dumps(v, indent=2))

thumbs = v.get('thumbnails', {}).get('data', [])
thumb_url = thumbs[0].get('uri') if thumbs else v.get('picture')
print(f"\nthumb_url: {thumb_url[:80] if thumb_url else 'NONE'}")

# 2. Try creative with image_url from Meta CDN (no instagram_user_id, no image_hash)
if thumb_url:
    print("\n=== Test creative com image_url (sem instagram_user_id) ===")
    story_spec = {
        'page_id': PAGE_ID,
        'video_data': {
            'video_id': VIDEO_ID,
            'message': 'Sua chance de mudar tudo está aqui!\nO que você vai fazer com ela?',
            'image_url': thumb_url,
            'call_to_action': {
                'type': 'SEE_DETAILS',
                'value': {'link': 'https://go.joaomafra.pt/'}
            }
        }
    }
    cr_r = requests.post(f"{BASE}/{ACCT}/adcreatives", data={
        'access_token': TOKEN,
        'name': 'test-creative-thumb-url',
        'object_story_spec': json.dumps(story_spec),
    }, timeout=30)
    print("Resp:", json.dumps(cr_r.json(), indent=2))
else:
    print("Sem thumbnail disponivel — tentando sem imagem...")
