import os
import json
import logging
from telegram_bot import ChannelManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def perform_initial_sync():
    print("🚀 Starting Initial Channel to SQL Sync...")
    
    # Initialize ChannelManager (this will reload data/channels.json and sync to SQL)
    cm = ChannelManager()
    
    # Force a sync
    cm._sync_state()
    
    print("✅ Initial sync complete! Existing channels should now appear as filters in the mobile app.")

if __name__ == "__main__":
    perform_initial_sync()
