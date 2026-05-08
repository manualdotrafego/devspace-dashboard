import requests, os, json

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
ADSET_ID = "120248610894970581"

# Get current budget
r = requests.get(f"{BASE}/{ADSET_ID}", params={
    'fields': 'id,name,daily_budget,lifetime_budget,effective_status',
    'access_token': TOKEN
})
print("GET response:", r.text)
