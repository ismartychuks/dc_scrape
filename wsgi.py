"""
WSGI entry point for production (Gunicorn)
"""
import os
import threading
import time
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🚀 DISCORD TELEGRAM ALERT BOT - STARTING")
print("=" * 80)

# Import Flask app first
from app import app

# Start Telegram Bot in background thread
if os.getenv("TELEGRAM_TOKEN"):
    import telegram_bot
    
    def run_telegram_safe():
        try:
            print("\n📡 Starting Telegram bot polling...")
            print("   Token:", os.getenv("TELEGRAM_TOKEN")[:10] + "...")
            telegram_bot.run_bot()
        except KeyboardInterrupt:
            print("\n⚠️  Telegram bot interrupted")
            sys.exit(0)
        except Exception as e:
            import traceback
            print(f"\n❌ Telegram bot critical error: {e}")
            print(traceback.format_exc())
            sys.exit(1)
    
    print("\n🔧 Spawning Telegram bot thread...")
    t_bot = threading.Thread(target=run_telegram_safe, daemon=True, name="TelegramBot")
    t_bot.start()
    time.sleep(0.5)  # Give thread time to start
    
    if t_bot.is_alive():
        print("✅ Telegram bot thread started successfully")
    else:
        print("⚠️  WARNING: Telegram bot thread exited immediately")
else:
    print("⚠️  WARNING: TELEGRAM_TOKEN not set - bot will not start")

print("\n🌐 Flask application ready")
print("=" * 80 + "\n")

# Export application for Gunicorn
if __name__ != '__main__':
    application = app
else:
    app.run(host='0.0.0.0', port=5000)