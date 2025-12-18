#!/usr/bin/env python3
"""
Diagnostic tool for Telegram Bot alerts
Checks: Users, Messages, Filters, Network, Permissions
"""

import os
import json
import requests
from datetime import datetime, timedelta
import supabase_utils
from dotenv import load_dotenv

load_dotenv()

SUPABASE_BUCKET = "monitor-data"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = os.getenv("TELEGRAM_ADMIN_ID")

print("\n" + "="*80)
print("🔍 TELEGRAM BOT DIAGNOSTIC CHECK")
print("="*80 + "\n")

# 1. Check Environment Variables
print("1️⃣  ENVIRONMENT VARIABLES")
print("-" * 80)
print(f"   TELEGRAM_TOKEN: {'✅ SET' if TELEGRAM_TOKEN else '❌ NOT SET'}")
print(f"   ADMIN_USER_ID: {'✅ SET' if ADMIN_USER_ID else '❌ NOT SET'}")

supabase_url, supabase_key = supabase_utils.get_supabase_config()
print(f"   SUPABASE_URL: {'✅ SET' if supabase_url else '❌ NOT SET'}")
print(f"   SUPABASE_KEY: {'✅ SET' if supabase_key else '❌ NOT SET'}")

# 2. Check Supabase Connection
print("\n2️⃣  SUPABASE CONNECTION")
print("-" * 80)
try:
    headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
    url = f"{supabase_url}/rest/v1/discord_messages?limit=1"
    res = requests.get(url, headers=headers, timeout=5)
    if res.status_code == 200:
        print("   ✅ Connected to Supabase successfully")
    else:
        print(f"   ❌ Supabase returned status {res.status_code}")
        print(f"      Response: {res.text[:200]}")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")

# 3. Check Local User File
print("\n3️⃣  LOCAL USER STATE")
print("-" * 80)
users_file = "data/bot_users.json"
if os.path.exists(users_file):
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
        print(f"   ✅ Users file exists")
        print(f"      Total users: {len(users)}")
        
        from telegram_bot import parse_iso_datetime
        now = datetime.utcnow()
        active_count = 0
        for uid, data in users.items():
            try:
                expiry = parse_iso_datetime(data.get("expiry", ""))
                if expiry > now:
                    paused = data.get("alerts_paused", False)
                    if not paused:
                        active_count += 1
                        print(f"      • {uid}: ✅ ACTIVE (expires {expiry.strftime('%Y-%m-%d')})")
                    else:
                        print(f"      • {uid}: ⏸️  PAUSED (expires {expiry.strftime('%Y-%m-%d')})")
                else:
                    print(f"      • {uid}: ❌ EXPIRED ({expiry.strftime('%Y-%m-%d')})")
            except:
                print(f"      • {uid}: ⚠️  ERROR parsing expiry")
        
        print(f"\n      Active users: {active_count}")
        if active_count == 0:
            print("      ⚠️  WARNING: NO ACTIVE USERS - Alerts won't be sent!")
    except Exception as e:
        print(f"   ❌ Error reading users file: {e}")
else:
    print(f"   ❌ Users file not found at {users_file}")

# 4. Check Recent Messages in Supabase
print("\n4️⃣  RECENT DISCORD MESSAGES")
print("-" * 80)
try:
    headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
    url = f"{supabase_url}/rest/v1/discord_messages"
    
    # Get messages from last hour
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    params = {"scraped_at": f"gt.{one_hour_ago}", "order": "scraped_at.desc", "limit": 10}
    
    res = requests.get(url, headers=headers, params=params, timeout=10)
    if res.status_code == 200:
        messages = res.json()
        if messages:
            print(f"   ✅ Found {len(messages)} messages in last hour")
            for i, msg in enumerate(messages[:5], 1):
                title = msg.get("raw_data", {}).get("embed", {}).get("title", "No title")[:50]
                author = msg.get("raw_data", {}).get("author", {}).get("name", "Unknown")
                print(f"      {i}. {author} - {title}")
        else:
            print("   ℹ️  No messages found in last hour")
    else:
        print(f"   ❌ Failed to fetch messages: {res.status_code}")
except Exception as e:
    print(f"   ❌ Error fetching messages: {e}")

# 5. Check Bot Cursor
print("\n5️⃣  BOT CURSOR STATE")
print("-" * 80)
cursor_file = "data/bot_cursor.json"
if os.path.exists(cursor_file):
    try:
        with open(cursor_file, 'r') as f:
            cursor = json.load(f)
        print(f"   ✅ Cursor file exists")
        last_scraped = cursor.get("last_scraped_at", "unknown")
        sent_count = len(cursor.get("sent_hashes", []))
        print(f"      Last scraped: {last_scraped}")
        print(f"      Messages sent (tracked): {sent_count}")
    except Exception as e:
        print(f"   ❌ Error reading cursor file: {e}")
else:
    print(f"   ℹ️  Cursor file not found (will be created on first run)")

# 6. Test Telegram Bot Token
print("\n6️⃣  TELEGRAM BOT CONNECTION")
print("-" * 80)
if TELEGRAM_TOKEN:
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            bot_data = res.json()
            if bot_data.get("ok"):
                bot_name = bot_data["result"].get("username", "Unknown")
                print(f"   ✅ Bot connected: @{bot_name}")
            else:
                print(f"   ❌ Bot API error: {bot_data}")
        else:
            print(f"   ❌ Failed to connect: {res.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
else:
    print("   ❌ TELEGRAM_TOKEN not set")

# 7. Summary & Recommendations
print("\n7️⃣  SUMMARY & RECOMMENDATIONS")
print("-" * 80)

issues = []

if not TELEGRAM_TOKEN or not supabase_key:
    issues.append("❌ Missing environment variables - bot cannot run")

try:
    with open("data/bot_users.json", 'r') as f:
        users = json.load(f)
    from telegram_bot import parse_iso_datetime
    now = datetime.utcnow()
    active_users = [uid for uid, data in users.items() 
                    if parse_iso_datetime(data.get("expiry", "")) > now 
                    and not data.get("alerts_paused", False)]
    if not active_users:
        issues.append("⚠️  NO ACTIVE USERS - Redeem a code to activate subscription")
except:
    issues.append("⚠️  Could not check active users")

try:
    headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    res = requests.get(
        f"{supabase_url}/rest/v1/discord_messages",
        headers=headers,
        params={"scraped_at": f"gt.{one_hour_ago}", "limit": 1},
        timeout=10
    )
    if res.status_code != 200 or not res.json():
        issues.append("⚠️  NO RECENT MESSAGES - Discord scraper may not be running")
except:
    issues.append("⚠️  Could not verify recent messages")

if issues:
    print("\n🔴 ISSUES DETECTED:\n")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n🟢 NO ISSUES DETECTED")
    print("   Bot should be receiving and sending alerts!")

print("\n" + "="*80)
print("💡 NEXT STEPS:")
print("="*80)
print("   1. Ensure Discord scraper is running (python app.py)")
print("   2. Ensure at least one user has active subscription")
print("   3. Run: python telegram_bot.py")
print("   4. Check logs for any errors")
print("="*80 + "\n")
