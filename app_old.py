import os
import time
import json
import threading
import queue
import base64
import logging
import requests
import asyncio
import nest_asyncio
import subprocess
import hashlib
import re
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import supabase_utils
from dotenv import load_dotenv
load_dotenv()


# --- Apply Nest Asyncio Globally ---
nest_asyncio.apply()

# --- Configuration ---
CHANNELS = os.getenv("CHANNELS", "").split(",")
CHANNELS = [c.strip() for c in CHANNELS if c.strip()]

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

SUPABASE_BUCKET = "monitor-data"
UPLOAD_FOLDER = "discord_josh"
STORAGE_STATE_FILE = "storage_state.json"
LAST_MESSAGE_ID_FILE = "last_message_ids.json"
DATA_DIR = "data"

HEADLESS_MODE = os.getenv("HEADLESS", "True").lower() == "true"
# Debug mode - accepts True, true, 1, yes, YES
DEBUG_ENV = os.getenv("DEBUG", "").lower()
DEBUG_MODE = DEBUG_ENV in ("true", "1", "yes", "on")  # More flexible check
os.makedirs(DATA_DIR, exist_ok=True)

# --- Alert Configuration ---
ERROR_THRESHOLD = 5
ALERT_COOLDOWN = 1800

# --- Flask App Setup ---
app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- Global State ---
archiver_state = {
    "status": "STOPPED",
    "logs": [],
    "error_counts": {},
    "last_alert_time": {},
    "last_success_time": {}
}
stop_event = threading.Event()
input_queue = queue.Queue()
archiver_thread = None
thread_lock = threading.Lock()

