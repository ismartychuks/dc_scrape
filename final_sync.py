import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def sync():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase config in .env")
        return

    if url.endswith('/'): url = url[:-1]
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates, return=minimal'
    }
    
    # Load channels
    chan_path = "data/channels.json"
    if not os.path.exists(chan_path):
        print(f"❌ {chan_path} not found")
        return
        
    with open(chan_path, 'r') as f:
        channels = json.load(f)
        
    print(f"📦 Loaded {len(channels)} channels from JSON")
    
    sql_categories = []
    seen = set()
    
    for c in channels:
        raw_cat = c.get('category', 'US Stores').upper()
        
        # Determine Country Code
        if 'UK' in raw_cat:
            country = 'UK'
        elif 'CANADA' in raw_cat or 'CA ' in raw_cat or 'CA STORES' in raw_cat:
            country = 'CA'
        else:
            country = 'US'
            
        sub_name = c.get('name', 'Unknown')
        
        key_pair = (country, sub_name)
        if key_pair in seen: continue
        seen.add(key_pair)
        
        sql_categories.append({
            "country_code": country,
            "category_name": sub_name,
            "display_name": f"{country} {sub_name}",
            "active": True
        })

    if not sql_categories:
        print("⚠️ No categories to sync")
        return

    print(f"📤 Syncing {len(sql_categories)} unique categories to SQL...")
    
    endpoint = f"{url}/rest/v1/categories"
    try:
        # Send in batches of 50 to be safe
        for i in range(0, len(sql_categories), 50):
            batch = sql_categories[i:i+50]
            response = requests.post(endpoint, headers=headers, json=batch, timeout=30)
            if response.status_code in [200, 201, 204]:
                print(f"   ✅ Batch {i//50 + 1} synced")
            else:
                print(f"   ❌ Batch {i//50 + 1} failed: {response.status_code} - {response.text}")
                
        print("🎉 Sync complete!")
    except Exception as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    sync()
