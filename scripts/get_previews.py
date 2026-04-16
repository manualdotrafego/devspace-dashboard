import requests, re, os

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = 'https://graph.facebook.com/v19.0'

ADS = [
    ('120249001823240002', 'IMG_4583',    '🥇 13 leads · CPL €5,75'),
    ('120249005627130002', 'IMG_4585',    '🥈 9 leads · CPL €5,50'),
    ('120249005624690002', 'IMG_4584',    '🥉 4 leads · CPL €6,65'),
    ('120249005639330002', 'MIX ESTÁTICO','⭐ CTR 3,54%'),
]

for ad_id, name, label in ADS:
    r = requests.get(f'{BASE}/{ad_id}/previews', params={
        'access_token': TOKEN,
        'ad_format': 'MOBILE_FEED_STANDARD'
    }, timeout=20)
    body = r.json().get('data', [{}])[0].get('body', '')
    m = re.search(r'src=[\'"](https://[^\'"]+)[\'"]', body)
    url = m.group(1).replace('&amp;', '&') if m else 'erro'
    print(f'AD: {name} | {label}')
    print(f'URL: {url}')
    print()
