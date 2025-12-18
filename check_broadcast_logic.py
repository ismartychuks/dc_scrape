#!/usr/bin/env python3
"""
Deep dive: Check if telegram_bot polling is running
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

print("\n" + "=" * 80)
print("🔍 DEEP DIVE: MESSAGE POLLING LOGIC")
print("=" * 80)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Read bot cursor (last time we polled)
print("\n1️⃣  READING BOT CURSOR:")
with open("data/bot_cursor.json", "r") as f:
    cursor = json.load(f)

last_scraped_at = cursor.get("last_scraped_at")
sent_hashes = set(cursor.get("sent_hashes", []))
print(f"   Last scraped: {last_scraped_at}")
print(f"   Sent hashes (dedup): {len(sent_hashes)} hashes")

# Query for NEW messages since last poll
print(f"\n2️⃣  QUERYING NEW MESSAGES:")
print(f"   Looking for messages with scraped_at > {last_scraped_at}")

try:
    url = f"{SUPABASE_URL}/rest/v1/discord_messages"
    params = {
        "scraped_at": f"gt.{last_scraped_at}",
        "order": "scraped_at.asc",
        "limit": 100
    }
    
    res = requests.get(url, headers=headers, params=params, timeout=10)
    
    if res.status_code == 200:
        messages = res.json()
        print(f"   ✅ Query successful")
        print(f"   Found: {len(messages)} new messages")
        
        if messages:
            print(f"\n   🎯 NEW MESSAGES THAT SHOULD BE SENT:")
            for i, msg in enumerate(messages[:5]):
                content = msg.get("content", "")[:60]
                scraped = msg.get("scraped_at", "unknown")
                content_hash = msg.get("raw_data", {}).get("content_hash", "N/A")
                
                is_duplicate = content_hash in sent_hashes
                status = "🔴 DUPLICATE (already sent)" if is_duplicate else "🟢 NEW"
                
                print(f"\n      Message {i+1}:")
                print(f"        Scraped: {scraped}")
                print(f"        Hash: {content_hash}")
                print(f"        Status: {status}")
                print(f"        Content: {content}...")
            
            if len(messages) > 5:
                print(f"\n      ... and {len(messages)-5} more messages")
        else:
            print(f"\n   ⚠️  NO NEW MESSAGES to send")
            print(f"   This could mean:")
            print(f"      • Archiver stopped running")
            print(f"      • All messages already sent (duplicates)")
            print(f"      • Supabase has no new data since {last_scraped_at}")
    else:
        print(f"   ❌ Query failed: {res.status_code}")
        print(f"   Response: {res.text}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ WHAT THIS MEANS:")
print("=" * 80)
print("""
If you see:
  🟢 NEW messages → Telegram bot SHOULD send them (check if bot is running)
  🔴 DUPLICATE messages → Bot successfully sent them before
  ⚠️  NO NEW MESSAGES → Archiver needs to be restarted or is not scraping
""")
print("\n💡 FIX: Make sure telegram_bot.py is running with:")
print("   python telegram_bot.py")
print("=" * 80 + "\n")
