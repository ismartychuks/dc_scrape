#!/usr/bin/env python3
"""
Test script to diagnose telegram message formatting issues
"""
import json
import os
import sys
from pathlib import Path

# Load bot utils
sys.path.insert(0, os.path.dirname(__file__))

# Mock the format function
def test_message_formatting():
    """Test if we can load and parse messages from Supabase"""
    
    print("=" * 80)
    print("🔍 TELEGRAM MESSAGE FORMATTING TEST")
    print("=" * 80)
    print()
    
    # Check if data files exist
    data_dir = Path("data")
    bot_cursor_file = data_dir / "bot_cursor.json"
    
    print("📁 Checking files...")
    if bot_cursor_file.exists():
        with open(bot_cursor_file) as f:
            cursor_data = json.load(f)
        print(f"✅ bot_cursor.json exists")
        print(f"   Last scraped: {cursor_data.get('last_scraped_at')}")
        print(f"   Sent hashes: {len(cursor_data.get('sent_hashes', []))}")
    else:
        print(f"❌ bot_cursor.json NOT found")
    
    print()
    print("=" * 80)
    print("🧪 Testing Message Format Function")
    print("=" * 80)
    print()
    
    # Create a mock message
    mock_message = {
        "content": "@Product Alert | [UK] TEST-001 | TestBrand | Just restocked for £9.99",
        "scraped_at": "2025-12-18T12:00:00.000000",
        "raw_data": {
            "content_hash": "test123",
            "author": {
                "name": "Test Bot",
                "is_bot": True
            },
            "embed": {
                "title": "Test Product",
                "description": "This is a test product description",
                "author": {
                    "name": "TestStore.com",
                    "url": "https://teststore.com"
                },
                "fields": [
                    {"name": "Price", "value": "£9.99"},
                    {"name": "Stock", "value": "5+"},
                    {"name": "Status", "value": "In Stock"}
                ],
                "links": [
                    {"field": "Links", "text": "Sold", "url": "https://ebay.com/sold"},
                    {"field": "Links", "text": "Keepa", "url": "https://keepa.com"},
                    {"field": "ATC / QT", "text": "ATC1", "url": "https://zephr.app/atc1"},
                    {"field": "ATC / QT", "text": "ATC2", "url": "https://zephr.app/atc2"}
                ],
                "images": ["https://example.com/image.jpg"],
                "thumbnail": "https://example.com/thumb.jpg",
                "footer": "Test Footer"
            }
        }
    }
    
    # Try to import and test the formatting function
    try:
        from telegram_bot import format_telegram_message
        
        print("✅ Successfully imported format_telegram_message")
        print()
        print("🔄 Formatting mock message...")
        
        text, images, keyboard = format_telegram_message(mock_message)
        
        print("✅ Message formatted successfully!")
        print()
        print("📝 TEXT OUTPUT:")
        print("-" * 80)
        print(text)
        print("-" * 80)
        print()
        
        print("🖼️  IMAGES:")
        if images:
            for i, img in enumerate(images):
                print(f"   {i+1}. {img[:80]}")
        else:
            print("   None")
        print()
        
        print("🔘 KEYBOARD BUTTONS:")
        if keyboard:
            for row_idx, row in enumerate(keyboard.inline_keyboard):
                print(f"   Row {row_idx + 1}:")
                for btn in row:
                    print(f"      • {btn.text[:30]} → {btn.url[:50]}")
        else:
            print("   None")
        print()
        
        print("✅ ALL TESTS PASSED!")
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        print()
        print("TRACEBACK:")
        print(traceback.format_exc())
        sys.exit(1)
    
    print("=" * 80)

if __name__ == "__main__":
    test_message_formatting()
