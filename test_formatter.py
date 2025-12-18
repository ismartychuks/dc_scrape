#!/usr/bin/env python3
"""Test Telegram message formatting with sample data"""

import sys
import json
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, '/Users/HP USER/Documents/Data Analyst/discord')

from telegram_bot import format_telegram_message

# Sample message 1: With links (new extraction method)
sample_message = {
    "id": 123456,
    "content": "@Product Flips | [UK] 520153 | Ogerpon ex Premium Collection | Magicmadhouse | Just restocked for 33.95",
    "scraped_at": datetime.utcnow().isoformat(),
    "raw_data": {
        "author": {
            "name": "Unfiltered Restocks",
            "is_bot": True
        },
        "embed": {
            "title": "Ogerpon ex Premium Collection",
            "description": "Just restocked",
            "fields": [],
            "images": [],
            "links": [
                {"text": "eBay Sold", "url": "https://ebay.com/itm/520153"},
                {"text": "Keepa", "url": "https://keepa.com/product/..."},
                {"text": "StockX", "url": "https://stockx.com/..."},
            ]
        }
    }
}

# Sample message 2: With rich embed fields
sample_message_2 = {
    "id": 654321,
    "content": "@Monitors v2.0.0 | Ogerpeon ex Premium Collection | Cardvault | Price: £33.95 Stock: 1+ New",
    "scraped_at": datetime.utcnow().isoformat(),
    "raw_data": {
        "author": {
            "name": "Monitors Bot v2.0.0",
            "is_bot": True
        },
        "embed": {
            "title": "Ogerpeon ex Premium Collection",
            "description": "Just restocked for 20.00",
            "fields": [
                {"name": "Price", "value": "£33.95"},
                {"name": "Stock", "value": "1+"},
                {"name": "Type", "value": "New Product"},
            ],
            "images": ["https://example.com/image.jpg"],
            "links": [
                {"text": "StockX", "url": "https://stockx.com/..."},
                {"text": "SnkrDunk", "url": "https://snkrdunk.com/..."},
                {"text": "eBay", "url": "https://ebay.com/itm/..."},
            ]
        }
    }
}

text, images, keyboard = format_telegram_message(sample_message)

print("=" * 60)
print("TEST 1: BASIC MESSAGE WITH LINKS")
print("=" * 60)
print(text)
print()
print("Images:", images)
print("Keyboard buttons:", len(keyboard.inline_keyboard) if keyboard else 0)
if keyboard:
    for i, row in enumerate(keyboard.inline_keyboard):
        print(f"  Row {i}: {[btn.text for btn in row]}")

print("\n\n")

text2, images2, keyboard2 = format_telegram_message(sample_message_2)

print("=" * 60)
print("TEST 2: MESSAGE WITH RICH EMBED FIELDS")
print("=" * 60)
print(text2)
print()
print("Images:", len(images2) if images2 else 0, "image(s)")
print("Keyboard buttons:", len(keyboard2.inline_keyboard) if keyboard2 else 0)
if keyboard2:
    for i, row in enumerate(keyboard2.inline_keyboard):
        print(f"  Row {i}: {[btn.text for btn in row]}")
