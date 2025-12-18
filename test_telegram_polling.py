#!/usr/bin/env python3
"""
Test script to check if the message poller is working
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

def test_polling():
    """Test if polling is working"""
    
    print("=" * 80)
    print("🔍 TELEGRAM MESSAGE POLLER TEST")
    print("=" * 80)
    print()
    
    try:
        from telegram_bot import poller, sm
        
        print("✅ Successfully imported poller and subscription manager")
        print()
        
        # Check cursor state
        print("📊 POLLER STATE:")
        print(f"   Last scraped at: {poller.last_scraped_at}")
        print(f"   Sent hashes: {len(poller.sent_hashes)}")
        print()
        
        # Check subscription state
        print("👥 SUBSCRIPTION STATE:")
        print(f"   Total users: {len(sm.users)}")
        active_users = sm.get_active_users()
        print(f"   Active users: {len(active_users)}")
        if active_users:
            for uid in active_users[:5]:
                user_data = sm.users[uid]
                print(f"      • {uid}: {user_data.get('username', 'Unknown')}")
        else:
            print("      ⚠️  NO ACTIVE USERS!")
        print()
        
        # Try polling
        print("🔄 ATTEMPTING POLL...")
        new_msgs = poller.poll_new_messages()
        print(f"✅ Poll completed")
        print(f"   New messages found: {len(new_msgs)}")
        
        if new_msgs:
            print()
            print("📬 MESSAGE DETAILS:")
            for i, msg in enumerate(new_msgs[:3]):
                author = msg.get("raw_data", {}).get("author", {}).get("name", "Unknown")
                embed_title = msg.get("raw_data", {}).get("embed", {}).get("title", "No title")
                print(f"   {i+1}. [{author}] {embed_title[:60]}")
        else:
            print()
            print("⚠️  No new messages in the database")
            print("   Polling from: {poller.last_scraped_at}")
        print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        print()
        print("TRACEBACK:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    test_polling()
