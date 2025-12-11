"""
WSGI entry point for production (Gunicorn)
Starts both Flask/SocketIO and Telegram bot
"""
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# Import after .env is loaded
from app import app, socketio, telegram_bot

# Start Telegram Bot in background thread
if os.getenv("TELEGRAM_TOKEN"):
    t_bot = threading.Thread(target=telegram_bot.run_bot, daemon=True)
    t_bot.start()

# Export app for Gunicorn
if __name__ != '__main__':
    # Running under Gunicorn
    application = app
