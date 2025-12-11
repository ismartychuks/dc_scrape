"""
WSGI entry point for production (Gunicorn)
Starts both Flask/SocketIO and Telegram bot in isolated threads
"""
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# NOTE: Eventlet removed to prevent conflict with Playwright Sync API
# We rely on Flask-SocketIO 'threading' mode which works with standard Gunicorn workers

from app import app, telegram_bot, run_archiver_logic_async

# Start Telegram Bot in background thread (isolated)
if os.getenv("TELEGRAM_TOKEN"):
    t_bot = threading.Thread(target=telegram_bot.run_bot, daemon=True)
    t_bot.start()

# Start archiver in a standard isolated thread
def start_archiver():
    # We use a standard thread instead of ThreadPoolExecutor to ensure
    # a clean context for Playwright without leftover async loops
    t_archiver = threading.Thread(target=run_archiver_logic_async, daemon=True)
    t_archiver.start()

# Start archiver immediately on startup
start_archiver()

# Export app for Gunicorn
# Command to run: gunicorn -w 1 --threads 100 wsgi:application
if __name__ != '__main__':
    application = app