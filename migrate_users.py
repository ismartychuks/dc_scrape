#!/usr/bin/env python3
"""
migrate_users.py
Migrates user data from data/bot_users.json to Supabase SQL tables.
"""

import json
import os
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any
from supabase_utils import get_supabase_config, sanitize_text

# Path to the old JSON data
JSON_PATH = os.path.join("data", "bot_users.json")

def migrate_to_supabase():
    if not os.path.exists(JSON_PATH):
        print(f"[ERROR] JSON file not found at {JSON_PATH}")
        return

    with open(JSON_PATH, "r") as f:
        old_data = json.load(f)

    url, key = get_supabase_config()
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation' # We need the ID back
    }

    print(f"--- Found {len(old_data)} users. Starting migration...")

    for telegram_id, data in old_data.items():
        try:
            # 1. Prepare User Data
            expiry_str = data.get("expiry")
            subscription_end = None
            status = "free"
            
            if expiry_str:
                subscription_end = expiry_str
                expiry_dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                if expiry_dt.tzinfo is None:
                    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                if expiry_dt > datetime.now(timezone.utc):
                    status = "active"
                else:
                    status = "expired"

            # Build user record
            user_record = {
                "subscription_status": status,
                "subscription_source": "stripe" if data.get("stripe_customer_id") else "manual",
                "subscription_end": subscription_end,
                "stripe_customer_id": data.get("stripe_customer_id"),
                "stripe_subscription_id": data.get("stripe_subscription_id"),
                "created_at": data.get("joined_at", datetime.now(timezone.utc).isoformat()),
                "notification_preferences": {
                    "subscribed_categories": data.get("subscribed_categories", []),
                    "disabled_subcategories": data.get("disabled_subcategories", [])
                }
            }

            # Insert User
            user_response = requests.post(
                f"{url}/rest/v1/users",
                headers=headers,
                data=json.dumps(user_record),
                timeout=30
            )

            if user_response.status_code in [200, 201]:
                user_id = user_response.json()[0]["id"]
                print(f"   [OK] Created user for TG:{telegram_id} (UUID: {user_id})")
                
                # 2. Link Telegram Account
                link_record = {
                    "user_id": user_id,
                    "telegram_id": str(telegram_id),
                    "telegram_username": data.get("username"),
                    "linked_at": datetime.now(timezone.utc).isoformat()
                }
                
                link_response = requests.post(
                    f"{url}/rest/v1/user_telegram_links",
                    headers={**headers, 'Prefer': 'resolution=ignore-duplicates'},
                    data=json.dumps(link_record),
                    timeout=30
                )
                
                if link_response.status_code in [200, 201, 204]:
                    print(f"      [LINK] Linked TG:{telegram_id}")
                else:
                    print(f"      [ERROR] Link failed for TG:{telegram_id}: {link_response.text}")
            else:
                print(f"   [ERROR] Failed to create user for TG:{telegram_id}: {user_response.text}")

        except Exception as e:
            print(f"   [ERROR] Error migrating TG:{telegram_id}: {e}")

    print("\n[COMPLETE] Migration complete!")

if __name__ == "__main__":
    migrate_to_supabase()
