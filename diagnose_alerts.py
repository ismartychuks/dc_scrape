#!/usr/bin/env python3
"""
Diagnostic script to identify why Telegram alerts aren't being sent
"""

import os
import json
import logging
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "").strip()

print("=" * 80)
print("🔍 TELEGRAM ALERTS DIAGNOSTIC")
print("=" * 80)

# 1. Check environment variables
print("\n1️⃣  ENVIRONMENT CHECK:")
print(f"   ✓ TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ MISSING'}")
print(f"   ✓ TELEGRAM_ADMIN_ID: {TELEGRAM_ADMIN_ID if TELEGRAM_ADMIN_ID else '❌ MISSING'}")
print(f"   ✓ SUPABASE_URL: {'✅ SET' if SUPABASE_URL else '❌ MISSING'}")
print(f"   ✓ SUPABASE_KEY: {'✅ SET' if SUPABASE_KEY else '❌ MISSING'}")

# 2. Check bot_users.json
print("\n2️⃣  BOT USERS STATUS:")
try:
    with open("data/bot_users.json", "r") as f:
        users = json.load(f)
    print(f"   Total users: {len(users)}")
    
    now = datetime.utcnow()
    for uid, data in users.items():
        expiry = data.get("expiry", "unknown")
        paused = data.get("alerts_paused", False)
        username = data.get("username", "unknown")
        
        # Parse expiry
        try:
            exp_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        except:
            exp_dt = None
        
        status = ""
        if paused:
            status = "🔴 PAUSED"
        elif exp_dt and exp_dt <= now:
            status = "🔴 EXPIRED"
        else:
            status = "🟢 ACTIVE"
        
        print(f"   • {uid} (@{username}): {status}")
        print(f"     Expires: {expiry}")
        print(f"     Paused: {paused}")
except Exception as e:
    print(f"   ❌ Error reading bot_users.json: {e}")

# 3. Check Discord Messages in Supabase
print("\n3️⃣  CHECKING SUPABASE DISCORD_MESSAGES TABLE:")
try:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Check total count
    count_url = f"{SUPABASE_URL}/rest/v1/discord_messages?select=count()"
    res = requests.get(count_url, headers=headers, timeout=10)
    
    if res.status_code == 200:
        total_count = len(res.json())
        print(f"   ✓ Table accessible")
        print(f"   ✓ Total messages: {total_count}")
    else:
        print(f"   ❌ Table access failed: {res.status_code}")
        print(f"   Response: {res.text[:200]}")
    
    # Check recent messages
    recent_url = f"{SUPABASE_URL}/rest/v1/discord_messages?order=scraped_at.desc&limit=5"
    res = requests.get(recent_url, headers=headers, timeout=10)
    
    if res.status_code == 200 and res.json():
        messages = res.json()
        print(f"\n   📬 Recent messages:")
        for msg in messages[:3]:
            scraped_at = msg.get("scraped_at", "unknown")
            content = msg.get("content", "")[:50]
            print(f"      • {scraped_at}: {content}...")
    else:
        print(f"   ⚠️  No recent messages found")
        
except Exception as e:
    print(f"   ❌ Error querying Supabase: {e}")

# 4. Check bot cursor
print("\n4️⃣  CHECKING BOT CURSOR (Last Polled Time):")
try:
    with open("data/bot_cursor.json", "r") as f:
        cursor = json.load(f)
    last_scraped = cursor.get("last_scraped_at", "unknown")
    print(f"   ✓ Last scraped: {last_scraped}")
    
    # Calculate how old
    try:
        last_dt = datetime.fromisoformat(last_scraped)
        now = datetime.utcnow()
        age = now - last_dt
        print(f"   ✓ Age: {age.total_seconds():.1f} seconds ago")
        if age.total_seconds() > 3600:
            print(f"   ⚠️  WARNING: Cursor is {age.total_seconds()/3600:.1f} hours old!")
    except:
        pass
except Exception as e:
    print(f"   ⚠️  No bot cursor found (first run?): {e}")

# 5. Check Telegram connectivity
print("\n5️⃣  TELEGRAM CONNECTIVITY:")
if TELEGRAM_TOKEN:
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"   ✅ Telegram Bot Connected")
                print(f"   ✓ Bot username: @{bot_info.get('username')}")
                print(f"   ✓ Bot name: {bot_info.get('first_name')}")
            else:
                print(f"   ❌ Bot error: {data.get('description')}")
        else:
            print(f"   ❌ HTTP Error: {res.status_code}")
    except Exception as e:
        print(f"   ❌ Telegram unreachable: {e}")
else:
    print(f"   ❌ TELEGRAM_TOKEN not set")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("""
If you see:
  🟢 All checks green → Alerts SHOULD be working
  🟡 Last scraped is old → Discord archiver isn't running
  🔴 No messages → Messages not being scraped
  🔴 All users paused/expired → No active subscribers
""")
print("=" * 80)
