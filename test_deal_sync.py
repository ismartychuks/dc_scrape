import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import supabase_utils
import telegram_bot

load_dotenv()

def simulate_deal():
    print("🧪 Simulating Deal Extraction & SQL Sync...")
    
    # Mock Discord Message Data
    mock_msg = {
        "id": "1234567890",
        "channel_id": "1367813504786108526", # UK Collectors Amazon
        "content": "New deal found!",
        "scraped_at": datetime.utcnow().isoformat(),
        "raw_data": {
            "embed": {
                "title": "Nike Air Jordan 1 Low",
                "description": "Premium leather upper with iconic swoosh.",
                "images": ["https://images.stockx.com/images/Air-Jordan-1-Low-Wolf-Grey-Product.jpg"],
                "fields": [
                    {"name": "Retail Price", "value": "109.95"},
                    {"name": "Resell Price", "value": "180.00"},
                    {"name": "ROI", "value": "64%"}
                ],
                "links": [
                    {"text": "Buy Now", "url": "https://www.nike.com/jordan-1-low", "field": "link"}
                ]
            }
        }
    }
    
    # 1. Format (Telegram side)
    text, img_url, keyboard, img_bytes = telegram_bot.format_telegram_message(mock_msg)
    print(f"✅ Formatted Text: {text[:50]}...")
    
    # 2. Extract (Mobile side)
    product_meta = telegram_bot.extract_deal_metadata(mock_msg, img_url)
    print(f"✅ Extracted Meta: {json.dumps(product_meta, indent=2)}")
    
    # 3. Push to SQL
    # Get channel info for category mapping
    cm = telegram_bot.ChannelManager()
    msg_category = "UK Stores"
    msg_subcategory = "Amazon"
    for c in cm.channels:
        if c['id'] == mock_msg['channel_id']:
            msg_category = c.get('category', 'US Stores')
            msg_subcategory = c.get('name', 'Amazon')
            break
            
    sql_country = "US"
    if "UK" in msg_category.upper(): sql_country = "UK"
    elif "CANADA" in msg_category.upper(): sql_country = "CA"
    
    success = supabase_utils.insert_alert(sql_country, msg_subcategory, product_meta)
    
    if success:
        print(f"🎉 SUCCESS! Alert synced to {sql_country} feed under {msg_subcategory}.")
        print("📲 You can now check your mobile app to see the new card.")
    else:
        print("❌ SQL Sync Failed.")

if __name__ == "__main__":
    simulate_deal()
