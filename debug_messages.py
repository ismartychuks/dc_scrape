#!/usr/bin/env python3
"""
Debug script to examine what message data is being stored in Supabase
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}'
}

# Get latest 5 messages
url = f"{SUPABASE_URL}/rest/v1/discord_messages"
params = {
    "order": "scraped_at.desc",
    "limit": 5
}

print("📋 Fetching latest messages from Supabase...\n")

try:
    res = requests.get(url, headers=headers, params=params, timeout=10)
    if res.status_code != 200:
        print(f"❌ HTTP {res.status_code}: {res.text}")
        exit(1)
    
    messages = res.json()
    print(f"Found {len(messages)} messages\n")
    
    for i, msg in enumerate(messages, 1):
        print(f"{'='*60}")
        print(f"Message #{i}")
        print(f"{'='*60}")
        print(f"ID: {msg.get('id')}")
        print(f"Channel: {msg.get('channel_id')}")
        print(f"Content: {msg.get('content', '')[:100]}")
        print(f"Scraped at: {msg.get('scraped_at')}")
        print()
        
        raw = msg.get('raw_data', {})
        embed = raw.get('embed')
        
        if embed is None:
            print(f"❌ NO EMBED DATA")
            print(f"   Content: {msg.get('content', '')}")
            
            # Check if content contains links or prices
            content_lower = msg.get('content', '').lower()
            if 'http' in content_lower or 'ebay' in content_lower or '£' in msg.get('content', ''):
                print(f"   ⚠️ CONTENT APPEARS TO HAVE LINKS OR PRICES!")
            print()
            continue
        
        print(f"📦 EMBED DATA:")
        print(f"   Title: {embed.get('title', 'N/A')[:80]}")
        print(f"   Description: {embed.get('description', 'N/A')[:80]}")
        print(f"   Author: {embed.get('author', {}).get('name', 'N/A')}")
        print()
        
        print(f"📋 FIELDS ({len(embed.get('fields', []))})")
        for field in embed.get('fields', []):
            print(f"   • {field.get('name', 'N/A')}: {field.get('value', 'N/A')[:60]}")
        print()
        
        print(f"🔗 LINKS ({len(embed.get('links', []))})")
        for link in embed.get('links', []):
            print(f"   • {link.get('text', 'N/A')[:30]}")
            print(f"     {link.get('url', 'N/A')[:70]}")
        print()
        
        print(f"🖼️ IMAGES ({len(embed.get('images', []))})")
        for img in embed.get('images', []):
            print(f"   • {img[:60]}...")
        print()
        
        # Check if links are complete
        if embed:
            num_links = len(embed.get('links', []))
            num_fields = len(embed.get('fields', []))
            print(f"✅ Embed extracted: {num_fields} fields, {num_links} links")
            
            # Check if any field values contain URLs
            for field in embed.get('fields', []):
                if 'http' in field.get('value', '').lower():
                    print(f"   ⚠️ Field contains URL: {field.get('name')} = {field.get('value')[:60]}")
        print()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
