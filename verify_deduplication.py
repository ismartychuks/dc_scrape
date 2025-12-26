import sys
import os
import json
from datetime import datetime

# Mock logger and supabase_utils since we're testing the logic, not the network
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def debug(self, msg): print(f"DEBUG: {msg}")

import logging
logger = MockLogger()

import hashlib

# Simplified versions of the functions from telegram_bot.py for testing
def parse_tag_line(tag: str):
    if not tag: return {}
    parts = [p.strip() for p in tag.split('|')]
    result = {'product_code': None, 'raw': tag}
    for part in parts:
        if not part.startswith('@') and not (part.startswith('[') and part.endswith(']')):
            if result['product_code'] is None: result['product_code'] = part
    return result

class MessagePoller:
    def __init__(self):
        self.sent_ids = set()
        self.recent_signatures = []

    def _get_content_signature(self, msg) -> str:
        try:
            raw = msg.get("raw_data", {})
            embed = raw.get("embed") or {}
            content = msg.get("content", "")
            
            retailer = ""
            if embed.get("author"):
                retailer = embed["author"].get("name", "")
            elif "Argos" in content:
                retailer = "Argos Instore"
            
            title = embed.get("title", "")
            if not title and content:
                tag_info = parse_tag_line(content)
                title = tag_info.get("product_code", "")
            
            price = ""
            fields = embed.get("fields", [])
            for f in fields:
                name = (f.get("name") or "").lower()
                if "price" in name:
                    price = f.get("value", "")
                    break
            
            raw_sig = f"{retailer}|{title}|{price}".lower().strip()
            return hashlib.md5(raw_sig.encode()).hexdigest()
        except Exception as e:
            return str(msg.get("id"))

    def filter_messages(self, messages):
        new_messages = []
        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id or msg_id in self.sent_ids:
                print(f"   Skipped ID: {msg_id}")
                continue
            
            sig = self._get_content_signature(msg)
            if sig in self.recent_signatures:
                print(f"   Skipped Signature Match: {msg_id} (Sig: {sig})")
                self.sent_ids.add(msg_id)
                continue

            new_messages.append(msg)
            self.sent_ids.add(msg_id)
        return new_messages

    def update_cursor(self, msg):
        sig = self._get_content_signature(msg)
        if sig not in self.recent_signatures:
            self.recent_signatures.append(sig)
            self.recent_signatures = self.recent_signatures[-3:]
        print(f"   Updated Signatures: {self.recent_signatures}")

# Test Cases
def run_test():
    poller = MessagePoller()
    
    # Message 1: Original
    msg1 = {
        "id": "101",
        "content": "Argos | Pokémon Box | £10",
        "raw_data": {"embed": {"title": "Pokémon Box", "fields": [{"name": "Price", "value": "£10"}]}}
    }
    
    # Message 2: Same content, different ID (Should be skipped if sent recently)
    msg2 = {
        "id": "102",
        "content": "Argos | Pokémon Box | £10",
        "raw_data": {"embed": {"title": "Pokémon Box", "fields": [{"name": "Price", "value": "£10"}]}}
    }
    
    # Message 3: Different content
    msg3 = {
        "id": "103",
        "content": "Argos | Zelda Box | £50",
        "raw_data": {"embed": {"title": "Zelda Box", "fields": [{"name": "Price", "value": "£50"}]}}
    }

    print("\n--- Cycle 1: Receive Msg 1 ---")
    new = poller.filter_messages([msg1])
    print(f"Found: {[m['id'] for m in new]}")
    if new: poller.update_cursor(new[0])

    print("\n--- Cycle 2: Receive Msg 2 (Duplicate Content) ---")
    new = poller.filter_messages([msg2])
    print(f"Found: {[m['id'] for m in new]} (EXPECTED EMPTY)")

    print("\n--- Cycle 3: Receive Msg 3 (New Content) ---")
    new = poller.filter_messages([msg3])
    print(f"Found: {[m['id'] for m in new]}")
    if new: poller.update_cursor(new[0])

    # Fill signature buffer with Msg 4, 5 to push out Msg 1
    msg4 = {"id": "104", "raw_data": {"embed": {"title": "Item 4", "fields": [{"name": "Price", "value": "1"}]}}}
    msg5 = {"id": "105", "raw_data": {"embed": {"title": "Item 5", "fields": [{"name": "Price", "value": "1"}]}}}
    
    print("\n--- Cycle 4: Push Msg 1 out of window ---")
    poller.update_cursor(msg4)
    poller.update_cursor(msg5)
    
    print("\n--- Cycle 5: Receive Msg 6 (Identical to Msg 1 but now allowed) ---")
    msg6 = {
        "id": "106",
        "content": "Argos | Pokémon Box | £10",
        "raw_data": {"embed": {"title": "Pokémon Box", "fields": [{"name": "Price", "value": "£10"}]}}
    }
    new = poller.filter_messages([msg6])
    print(f"Found: {[m['id'] for m in new]} (EXPECTED ALLOWED)")

if __name__ == "__main__":
    run_test()
