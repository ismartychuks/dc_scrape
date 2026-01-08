
import os
import json
import requests

def load_env_manual():
    env_path = ".env"
    if not os.path.exists(env_path):
        return
        
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("'").strip('"')

load_env_manual()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def inspect_latest():
    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(str(msg))

    if not SUPABASE_URL or not SUPABASE_KEY:
        log("Missing SUPABASE_URL or SUPABASE_KEY")
        return

    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    url = f"{SUPABASE_URL}/rest/v1/discord_messages"
    params = {
        "select": "*",
        "order": "scraped_at.desc",
        "limit": 50
    }
    
    log(f"Fetching last 50 messages from {url}...")
    res = requests.get(url, headers=headers, params=params)
    
    if res.status_code != 200:
        log(f"Error: {res.status_code}")
        return

    messages = res.json()
    if not messages:
        log("No messages found.")
        return

    found = False
    for msg in messages:
        raw = msg.get("raw_data", {})
        embed = raw.get("embed")
        
        if embed and (embed.get("images") or embed.get("thumbnail") or embed.get("image")):
            log(f"\n✅ Found message with images! ID: {msg.get('id')}")
            
            if embed.get("images"):
                log("Images array found in JSON:")
                for img in embed["images"]:
                    log(f" - {img}")
            else:
                log("No 'images' array in embed.")
                
            if embed.get("image"):
                 log(f"Legacy 'image' field: {embed.get('image')}")
                 
            if embed.get("thumbnail"):
                log(f"Thumbnail URL: {embed.get('thumbnail')}")
                
            log("\nFull Embed JSON:")
            log(json.dumps(embed, indent=2, ensure_ascii=False))
            found = True
            break
            
    if not found:
        log("❌ No messages with images found in the last 50.")
        
    with open("inspection_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

if __name__ == "__main__":
    inspect_latest()
