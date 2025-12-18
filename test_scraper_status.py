#!/usr/bin/env python3
"""
Test script to check if Discord messages are being scraped
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

def test_scraper_status():
    """Check Discord scraper status"""
    
    print("=" * 80)
    print("🔍 DISCORD SCRAPER STATUS CHECK")
    print("=" * 80)
    print()
    
    # Check Supabase connection
    print("🔗 SUPABASE CONNECTION:")
    try:
        import supabase_utils
        from telegram_bot import parse_iso_datetime
        url, key = supabase_utils.get_supabase_config()
        print(f"✅ Supabase configured")
        print(f"   URL: {url[:50]}...")
        print()
    except Exception as e:
        print(f"❌ Supabase error: {e}")
        return
    
    # Check recent messages in database
    print("📊 RECENT MESSAGES IN DATABASE:")
    try:
        import requests
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        url_query = f"{url}/rest/v1/discord_messages"
        
        # Get the last 5 messages
        params = {"order": "scraped_at.desc", "limit": "5"}
        res = requests.get(url_query, headers=headers, params=params, timeout=10)
        
        if res.status_code == 200:
            messages = res.json()
            print(f"✅ Retrieved {len(messages)} recent messages")
            print()
            
            for i, msg in enumerate(messages):
                scraped = msg.get("scraped_at", "unknown")
                author = msg.get("raw_data", {}).get("author", {}).get("name", "Unknown")
                print(f"   {i+1}. [{scraped}] {author}")
            
            if messages:
                last_msg_time = messages[0].get("scraped_at")
                print()
                print(f"⏰ Most recent message: {last_msg_time}")
                
                # Calculate time ago using the parse_iso_datetime function
                last_dt = parse_iso_datetime(last_msg_time)
                now = datetime.utcnow()
                time_ago = now - last_dt.replace(tzinfo=None)  # Remove timezone for comparison
                
                if time_ago.total_seconds() < 300:
                    print(f"✅ Messages are RECENT ({int(time_ago.total_seconds())}s ago)")
                elif time_ago.total_seconds() < 3600:
                    print(f"⚠️  Messages are somewhat old ({int(time_ago.total_seconds()//60)}m ago)")
                else:
                    print(f"❌ Messages are STALE ({int(time_ago.total_seconds()//3600)}h ago)")
        else:
            print(f"❌ Database query failed: {res.status_code}")
            print(f"   Response: {res.text[:200]}")
    
    except Exception as e:
        print(f"❌ Error querying database: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
    
    print()
    print("=" * 80)
    print("💡 RECOMMENDATION:")
    print("=" * 80)
    print()
    print("If no recent messages are showing:")
    print("1. Start the Discord scraper: python app.py")
    print("2. Wait for it to collect messages from Discord channels")
    print("3. The Telegram bot will then send alerts when new messages arrive")
    print()

if __name__ == "__main__":
    test_scraper_status()
