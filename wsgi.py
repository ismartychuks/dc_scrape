"""
WSGI entry point for production (Gunicorn)
Starts both Flask/SocketIO and Telegram bot
"""
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# Import after .env is loaded
from app import app, socketio, telegram_bot, run_archiver_logic, stop_event

# Start Telegram Bot in background thread
if os.getenv("TELEGRAM_TOKEN"):
    t_bot = threading.Thread(target=telegram_bot.run_bot, daemon=True)
    t_bot.start()

# Start archiver in background thread (auto-start on production)
def start_archiver():
    t_archiver = threading.Thread(target=run_archiver_logic, daemon=True)
    t_archiver.start()

# Start archiver immediately on startup
start_archiver()

# Export app for Gunicorn
if __name__ != '__main__':
    # Running under Gunicorn
    application = app
