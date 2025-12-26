import sys
import os
import json
from datetime import datetime, timedelta

# Mock dependencies
class MockSupabase:
    def get_supabase_config(self): return "url", "key"
    def download_file(self, local, remote, bucket): return None
    def upload_file(self, local, bucket, remote, debug=False): pass

sys.modules['supabase_utils'] = MockSupabase()

import logging
logger = logging.getLogger(__name__)

# Mock the datetime parsing utility
def parse_iso_datetime(iso_string):
    return datetime.fromisoformat(iso_string)

# Import the class (assuming we can import from the file or we copy the logic)
# For isolation, I'll copy the relevant logic from telegram_bot.py into this test script
class SubscriptionManager:
    def __init__(self):
        self.users = {}
        self.codes = {"TESTCODE": 30}
        self.potential_users = {}
        import threading
        self.lock = threading.Lock()
        
    def _sync_state(self): pass # Mock sync

    def track_potential_user(self, user_id, username):
        uid = str(user_id)
        if uid not in self.users and uid not in self.potential_users:
            self.potential_users[uid] = {
                "username": username or "Unknown",
                "first_seen": datetime.utcnow().isoformat(),
                "last_reminder": None
            }
            print(f"   [Added Potential] {uid}")

    def redeem_code(self, user_id, username, code):
        uid = str(user_id)
        if code in self.codes:
            self.codes.pop(code)
            self.users[uid] = {"expiry": (datetime.utcnow() + timedelta(days=30)).isoformat()}
            if uid in self.potential_users:
                self.potential_users.pop(uid)
                print(f"   [Removed from Potential] {uid}")
            return True
        return False

    def get_potential_users_needing_reminder(self):
        needing_reminder = []
        now = datetime.utcnow()
        for uid, data in self.potential_users.items():
            last_reminder_str = data.get("last_reminder")
            if not last_reminder_str:
                first_seen = parse_iso_datetime(data["first_seen"])
                if (now - first_seen).days >= 14:
                    needing_reminder.append(uid)
            else:
                last_reminder = parse_iso_datetime(last_reminder_str)
                if (now - last_reminder).days >= 14:
                    needing_reminder.append(uid)
        return needing_reminder

def run_test():
    sm = SubscriptionManager()
    
    print("--- Test 1: New user /start ---")
    sm.track_potential_user("123", "Josh")
    assert "123" in sm.potential_users
    
    print("--- Test 2: User subscribes ---")
    sm.redeem_code("123", "Josh", "TESTCODE")
    assert "123" not in sm.potential_users
    assert "123" in sm.users
    
    print("--- Test 3: Reminder timing ---")
    sm.track_potential_user("456", "Potential")
    # Manually set first_seen to 15 days ago
    sm.potential_users["456"]["first_seen"] = (datetime.utcnow() - timedelta(days=15)).isoformat()
    needing = sm.get_potential_users_needing_reminder()
    assert "456" in needing
    print(f"   Users needing reminder: {needing}")

    print("--- Test 4: Already subscribed user /start ---")
    sm.track_potential_user("123", "Josh") # Already in users
    assert "123" not in sm.potential_users
    print("   User 123 correctly ignored as potential (already subscribed)")

    print("\n[SUCCESS] All logic tests passed!")

if __name__ == "__main__":
    run_test()
