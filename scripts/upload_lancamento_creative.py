import requests, os, json
from datetime import date

TOKEN = os.environ['META_ACCESS_TOKEN']
BASE  = "https://graph.facebook.com/v19.0"
CAMP  = "120248546729160002"

# Campaign metadata
r = requests.get(f"{BASE}/{CAMP}", params={
    'fields':'id,name,status,effective_status,created_time,updated_time,start_time,stop_time,objective',
    'access_token':TOKEN
}, timeout=30).json()
print(f"Campanha: {r.get('name')}")
print(f"  ID:       {r.get('id')}")
print(f"  Status:   {r.get('effective_status')}")
print(f"  Objetivo: {r.get('objective')}")
print(f"  Criada:   {r.get('created_time')}")
print(f"  Iniciada: {r.get('start_time')}")
print(f"  Atualiz:  {r.get('updated_time')}")
print(f"  Encerra:  {r.get('stop_time','sem data fim')}")

# First insights data point (effective start = first day with spend)
r2 = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend,date_start,date_stop',
    'date_preset':'maximum',
    'access_token':TOKEN
}, timeout=30).json()
data = r2.get('data', [])
if data:
    d = data[0]
    print(f"\n  Primeira entrega: {d.get('date_start')}")
    print(f"  Ult dia entrega:  {d.get('date_stop')}")
    print(f"  Gasto lifetime:   EUR{float(d.get('spend',0)):.2f}")

# Get first day with actual spend (time_increment=1)
r3 = requests.get(f"{BASE}/{CAMP}/insights", params={
    'fields':'spend',
    'date_preset':'maximum',
    'time_increment':1,
    'access_token':TOKEN
}, timeout=30).json()
days = r3.get('data', [])
days_with_spend = [d for d in days if float(d.get('spend',0)) > 0]
if days_with_spend:
    first_day = days_with_spend[0]
    print(f"\n  Primeiro dia com gasto: {first_day.get('date_start')} (EUR{float(first_day.get('spend',0)):.2f})")
    total_days = (date.fromisoformat(days_with_spend[-1].get('date_start')) - date.fromisoformat(first_day.get('date_start'))).days + 1
    print(f"  Dias ativos: {len(days_with_spend)} dias com entrega de {total_days} dias corridos")
