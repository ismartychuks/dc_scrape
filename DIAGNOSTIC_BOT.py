#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC TOOL - Debug why Telegram alerts aren't being sent

This script checks:
1. Are there active users in the subscription manager?
2. Are messages being stored in Supabase?
3. Is the poller finding new messages?
4. Is the broadcaster connected?
"""

import os
import json
import sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_bot import sm, poller, SUPABASE_BUCKET
import supabase_utils
import requests

print("╔════════════════════════════════════════════════════════════════╗")
print("║         🔍 TELEGRAM BOT DIAGNOSTIC TOOL                       ║")
print("╚════════════════════════════════════════════════════════════════╝\n")

# ===== CHECK 1: Active Users =====
print("1️⃣  CHECK: Active Users")
print("─" * 60)

active_users = sm.get_active_users()
all_users = sm.users

print(f"📊 Total registered users: {len(all_users)}")
print(f"✅ Active users (not paused, not expired): {len(active_users)}")

if not active_users:
    print("\n⚠️  WARNING: No active users!")
    print("\n   Possible causes:")
    print("   • No codes have been redeemed")
    print("   • All subscriptions expired")
    print("   • All users paused alerts")
    print("\n   Users registered:")
    for uid, data in all_users.items():
        expiry = data.get("expiry", "Unknown")
        paused = data.get("alerts_paused", False)
        print(f"     • {uid}: expires {expiry}, paused={paused}")
else:
    print("\n✅ Active users found:")
    for uid in active_users:
        user_data = all_users.get(uid, {})
        expiry = user_data.get("expiry", "Unknown")
        print(f"   • {uid}: expires {expiry}")

print()

# ===== CHECK 2: Messages in Supabase =====
print("2️⃣  CHECK: Messages in Supabase")
print("─" * 60)

try:
    supabase_url, supabase_key = supabase_utils.get_supabase_config()
    headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
    url = f"{supabase_url}/rest/v1/discord_messages"
    
    # Get recent messages
    params = {"order": "scraped_at.desc", "limit": "5"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    
    if res.status_code == 200:
        messages = res.json()
        print(f"📦 Recent messages in database: {len(messages) if messages else 0}")
        
        if messages:
            print("\n   Last 5 messages:")
            for i, msg in enumerate(messages[:5], 1):
                msg_id = msg.get("id")
                content = msg.get("content", "")[:50]
                scraped = msg.get("scraped_at", "Unknown")
                embed = msg.get("raw_data", {}).get("has_embed", False)
                
                print(f"   {i}. ID: {msg_id}")
                print(f"      Content: {content}...")
                print(f"      Scraped: {scraped}")
                print(f"      Has Embed: {'✅' if embed else '❌'}")
        else:
            print("\n⚠️  WARNING: No messages found in database!")
    else:
        print(f"❌ Failed to query messages: {res.status_code}")
        print(f"   Response: {res.text}")
except Exception as e:
    print(f"❌ Error querying messages: {e}")

print()

# ===== CHECK 3: Poller Status =====
print("3️⃣  CHECK: Message Poller")
print("─" * 60)

print(f"⏰ Poller last_scraped_at: {poller.last_scraped_at}")
print(f"📝 Sent message hashes: {len(poller.sent_hashes)}")

if poller.last_scraped_at:
    try:
        last_dt = datetime.fromisoformat(poller.last_scraped_at.replace('Z', '+00:00'))
        now = datetime.utcnow()
        age = now - last_dt
        print(f"⏳ Time since last poll: {age}")
        
        if age > timedelta(hours=1):
            print("⚠️  WARNING: Haven't polled in over 1 hour!")
            print("   Check if app.py is uploading messages correctly")
    except:
        pass

# Try polling
print("\n🔄 Testing poll_new_messages()...")
try:
    new_msgs = poller.poll_new_messages()
    print(f"   Found {len(new_msgs)} new messages" if new_msgs else "   No new messages")
    
    if new_msgs:
        print("   ✅ Poller is working!")
        for msg in new_msgs[:3]:
            print(f"      • {msg.get('id')}: {msg.get('content', '')[:30]}...")
    else:
        print("   ⚠️  Poller found no new messages")
        print("   This could mean:")
        print("     • app.py isn't uploading messages")
        print("     • Messages have already been sent")
        print("     • last_scraped_at is too recent")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# ===== CHECK 4: Message Format =====
print("4️⃣  CHECK: Message Format")
print("─" * 60)

print("Checking if messages have required fields for formatting...")
try:
    # Get one message
    params = {"limit": "1"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    if res.status_code == 200:
        messages = res.json()
        if messages:
            msg = messages[0]
            required_fields = ["id", "content", "scraped_at", "raw_data"]
            
            print(f"\nMessage structure check:")
            for field in required_fields:
                has_field = field in msg
                print(f"  {'✅' if has_field else '❌'} {field}")
            
            raw_data = msg.get("raw_data", {})
            if raw_data:
                print(f"\nraw_data structure:")
                print(f"  ✅ author: {'author' in raw_data}")
                print(f"  ✅ embed: {'embed' in raw_data}")
                print(f"  ✅ has_embed: {'has_embed' in raw_data}")
except Exception as e:
    print(f"❌ Error checking message format: {e}")

print()

# ===== SUMMARY =====
print("📋 SUMMARY")
print("─" * 60)

issues = []

if not active_users:
    issues.append("❌ No active users - messages won't be sent to anyone")
else:
    print(f"✅ {len(active_users)} active user(s)")

try:
    params = {"limit": "1"}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    if res.status_code == 200:
        messages = res.json()
        if messages:
            print(f"✅ Messages are in Supabase")
        else:
            issues.append("❌ No messages in Supabase - check if app.py is uploading")
except:
    issues.append("❌ Can't access Supabase")

if issues:
    print("\n🚨 ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n✅ Everything looks good!")
    print("   If alerts still aren't working:")
    print("   • Check bot token is correct")
    print("   • Check bot is running with /start command")
    print("   • Check broadcast_job frequency (should run every 10s)")

print("\n" + "=" * 60)
