import requests, os, time
TOKEN=os.environ['META_ACCESS_TOKEN']; BASE="https://graph.facebook.com/v19.0"
ACCT="act_615338413578534"
URL="https://github.com/manualdotrafego/devspace-dashboard/releases/download/webnar-3006-v1/IMG_7120.MP4"
r=requests.post(f"{BASE}/{ACCT}/advideos",data={
    'file_url':URL,'name':'IMG_7120','access_token':TOKEN},timeout=300).json()
vid=r.get('id')
print(f"video_id={vid}" if vid else f"ERRO: {r}")
if vid:
    for i in range(40):
        time.sleep(6)
        st=requests.get(f"{BASE}/{vid}",params={'fields':'status','access_token':TOKEN},timeout=30).json()
        ph=st.get('status',{}).get('video_status','?')
        if ph=='ready': print("STATUS=ready"); break
        if ph=='error': print(f"STATUS=error {st}"); break