if not CHANNELS:
    logging.error("ERROR: CHANNELS environment variable not set.")

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Discord Archiver Portal</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: monospace; background: #222; color: #eee; margin: 0; padding: 20px; }
        .container { display: flex; gap: 20px; }
        .controls { min-width: 250px; }
        .view { flex-grow: 1; text-align: center; }
        img { max-width: 100%; border: 1px solid #555; }
        .log-box { height: 400px; overflow-y: scroll; background: #111; border: 1px solid #333; padding: 10px; font-size: 11px; margin-top: 10px; }
        button { padding: 8px; width: 100%; margin-bottom: 5px; cursor: pointer; background: #444; color: white; border: none; }
        button:hover { background: #555; }
        .status { padding: 10px; text-align: center; font-weight: bold; margin-bottom: 15px; }
        .running { background: #2fdd2f; color: #000; }
        .stopped { background: #dd2f2f; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <div class="controls">
            <div id="status-display" class="status stopped">STOPPED</div>
            <button onclick="api('start')">Start Archiver</button>
            <button onclick="api('stop')">Stop Archiver</button>
            <button onclick="testStatus()">Check Status</button>
            <div id="stats" style="background: #111; padding: 10px; margin: 10px 0; font-size: 11px; border: 1px solid #333;"></div>
            <div class="log-box" id="logs"></div>
        </div>
        <div class="view">
            <h3>Live Browser View</h3>
            <img id="live-stream" src="" alt="Stream inactive" />
        </div>
    </div>
    <script>
        var socket = io();
        var img = document.getElementById('live-stream');
        var logs = document.getElementById('logs');
        var stats = document.getElementById('stats');
        
        socket.on('screenshot', data => img.src = 'data:image/jpeg;base64,' + data);
        socket.on('log', data => {
            var div = document.createElement('div');
            div.textContent = `[${new Date().toLocaleTimeString()}] ${data.message}`;
            logs.appendChild(div);
            logs.scrollTop = logs.scrollHeight;
        });
        socket.on('status_update', data => {
            var el = document.getElementById('status-display');
            el.textContent = data.status;
            el.className = 'status ' + (data.status === 'RUNNING' ? 'running' : 'stopped');
        });

        function api(cmd) { 
            fetch('/api/' + cmd, { method: 'POST' })
                .then(r => r.json())
                .then(d => console.log(d))
                .catch(e => console.error(e));
        }
        
        function testStatus() {
            fetch('/api/test', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    let html = '<b>Status Check:</b><br>';
                    html += 'Archiver: ' + data.archiver_status + '<br><br>';
                    html += '<b>Error Counts:</b><br>';
                    for (let [url, count] of Object.entries(data.error_counts || {})) {
                        html += url.split('/').pop() + ': ' + count + ' errors<br>';
                    }
                    html += '<br><b>Last Success:</b><br>';
                    for (let [url, time] of Object.entries(data.last_success || {})) {
                        html += url.split('/').pop() + ': ' + new Date(time).toLocaleTimeString() + '<br>';
                    }
                    stats.innerHTML = html;
                })
                .catch(e => stats.innerHTML = 'Error: ' + e);
        }
        
        img.onclick = function(e) {
            var rect = img.getBoundingClientRect();
            socket.emit('input', {
                type: 'click', 
                x: (e.clientX - rect.left) / rect.width,
                y: (e.clientY - rect.top) / rect.height
            });
        };
    </script>
</body>
</html>
"""

def log(message):
    print(f"[Scraper] {message}")
    archiver_state["logs"].append(message)
    if len(archiver_state["logs"]) > 50: archiver_state["logs"].pop(0)
    socketio.emit('log', {'message': message})

def should_send_alert(alert_type):
    last_alert = archiver_state["last_alert_time"].get(alert_type, 0)
    return time.time() - last_alert > ALERT_COOLDOWN

def send_telegram_alert(subject, body, alert_type=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_ADMIN_ID:
        log(f"📧 Alert: {subject} (Telegram not configured)")
        return
    if alert_type and not should_send_alert(alert_type):
        return
    
    text = f"⚠️ <b>ARCHIVER ALERT: {subject}</b>\n\n{body}"
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_ADMIN_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
        if response.status_code == 200:
            log(f"✅ Alert sent: {subject}")
            if alert_type:
                archiver_state["last_alert_time"][alert_type] = time.time()
    except Exception as e:
        log(f"❌ Alert error: {str(e)}")

def set_status(status):
    archiver_state["status"] = status
    socketio.emit('status_update', {'status': status})

def clean_text(text):
    if not text: return ""
    text = str(text).replace('\x00', '')
    return ' '.join(text.split()).encode('ascii', 'ignore').decode('ascii')

async def save_message_html_for_inspection(message_element, message_id):
    """
    Save raw HTML of a Discord message to a file for inspection.
    This helps us understand the exact structure Discord uses.
    """
    try:
        html = await message_element.inner_html()
        filename = f"data/message_inspection_{message_id}.html"
        os.makedirs("data", exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Message ID: {message_id} -->\n")
            f.write(f"<!-- Timestamp: {datetime.utcnow().isoformat()} -->\n")
            f.write(f"<!-- File saved for HTML structure analysis -->\n")
            f.write(html)
        log(f"   💾 Saved HTML inspection: data/message_inspection_{message_id}.html ({len(html)} bytes)")
        return filename
    except Exception as e:
        log(f"   ⚠️ Could not save HTML inspection: {e}")
        return None

def track_channel_error(channel_url, error_msg):
    archiver_state["error_counts"][channel_url] = archiver_state["error_counts"].get(channel_url, 0) + 1
    if archiver_state["error_counts"][channel_url] >= ERROR_THRESHOLD:
        alert_type = f"channel_error_{channel_url}"
        send_telegram_alert(f"Channel Access Failed", f"Channel: {channel_url}\nError: {error_msg}", alert_type)

def track_channel_success(channel_url):
    archiver_state["error_counts"][channel_url] = 0
    archiver_state["last_success_time"][channel_url] = datetime.utcnow().isoformat()

def generate_content_hash(content_dict):
    """Generate unique hash for message content to detect duplicates"""
    content_str = json.dumps(content_dict, sort_keys=True)
    return hashlib.md5(content_str.encode()).hexdigest()

def extract_markdown_links(text):
    """
    Extract markdown-style links from Discord text.
    Format: [Link Text](https://url.com)
    """
    if not text:
        return []
    
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = []
    
    for match in re.finditer(pattern, text):
        link_text = match.group(1).strip()
        link_url = match.group(2).strip()
        
        if link_url.startswith('http'):
            links.append({
                'text': link_text,
                'url': link_url
            })
    
    return links

# --- AUTO-INSTALLER ---
def ensure_browsers_installed():
    """Checks for browsers and installs them if missing"""
    log("🔧 Checking Playwright browsers...")
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        log("✅ Browsers ready.")
    except Exception as e:
        log(f"⚠️ Browser install warning: {e}")

# --- ENHANCED EMBED EXTRACTION ---
async def extract_embed_data(message_element):
    """
    Extract structured embed data from Discord message.
    UPDATED: Uses correct selectors from actual Discord HTML structure
    """
    embed_data = {
        "title": None,
        "description": None,
        "fields": [],
        "images": [],
        "thumbnail": None,
        "color": None,
        "author": None,
        "footer": None,
        "timestamp": None,
        "links": []
    }
    
    try:
        # Find embed article (uses randomized class names like _623de82e76ad7f82-embedFull)
        embed = message_element.locator('article[class*="embedFull"]').first
        if await embed.count() == 0:
            # Fallback: Try generic embed selector
            embed = message_element.locator('article[class*="embed"]').first
        if await embed.count() == 0:
            return None
        
        # Extract embed color (border-left-color)
        try:
            color_style = await embed.get_attribute('style')
            if color_style and 'border-left-color' in color_style:
                embed_data["color"] = color_style
        except: pass
        
        # Extract embed author
        try:
            author_elem = embed.locator('div[class*="embedAuthor"] a').first
            if await author_elem.count() > 0:
                author_name = await author_elem.inner_text()
                author_url = await author_elem.get_attribute('href')
                embed_data["author"] = {"name": clean_text(author_name), "url": author_url}
                if author_url and author_url not in [l.get("url") for l in embed_data["links"]]:
                    embed_data["links"].append({"type": "author", "text": clean_text(author_name), "url": author_url})
        except: pass
        
        # Extract embed title
        try:
            title_elem = embed.locator('div[class*="embedTitle"] a').first
            if await title_elem.count() > 0:
                title_text = await title_elem.inner_text()
                title_url = await title_elem.get_attribute('href')
                embed_data["title"] = clean_text(title_text)
                
                # Add title as link
                if title_url and title_url not in [l.get("url") for l in embed_data["links"]]:
                    embed_data["links"].append({"type": "title", "text": embed_data["title"], "url": title_url})
        except: pass
        
        # Extract embed fields (Price, Stock, Links, etc.) - CRITICAL
        try:
            field_containers = embed.locator('div[class*="embedField"]')
            field_count = await field_containers.count()
            
            for i in range(field_count):
                field = field_containers.nth(i)
                
                # Get field name
                field_name_elem = field.locator('div[class*="embedFieldName"]').first
                field_name = ""
                if await field_name_elem.count() > 0:
                    field_name = await field_name_elem.inner_text()
                    field_name = clean_text(field_name)
                
                # Get field value (can contain links and text)
                field_value_elem = field.locator('div[class*="embedFieldValue"]').first
                field_value = ""
                if await field_value_elem.count() > 0:
                    field_value = await field_value_elem.inner_text()
                    field_value = clean_text(field_value)
                
                # Only add non-empty fields
                if field_name or field_value:
                    embed_data["fields"].append({
                        "name": field_name,
                        "value": field_value
                    })
                    
                    # Extract links from field value (for Links field, ATC field, etc.)
                    try:
                        value_links = field_value_elem.locator('a[href]')
                        link_count = await value_links.count()
                        
                        for j in range(link_count):
                            link_elem = value_links.nth(j)
                            href = await link_elem.get_attribute('href')
                            text = await link_elem.inner_text()
                            
                            if href and href not in [l.get("url") for l in embed_data["links"]]:
                                embed_data["links"].append({
                                    "field": field_name,
                                    "text": clean_text(text),
                                    "url": href
                                })
                    except: pass
        except: pass
        
        # Extract embed thumbnail
        try:
            thumb_elem = embed.locator('[class*="embedThumbnail"] img').first
            if await thumb_elem.count() > 0:
                thumb_src = await thumb_elem.get_attribute('src')
                if thumb_src:
                    embed_data["images"].append(thumb_src)
        except: pass
        
        # Extract footer
        try:
            footer_elem = embed.locator('div[class*="embedFooter"]')
            if await footer_elem.count() > 0:
                footer_text = await footer_elem.inner_text()
                embed_data["footer"] = clean_text(footer_text)
        except: pass
        
        # Return if we found anything
        return embed_data if any([embed_data["title"], embed_data["fields"], embed_data["links"]]) else None
        
    except Exception as e:
        log(f"   ⚠️ Embed extraction error: {e}")
        return None

async def extract_message_author(message_element):
    """Extract message author info"""
    try:
        # Look for author in header
        author_elem = message_element.locator('h3[class*="header"] span[class*="username"]').first
        if await author_elem.count() > 0:
            author_name = await author_elem.inner_text()
            
            # Check for bot badge
            is_bot = await message_element.locator('span[class*="botTag"]').count() > 0
            
            # Get avatar if available
            avatar_elem = message_element.locator('img[class*="avatar"]').first
            avatar_url = await avatar_elem.get_attribute('src') if await avatar_elem.count() > 0 else None
            
            return {
                "name": clean_text(author_name),
                "is_bot": is_bot,
                "avatar": avatar_url
            }
    except: pass
    
    return {"name": "Unknown", "is_bot": False, "avatar": None}

# --- ASYNC LOGIC ---
async def wait_for_messages_to_load(page):
    SELECTORS = [
        'li[id^="chat-messages-"]',
        '[class*="message-"][class*="cozy"]',
        '[id^="message-content-"]',
        'div[class*="messageContent-"]',
        '[data-list-item-id^="chat-messages"]',
    ]
    
    log("   🔍 Waiting for messages to load...")
    try:
        await page.wait_for_selector('main[class*="chatContent"], div[class*="chat-"]', timeout=5000)
    except: pass
    
    for attempt in range(3):
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.5)
        for selector in SELECTORS:
            try:
                elements = page.locator(selector)
                if await elements.count() > 0:
                    return selector, elements
            except: continue
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)
    
    return None, None

async def detect_account_picker(page):
    """Detect if Discord is showing account picker"""
    selectors = [
        'button[class*="userButton"]',
        '[class*="accountPicker"]',
        '[class*="SelectAccount"]',
        'div:has-text("Select Account")',
        'div:has-text("Which account?")',
    ]
    
    for selector in selectors:
        try:
            if await page.locator(selector).count() > 0:
                return True
        except: pass
    
    return False

async def async_archiver_logic():
    """Enhanced Discord scraper with FULL embed + markdown link extraction"""
    log("🚀 Advanced Scraper Started - Professional Alert Mode")
    
    # Show debug status
    if DEBUG_MODE:
        log("🐛 DEBUG MODE ENABLED - Saving HTML files to data/message_inspection_*.html")
    else:
        log("📝 Debug mode OFF. Set DEBUG=True to capture HTML for analysis")
    
    state_path = os.path.join(DATA_DIR, STORAGE_STATE_FILE)
    remote_state_path = f"{UPLOAD_FOLDER}/{STORAGE_STATE_FILE}"
    last_ids_path = os.path.join(DATA_DIR, LAST_MESSAGE_ID_FILE)
    
    try:
        data = supabase_utils.download_file(state_path, remote_state_path, SUPABASE_BUCKET)
        if data: log("✅ Session restored.")
    except: pass

    last_ids = {}
    if os.path.exists(last_ids_path):
        try:
            with open(last_ids_path, 'r') as f: last_ids = json.load(f)
        except: pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS_MODE, 
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            storage_state=state_path if os.path.exists(state_path) else None
        )
        page = await context.new_page()
        set_status("RUNNING")

        while not stop_event.is_set():
            try:
                # Login Logic
                if "login" in page.url or "discord.com/channels" not in page.url:
                    log("🔐 Login required...")
                    try: await page.goto("https://discord.com/login", timeout=10000)
                    except: pass
                    
                    account_picker_detected = await detect_account_picker(page)
                    if account_picker_detected:
                        log("👤 Account picker detected - interactive mode active")
                        send_telegram_alert("Account Picker", "Discord requires account selection. Web UI active for manual selection.", "warning")
                    
                    wait_cycles = 0
                    while wait_cycles < 120 and not stop_event.is_set():
                        try:
                            scr = await page.screenshot(quality=40, type='jpeg')
                            socketio.emit('screenshot', base64.b64encode(scr).decode('utf-8'))
                        except: pass
                        
                        try:
                            while not input_queue.empty():
                                act = input_queue.get_nowait()
                                if act['type'] == 'click':
                                    vp = page.viewport_size
                                    await page.mouse.click(act['x'] * vp['width'], act['y'] * vp['height'])
                        except: pass
                        
                        if "discord.com/channels" in page.url and "/login" not in page.url:
                            await context.storage_state(path=state_path)
                            supabase_utils.upload_file(state_path, SUPABASE_BUCKET, remote_state_path, debug=False)
                            log("✅ Login success!")
                            break
                        
                        await asyncio.sleep(5)
                        wait_cycles += 1
                        if wait_cycles % 10 == 0: log(f"⏳ Waiting... {wait_cycles*5}s")

                # Channel Scraping with FULL EMBED + MARKDOWN LINK EXTRACTION
                for channel_url in CHANNELS:
                    if stop_event.is_set(): break
                    log(f"📂 Scanning: {channel_url}...")
                    
                    try:
                        await page.goto(channel_url, timeout=30000)
                        await asyncio.sleep(2)
                        
                        try:
                            scr = await page.screenshot(quality=40, type='jpeg')
                            socketio.emit('screenshot', base64.b64encode(scr).decode('utf-8'))
                        except: pass
                        
                        selector, messages = await wait_for_messages_to_load(page)
                        if not messages:
                            log("   ⚠️ No messages found")
                            track_channel_error(channel_url, "No messages")
                            continue
                            
                        count = await messages.count()
                        batch = []
                        current_ids = last_ids.get(channel_url, [])
                        
                        # Process last 10 messages
                        debug_saved = False  # Only save one message per channel for inspection
                        for i in range(max(0, count - 10), count):
                            msg = messages.nth(i)
                            raw_id = await msg.get_attribute('id') or await msg.get_attribute('data-list-item-id')
                            if not raw_id: continue
                            
                            msg_id = raw_id.replace('chat-messages-', '').replace('message-', '')
                            if msg_id in current_ids: continue
                            
                            # DEBUG: Save first message HTML for inspection
                            if DEBUG_MODE and not debug_saved:
                                await save_message_html_for_inspection(msg, msg_id)
                                debug_saved = True
                            
                            # Extract message author
                            author_data = await extract_message_author(msg)
                            
                            # CRITICAL: Try to extract FULL embed data with markdown links
                            embed_data = await extract_embed_data(msg)
                            
                            # Extract plain text content as fallback
                            content_loc = msg.locator('[id^="message-content-"]').first
                            plain_content = await content_loc.inner_text() if await content_loc.count() else ""
                            
                            # Build message data structure
                            message_data = {
                                "id": int(msg_id) if msg_id.isdigit() else abs(hash(msg_id)) % (10 ** 15),
                                "channel_id": channel_url.split('/')[-1],
                                "content": clean_text(plain_content),
                                "scraped_at": datetime.utcnow().isoformat(),
                                "raw_data": {
                                    "author": author_data,
                                    "channel_url": channel_url,
                                    "embed": embed_data,
                                    "has_embed": embed_data is not None
                                }
                            }
                            
                            # Generate content hash for deduplication
                            hash_content = {
                                "content": plain_content,
                                "embed_title": embed_data.get("title") if embed_data else None,
                                "embed_desc": embed_data.get("description") if embed_data else None
                            }
                            message_data["raw_data"]["content_hash"] = generate_content_hash(hash_content)
                            
                            batch.append(message_data)
                            current_ids.append(msg_id)
                            
                            # Log what we extracted
                            if embed_data:
                                log(f"   ✅ Extracted embed: {embed_data.get('title', 'No title')[:50]}...")
                                if embed_data.get('images'):
                                    log(f"      🖼️ Found {len(embed_data['images'])} image(s)")
                                if embed_data.get('links'):
                                    log(f"      🔗 Found {len(embed_data['links'])} link(s)")
                                if embed_data.get('fields'):
                                    log(f"      📋 Found {len(embed_data['fields'])} field(s)")
                            else:
                                log(f"   📝 Plain message: {plain_content[:50]}...")

                        if batch:
                            log(f"   ⬆️ Uploading {len(batch)} message(s)")
                            supabase_utils.insert_discord_messages(batch)
                            last_ids[channel_url] = current_ids[-200:]
                            with open(last_ids_path, 'w') as f: json.dump(last_ids, f)
                        
                        track_channel_success(channel_url)
                        await asyncio.sleep(1)

                    except Exception as e:
                        log(f"   ⚠️ Error: {str(e)}")
                        track_channel_error(channel_url, str(e))

                log("💤 Sleeping 30s...")
                for _ in range(30):
                    if stop_event.is_set(): break
                    await asyncio.sleep(1)

            except Exception as e:
                log(f"💥 Critical Error: {e}")
                await asyncio.sleep(10)
        
        if context:
            await context.close()
        if browser:
            await browser.close()
        log("✅ Browser session closed.")
    
    set_status("STOPPED")

def run_archiver_thread_wrapper():
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    
    ensure_browsers_installed()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_archiver_logic())
        loop.close()
    except Exception as e:
        log(f"FATAL WRAPPER ERROR: {e}")
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(async_archiver_logic(), loop)
        except:
            pass

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/api/start', methods=['POST'])
def start_worker():
    global archiver_thread
    with thread_lock:
        if archiver_thread and archiver_thread.is_alive():
            return jsonify({"status": "already_running"}), 409
        stop_event.clear()
        archiver_thread = threading.Thread(target=run_archiver_thread_wrapper, daemon=True)
        archiver_thread.start()
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def stop_worker():
    stop_event.set()
    return jsonify({"status": "stopping"})

@app.route('/api/test', methods=['POST'])
def test_channel():
    if not archiver_thread or not archiver_thread.is_alive():
        return jsonify({"status": "error", "message": "Archiver not running"}), 400
    return jsonify({
        "status": "ok",
        "error_counts": archiver_state["error_counts"],
        "archiver_status": archiver_state["status"],
        "last_success": archiver_state["last_success_time"]
    })

@app.route('/health')
def health(): return jsonify({"status": "ok"})

@socketio.on('input')
def handle_input(data): input_queue.put(data)


if __name__ == '__main__':
    import telegram_bot
    if os.getenv("TELEGRAM_TOKEN"):
        t_bot = threading.Thread(target=telegram_bot.run_bot, daemon=True)
        t_bot.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)