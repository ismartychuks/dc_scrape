import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_db():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}'
    }
    
    # 1. Check Alerts
    r = requests.get(f"{url}/rest/v1/alerts?select=count", headers=headers)
    print(f"Alerts Count: {r.headers.get('Content-Range')}")
    
    # 2. Check Categories
    r = requests.get(f"{url}/rest/v1/categories?select=count", headers=headers)
    print(f"Categories Count: {r.headers.get('Content-Range')}")
    
if __name__ == "__main__":
    check_db()
