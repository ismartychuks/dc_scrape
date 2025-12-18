import os
import json
import logging
import threading
import traceback
import requests
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import supabase_utils
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = os.getenv("TELEGRAM_ADMIN_ID")
SUPABASE_BUCKET = "monitor-data"
USERS_FILE = "bot_users.json"
CODES_FILE = "active_codes.json"
POLL_INTERVAL = 35  # Check every 35 seconds (increased to prevent job overlap - broadcasts take time to send to multiple users)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- DATETIME PARSING UTILITY ---

def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse ISO format datetime string with flexible microseconds.
    Handles variable-length microsecond strings (3-6 digits).
    """
    if not iso_string:
        return datetime.utcnow()
    
    try:
        # Try direct parsing first
        return datetime.fromisoformat(iso_string)
    except ValueError:
        # Handle variable-length microseconds
        try:
            if "." in iso_string:
                parts = iso_string.split(".")
                if "+" in parts[1]:
                    ms, tz = parts[1].split("+")
                    ms = (ms + "000000")[:6]  # Pad or truncate to 6 digits
                    fixed_str = f"{parts[0]}.{ms}+{tz}"
                elif "-" in parts[1] and parts[1].count("-") > 0:
                    ms, tz = parts[1].rsplit("-", 1)
                    ms = (ms + "000000")[:6]
                    fixed_str = f"{parts[0]}.{ms}-{tz}"
                else:
                    # No timezone
                    ms = (parts[1] + "000000")[:6]
                    fixed_str = f"{parts[0]}.{ms}"
                return datetime.fromisoformat(fixed_str)
        except:
            pass
    
    # Fallback
    return datetime.utcnow()

# --- LINK PARSING UTILITIES ---

def extract_markdown_links(text: str) -> List[Dict[str, str]]:
    """Extract markdown-style links from text"""
    if not text:
        return []
    
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = []
    
    for match in re.finditer(pattern, text):
        link_text = match.group(1).strip()
        link_url = match.group(2).strip()
        
        if link_url.startswith('http'):
            links.append({'text': link_text, 'url': link_url})
    
    return links


def categorize_links(links: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Categorize links into eBay, FBA, Buy, Other"""
    categories = {'ebay': [], 'fba': [], 'buy': [], 'other': []}
    
    ebay_keywords = ['sold', 'active', 'google', 'ebay']
    fba_keywords = ['keepa', 'amazon', 'selleramp', 'fba', 'camel']
    buy_keywords = ['buy', 'shop', 'purchase', 'checkout', 'cart']
    
    for link in links:
        text_lower = link['text'].lower()
        url_lower = link['url'].lower()
        
        if any(kw in text_lower or kw in url_lower for kw in ebay_keywords):
            categories['ebay'].append(link)
        elif any(kw in text_lower or kw in url_lower for kw in fba_keywords):
            categories['fba'].append(link)
        elif any(kw in text_lower or kw in url_lower for kw in buy_keywords):
            categories['buy'].append(link)
        else:
            categories['other'].append(link)
    
    return categories


def add_emoji_to_link_text(text: str) -> str:
    """Add emoji prefix to link text for better visual appeal"""
    emojis = {
        'sold': '💰', 'active': '⚡', 'google': '🔍', 'ebay': '🛒',
        'keepa': '📈', 'amazon': '🔎', 'selleramp': '💎', 'camel': '🐫',
        'buy': '🛒', 'shop': '🏪', 'cart': '🛒', 'checkout': '✅',
    }
    
    text_lower = text.lower()
    for keyword, emoji in emojis.items():
        if keyword in text_lower:
            return f"{emoji} {text}"
    
    return f"🔗 {text}"


def parse_tag_line(tag: str) -> Dict[str, Optional[str]]:
    """
    Parse Discord tag line above embeds.
    Example: "@Product Flips | [UK] CRW-001-1ER | Casio | Just restocked for £0.00"
    """
    if not tag:
        return {}
    
    parts = [p.strip() for p in tag.split('|')]
    result = {
        'ping': None, 'region': None, 'product_code': None,
        'brand': None, 'action': None, 'price': None, 'raw': tag
    }
    
    for part in parts:
        if part.startswith('@'):
            result['ping'] = part
        elif part.startswith('[') and part.endswith(']'):
            result['region'] = part.strip('[]')
        elif any(kw in part.lower() for kw in ['restocked', 'in stock', 'available']):
            result['action'] = part
            price_match = re.search(r'[£$€]\s*[\d,]+\.?\d*', part)
            if price_match:
                result['price'] = price_match.group(0)
        else:
            if result['product_code'] is None:
                result['product_code'] = part
            elif result['brand'] is None:
                result['brand'] = part
    
    return result


# --- SUBSCRIPTION MANAGER ---

class SubscriptionManager:
    def __init__(self):
        self.users: Dict[str, Dict] = {} 
        self.codes: Dict[str, int] = {}
        self.lock = threading.Lock()
        self.remote_users_path = f"discord_josh/{USERS_FILE}"
        self.remote_codes_path = f"discord_josh/{CODES_FILE}"
        self.local_users_path = f"data/{USERS_FILE}"
        self.local_codes_path = f"data/{CODES_FILE}"
        os.makedirs("data", exist_ok=True)
        self._load_state()

    def _load_state(self):
        try:
            data = supabase_utils.download_file(self.local_users_path, self.remote_users_path, SUPABASE_BUCKET)
            if data: self.users = json.loads(data)
        except: pass
        try:
            data = supabase_utils.download_file(self.local_codes_path, self.remote_codes_path, SUPABASE_BUCKET)
            if data: self.codes = json.loads(data)
        except: pass

    def _sync_state(self):
        try:
            with open(self.local_users_path, 'w') as f: json.dump(self.users, f)
            supabase_utils.upload_file(self.local_users_path, SUPABASE_BUCKET, self.remote_users_path, debug=False)
            with open(self.local_codes_path, 'w') as f: json.dump(self.codes, f)
            supabase_utils.upload_file(self.local_codes_path, SUPABASE_BUCKET, self.remote_codes_path, debug=False)
        except Exception as e:
            logger.error(f"Sync error: {e}")

    def generate_code(self, days: int) -> str:
        import secrets
        code = secrets.token_hex(4).upper()
        with self.lock:
            self.codes[code] = days
            self._sync_state()
        return code

    def redeem_code(self, user_id: str, username: str, code: str) -> bool:
        with self.lock:
            if code not in self.codes: return False
            days = self.codes.pop(code)
            current_expiry = datetime.utcnow()
            if str(user_id) in self.users:
                try:
                    old_expiry = parse_iso_datetime(self.users[str(user_id)]["expiry"])
                    if old_expiry > datetime.utcnow(): current_expiry = old_expiry
                except: pass
            
            new_expiry = current_expiry + timedelta(days=days)
            self.users[str(user_id)] = {
                "expiry": new_expiry.isoformat(), 
                "username": username or "Unknown",
                "alerts_paused": False,
                "joined_at": self.users.get(str(user_id), {}).get("joined_at", datetime.utcnow().isoformat())
            }
            self._sync_state()
            return True

    def get_active_users(self) -> List[str]:
        active = []
        now = datetime.utcnow()
        with self.lock:
            for uid, data in self.users.items():
                try:
                    if parse_iso_datetime(data["expiry"]) > now:
                        if not data.get("alerts_paused", False):
                            active.append(uid)
                except: pass
        return active
    
    def get_expiry(self, user_id: str):
        return self.users.get(str(user_id), {}).get("expiry")
    
    def is_active(self, user_id: str) -> bool:
        expiry = self.get_expiry(str(user_id))
        if not expiry: return False
        try:
            return parse_iso_datetime(expiry) > datetime.utcnow()
        except:
            return False
    
    def toggle_pause(self, user_id: str) -> bool:
        """Toggle pause status, returns new paused state"""
        with self.lock:
            if str(user_id) not in self.users:
                return False
            current = self.users[str(user_id)].get("alerts_paused", False)
            self.users[str(user_id)]["alerts_paused"] = not current
            self._sync_state()
            return not current
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        user_data = self.users.get(str(user_id), {})
        if not user_data:
            return None
        
        expiry = parse_iso_datetime(user_data["expiry"])
        joined = parse_iso_datetime(user_data.get("joined_at", datetime.utcnow().isoformat()))
        now = datetime.utcnow()
        
        return {
            "username": user_data.get("username", "Unknown"),
            "days_remaining": (expiry - now).days if expiry > now else 0,
            "days_active": (now - joined).days,
            "is_paused": user_data.get("alerts_paused", False),
            "expiry_date": expiry.strftime("%Y-%m-%d %H:%M UTC")
        }


# --- MESSAGE POLLER ---

class MessagePoller:
    def __init__(self):
        self.last_scraped_at = None
        self.sent_hashes = set()
        self.supabase_url, self.supabase_key = supabase_utils.get_supabase_config()
        self.cursor_file = "bot_cursor.json"
        self.local_path = f"data/{self.cursor_file}"
        self.remote_path = f"discord_josh/{self.cursor_file}"
        self._init_cursor()

    def _init_cursor(self):
        try:
            data = supabase_utils.download_file(self.local_path, self.remote_path, SUPABASE_BUCKET)
            if data: 
                loaded = json.loads(data)
                self.last_scraped_at = loaded.get("last_scraped_at")
                self.sent_hashes = set(loaded.get("sent_hashes", []))
            if not self.last_scraped_at: 
                self.last_scraped_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        except:
            self.last_scraped_at = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    def _save_cursor(self):
        try:
            with open(self.local_path, 'w') as f: 
                json.dump({
                    "last_scraped_at": self.last_scraped_at,
                    "sent_hashes": list(self.sent_hashes)[-1000:]
                }, f)
            supabase_utils.upload_file(self.local_path, SUPABASE_BUCKET, self.remote_path, debug=False)
        except: pass

    def poll_new_messages(self):
        try:
            if not self.last_scraped_at: 
                self.last_scraped_at = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            
            headers = {"apikey": self.supabase_key, "Authorization": f"Bearer {self.supabase_key}"}
            url = f"{self.supabase_url}/rest/v1/discord_messages"
            params = {"scraped_at": f"gt.{self.last_scraped_at}", "order": "scraped_at.asc"}
            
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code != 200: return []
            
            messages = res.json()
            
            # Filter duplicates by content hash
            new_messages = []
            for msg in messages:
                content_hash = msg.get("raw_data", {}).get("content_hash")
                if content_hash and content_hash not in self.sent_hashes:
                    new_messages.append(msg)
                    self.sent_hashes.add(content_hash)
            
            if messages and isinstance(messages, list):
                self.last_scraped_at = messages[-1].get('scraped_at')
                self._save_cursor()
            
            return new_messages
        except Exception as e:
            logger.error(f"Poll error: {e}")
            return []


sm = SubscriptionManager()
poller = MessagePoller()


# --- PROFESSIONAL MESSAGE FORMATTING ---

# Phrases to remove from messages
PHRASES_TO_REMOVE = [
    "CCN 2.0 | Profitable Pinger",
    " Monitors v2.0.0 | CCN x Zephyr Monitors #ad",
    " Monitors v2.0.0 | CCN x Zephyr Monitors",
    "CCN 2.0 | Profitable Pinger",
    "@Unfiltered",
    "CCN"
]

# Regex patterns to remove (for dynamic content like timestamps)
REGEX_PATTERNS_TO_REMOVE = [
    r'Monitors\s+v[\d.]+\s*\|\s*CCN\s+x\s+Zephyr\s+Monitors\s*\[\d{2}:\d{2}:\d{2}\]',  # Monitors v2.0.0 | CCN x Zephyr Monitors [HH:MM:SS]
    r'\s*\|\s*CCN\s+x\s+Zephyr\s+Monitors\s+\[[^\]]+\].*',  # | CCN x Zephyr Monitors [anything] and everything after
    r'Today\s+at\s+\d{1,2}:\d{2}\s*(?:AM|PM)',  # Today at 5:46 PM
]

def clean_text(text: str) -> str:
    """Remove unwanted phrases from text"""
    if not text:
        return text
    
    # Remove literal phrases
    for phrase in PHRASES_TO_REMOVE:
        # Case-insensitive removal
        text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)
    
    # Remove patterns with regex
    for pattern in REGEX_PATTERNS_TO_REMOVE:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def format_telegram_message(msg_data: Dict) -> Tuple[str, List[str], Optional[InlineKeyboardMarkup]]:
    """
    PROFESSIONAL formatter - converts Discord embed to rich Telegram message.
    
    Returns:
        (text, image_urls, keyboard)
    """
    raw = msg_data.get("raw_data", {})
    embed = raw.get("embed")
    author = raw.get("author", {})
    plain_content = msg_data.get("content", "")
    
    # Parse the tag line for extra info
    tag_info = parse_tag_line(plain_content) if plain_content else {}
    
    lines = []
    
    # === HEADER SECTION ===
    
    # Author name with bot badge
    author_name = clean_text(author.get("name", "Unknown"))
    if author.get("is_bot"):
        lines.append(f"🤖 <b>{author_name}</b>")
    else:
        lines.append(f"👤 <b>{author_name}</b>")
    
    lines.append("")
    
    # === EMBED CONTENT ===
    
    if embed:
        # RETAILER/SOURCE (from embed author or tag)
        retailer = None
        if embed.get("author"):
            retailer = clean_text(embed["author"].get("name"))
        elif tag_info.get("brand"):
            retailer = clean_text(tag_info["brand"])
        
        if retailer:
            lines.append(f"🏪 <b>{retailer}</b>")
            lines.append("")
        
        # PRODUCT TITLE (prioritize embed title over tag)
        title = clean_text(embed.get("title") or tag_info.get("product_code") or "Product Alert")
        
        # Add region if available
        if tag_info.get("region"):
            title = f"[{tag_info['region']}] {title}"
        
        lines.append(f"📦 <b>{title}</b>")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append("")
        
        # DESCRIPTION (truncated for readability)
        if embed.get("description"):
            desc = clean_text(embed["description"])[:400]
            if len(clean_text(embed["description"])) > 400:
                desc += "..."
            lines.append(desc)
            lines.append("")
        
        # FIELDS (Status, Price, Stock info) - EXCLUDE LINK FIELDS and DUPLICATES
        seen_values = set()  # Track what we've already shown
        if embed.get("fields"):
            for field in embed["fields"]:
                name = clean_text(field.get("name", ""))
                value = clean_text(field.get("value", ""))
                
                # Skip link-related fields - these go to buttons
                # Skip duplicates and empty values
                if name and value and not any(kw in name.lower() for kw in ['link', 'atc', 'qt']):
                    # Skip if we've already shown this exact value
                    if value in seen_values:
                        continue
                    seen_values.add(value)
                    
                    # Smart emoji mapping
                    if "status" in name.lower() or "stock" in name.lower():
                        icon = "✅"
                    elif "price" in name.lower() or "cost" in name.lower():
                        icon = "💰"
                    elif "resell" in name.lower():
                        icon = "📈"
                    elif "member" in name.lower():
                        icon = "👥"
                    elif "store" in name.lower() or "shop" in name.lower():
                        icon = "🏪"
                    elif "size" in name.lower():
                        icon = "📏"
                    elif "product" in name.lower():
                        icon = "📦"
                    else:
                        icon = "•"
                    
                    # Format value for better readability (bold for prices and stock)
                    if "price" in name.lower():
                        lines.append(f"{icon} <b>{name}:</b> <b>{value}</b>")
                    else:
                        lines.append(f"{icon} <b>{name}:</b> {value}")
        
        lines.append("")
        
        # FOOTER (timestamp) - REMOVE IF CONTAINS CCN/MONITOR INFO
        footer = embed.get("footer")
        if footer and "ccn" not in footer.lower() and "monitor" not in footer.lower():
            lines.append(f"⏰ {footer}")
        else:
            # Use scraped_at only if footer is empty/monitor-related
            scraped_time = parse_iso_datetime(msg_data.get("scraped_at", datetime.utcnow().isoformat()))
            lines.append(f"⏰ {scraped_time.strftime('%H:%M UTC')}")
    
    else:
        # FALLBACK: No embed, use plain content
        if plain_content:
            # Show parsed tag info nicely
            if tag_info.get("product_code"):
                lines.append(f"📦 <b>{clean_text(tag_info['product_code'])}</b>")
            if tag_info.get("brand"):
                lines.append(f"🏪 {clean_text(tag_info['brand'])}")
            if tag_info.get("action"):
                lines.append(f"ℹ️ {clean_text(tag_info['action'])}")
            
            lines.append("")
            lines.append(clean_text(plain_content)[:800])
            
            scraped_time = parse_iso_datetime(msg_data.get("scraped_at", datetime.utcnow().isoformat()))
            lines.append("")
            lines.append(f"⏰ {scraped_time.strftime('%H:%M:%S UTC')}")
    
    text = "\n".join(lines)
    
    # === IMAGE EXTRACTION ===
    images = []
    if embed:
        # Prioritize main images over thumbnail
        if embed.get("images"):
            images.extend(embed["images"][:3])  # Max 3 images
        elif embed.get("thumbnail"):
            images.append(embed["thumbnail"])
    
    # === BUTTON CREATION (CRITICAL FOR RESELLER LINKS) ===
    keyboard = []
    
    if embed and embed.get("links"):
        all_links = embed["links"]
        
        # Track URLs we've already added (deduplicate by URL)
        seen_urls = set()
        
        # Organize links by priority and field
        ebay_links = []
        fba_links = []
        atc_links = []
        buy_links = []
        other_links = []
        
        for link in all_links:
            text_lower = link.get('text', '').lower()
            url = link.get('url', '')
            link_text = link.get('text', 'Link')
            field = link.get('field', '').lower()
            
            # Skip empty URLs and invalid URLs
            if not url or not url.startswith('http'):
                continue
            
            # Skip if we've already added this exact URL
            if url in seen_urls:
                continue
            
            # Categorize by field first
            if 'atc' in field or 'qt' in field:
                atc_links.append({'text': link_text, 'url': url, 'field': field})
                seen_urls.add(url)
            elif 'link' in field:
                # These are the main links from the Links field
                if any(kw in text_lower for kw in ['sold', 'active', 'google', 'ebay']):
                    ebay_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
                elif any(kw in text_lower for kw in ['keepa', 'amazon', 'selleramp', 'camel']):
                    fba_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
                elif any(kw in text_lower for kw in ['buy', 'shop', 'purchase', 'checkout', 'cart']):
                    buy_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
                else:
                    other_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
            else:
                # Uncategorized links from other fields
                if any(kw in text_lower for kw in ['sold', 'active', 'google', 'ebay']):
                    ebay_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
                elif any(kw in text_lower for kw in ['keepa', 'amazon', 'selleramp', 'camel']):
                    fba_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
                elif any(kw in text_lower for kw in ['buy', 'shop', 'purchase', 'checkout', 'cart']):
                    buy_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
                else:
                    other_links.append({'text': link_text, 'url': url})
                    seen_urls.add(url)
        
        # Row 1: Price Checking (eBay links - Sold, Active, etc.)
        if ebay_links:
            row = []
            for link in ebay_links[:3]:
                emoji = '💰' if 'sold' in link['text'].lower() else '⚡'
                btn_text = f"{emoji} {link['text'][:15]}"
                row.append(InlineKeyboardButton(btn_text, url=link['url']))
            if row:
                keyboard.append(row)
        
        # Row 2: FBA/Analysis (Keepa, Amazon, etc.)
        if fba_links:
            row = []
            for link in fba_links[:3]:
                emoji = '📈' if 'keepa' in link['text'].lower() else '🔎'
                btn_text = f"{emoji} {link['text'][:15]}"
                row.append(InlineKeyboardButton(btn_text, url=link['url']))
            if row:
                keyboard.append(row)
        
        # Row 3: Direct Buy Links
        if buy_links:
            row = []
            for link in buy_links[:2]:
                btn_text = f"🛒 {link['text'][:18]}"
                row.append(InlineKeyboardButton(btn_text, url=link['url']))
            if row:
                keyboard.append(row)
        
        # Row 4: ATC (Add To Cart) Options
        if atc_links:
            row = []
            for link in atc_links[:5]:  # Show up to 5 ATC options
                # Extract quantity from text if possible
                qty_match = re.search(r'\d+', link['text'])
                qty = qty_match.group(0) if qty_match else link['text']
                btn_text = f"🛒 {qty}"
                row.append(InlineKeyboardButton(btn_text, url=link['url']))
                if len(row) == 3:  # 3 per row for ATC
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
        
        # Row 5: Other Links
        if other_links:
            row = []
            for link in other_links[:3]:
                btn_text = f"🔗 {link['text'][:15]}"
                row.append(InlineKeyboardButton(btn_text, url=link['url']))
            if row:
                keyboard.append(row)
    
    return text, images, InlineKeyboardMarkup(keyboard) if keyboard else None


def is_duplicate_source(msg_data: Dict) -> bool:
    """
    Check if message is from a duplicate source (like Profitable Pinger).
    These are filtered out to avoid duplicate alerts.
    """
    raw = msg_data.get("raw_data", {})
    embed = raw.get("embed", {})
    plain_content = msg_data.get("content", "")
    
    # Check author name
    author_name = (raw.get("author", {}).get("name") or "").lower()
    if "profitable pinger" in author_name:
        return True
    
    # Check embed author
    embed_author = (embed.get("author", {}) or {}).get("name") or ""
    if "profitable pinger" in embed_author.lower():
        return True
    
    # Check footer (bot signature)
    footer = (embed.get("footer") or "").lower()
    if "profitable pinger" in footer:
        return True
    
    # Check plain content
    if "profitable pinger" in plain_content.lower():
        return True
    
    return False


def create_main_menu() -> InlineKeyboardMarkup:
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 My Status", callback_data="status")],
        [InlineKeyboardButton("🔔 Toggle Alerts", callback_data="toggle_pause")],
        [InlineKeyboardButton("🎟️ Redeem Code", callback_data="redeem")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_menu_with_back(buttons: List[List[InlineKeyboardButton]], back_to: str = "main") -> InlineKeyboardMarkup:
    """Create menu with back button"""
    keyboard = buttons + [
        [InlineKeyboardButton("◀️ Back", callback_data=f"back:{back_to}")]
    ]
    return InlineKeyboardMarkup(keyboard)


# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with main menu"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    
    welcome_text = f"""
👋 <b>Welcome to Professional Discord Alerts!</b>

Hello {username}! Get instant product alerts with all the data you need.

<b>🎯 Features:</b>
• ⚡ Real-time notifications
• 🖼️ Product images
• 🔗 Direct action links (eBay, Keepa, Amazon, etc.)
• 📊 Full stock & price data
• ⏸️ Pause/Resume anytime

<b>📋 Status:</b>
"""
    
    if sm.is_active(user_id):
        stats = sm.get_user_stats(user_id)
        welcome_text += f"✅ <b>Active</b> - {stats['days_remaining']} days remaining\n"
        if stats['is_paused']:
            welcome_text += "⏸️ Alerts currently paused\n"
    else:
        welcome_text += "❌ <b>Not subscribed</b>\n\nRedeem a code to get started!\n"
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=create_main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses with back navigation"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    action = query.data
    
    # Handle back button
    if action.startswith("back:"):
        menu_to_go = action.split(":", 1)[1]
        if menu_to_go == "main":
            await query.edit_message_text("📋 <b>Main Menu</b>", parse_mode=ParseMode.HTML, reply_markup=create_main_menu())
        return
    
    if action == "status":
        if not sm.is_active(user_id):
            text = "❌ <b>Not Subscribed</b>\n\nUse /start to redeem a code!"
        else:
            stats = sm.get_user_stats(user_id)
            text = f"""
📊 <b>Your Subscription</b>

👤 User: {stats['username']}
⏰ Expires: {stats['expiry_date']}
⏳ Days Left: {stats['days_remaining']}
📅 Member Since: {stats['days_active']} days

🔔 Alerts: {'⏸️ PAUSED' if stats['is_paused'] else '✅ Active'}
"""
        
        buttons = [[InlineKeyboardButton("🔄 Refresh", callback_data="status")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=create_menu_with_back(buttons, "main"))
    
    elif action == "toggle_pause":
        if not sm.is_active(user_id):
            buttons = []
            await query.edit_message_text("❌ You need an active subscription!", parse_mode=ParseMode.HTML, reply_markup=create_menu_with_back(buttons, "main"))
            return
        
        new_state = sm.toggle_pause(user_id)
        status = "⏸️ PAUSED" if new_state else "✅ RESUMED"
        
        text = f"""
{status} <b>Alerts {status}</b>

Your alerts have been {'paused' if new_state else 'resumed'}.
Toggle anytime from the menu.
"""
        buttons = [[InlineKeyboardButton("📊 Status", callback_data="status")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=create_menu_with_back(buttons, "main"))
    
    elif action == "redeem":
        text = """
🎟️ <b>Redeem Subscription Code</b>

Send your code in this format:
<code>XXXXXXXX</code>

Example: <code>ABC123DEF456</code>

Get a code from your administrator!
"""
        buttons = []
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=create_menu_with_back(buttons, "main"))
    
    elif action == "help":
        text = """
❓ <b>Help & Information</b>

<b>How It Works:</b>
1️⃣ Redeem a subscription code
2️⃣ Receive real-time alerts with images & links
3️⃣ Click buttons to check eBay, Keepa, Amazon instantly

<b>Commands:</b>
• /start - Main menu & status

<b>Tips:</b>
• Enable Telegram notifications
• Keep alerts active for drops
• Use pause when needed

<b>Need Support?</b>
Contact your administrator!
"""
        buttons = []
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=create_menu_with_back(buttons, "main"))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle code redemption"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name
    text = update.message.text.strip().upper()
    
    code = text.replace("-", "").replace(" ", "")
    
    if len(code) >= 8 and len(code) <= 16:
        if sm.redeem_code(user_id, username, code):
            stats = sm.get_user_stats(user_id)
            response = f"""
🎉 <b>Code Redeemed Successfully!</b>

✅ Subscription Active
⏰ Expires: {stats['expiry_date']}
⏳ Days: {stats['days_remaining']}

You'll now receive professional alerts!
Use /start for the menu.
"""
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(
                "❌ <b>Invalid Code</b>\n\nCheck your code and try again.",
                parse_mode=ParseMode.HTML
            )
    else:
        await update.message.reply_text(
            "💡 Send a subscription code or use /start for the menu.",
            parse_mode=ParseMode.HTML
        )


async def gen_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Generate codes"""
    if str(update.effective_user.id) != str(ADMIN_USER_ID): 
        return
    
    try:
        days = int(context.args[0])
        code = sm.generate_code(days)
        await update.message.reply_text(
            f"🔑 <b>New Code Generated</b>\n\nCode: <code>{code}</code>\nDuration: {days} days",
            parse_mode=ParseMode.HTML
        )
    except:
        await update.message.reply_text("Usage: /gen <days>")


async def broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    """Poll for new messages and broadcast with PROFESSIONAL formatting"""
    try:
        new_msgs = poller.poll_new_messages()
        
        if not new_msgs:
            logger.debug("📭 Poll: No new messages found")
            return
        
        # Filter out duplicate sources (Profitable Pinger, etc.)
        filtered_msgs = [msg for msg in new_msgs if not is_duplicate_source(msg)]
        
        if len(filtered_msgs) < len(new_msgs):
            skipped_count = len(new_msgs) - len(filtered_msgs)
            logger.info(f"📬 Poll: Found {len(new_msgs)} message(s), skipped {skipped_count} duplicate source(s)")
        else:
            logger.info(f"📬 Poll: Found {len(new_msgs)} new message(s)")
        
        if not filtered_msgs:
            logger.debug("📭 No messages after filtering duplicates")
            return
        
        active_users = sm.get_active_users()
        all_users = sm.users
        
        if not active_users:
            logger.warning(f"⚠️  BROADCAST BLOCKED: No active users!")
            logger.warning(f"   Total users: {len(all_users)}")
            logger.warning(f"   New messages waiting: {len(filtered_msgs)}")
            
            # Show why users are inactive
            for uid, user_data in all_users.items():
                paused = user_data.get("alerts_paused", False)
                expiry = user_data.get("expiry", "unknown")
                if paused:
                    logger.warning(f"   • {uid}: PAUSED (expires {expiry})")
                else:
                    try:
                        exp_dt = parse_iso_datetime(expiry)
                        now = datetime.utcnow()
                        if exp_dt <= now:
                            logger.warning(f"   • {uid}: EXPIRED ({expiry})")
                    except:
                        logger.warning(f"   • {uid}: unknown status")
            return
        
        logger.info(f"📤 BROADCAST: {len(filtered_msgs)} message(s) → {len(active_users)} active user(s)")
        
        for msg_idx, msg in enumerate(filtered_msgs):
            try:
                logger.debug(f"   📝 Formatting message {msg_idx + 1}/{len(filtered_msgs)}...")
                text, images, keyboard = format_telegram_message(msg)
                logger.debug(f"   ✓ Message formatted successfully (text={len(text)} chars, images={len(images) if images else 0}, buttons={len(keyboard.inline_keyboard) if keyboard else 0})")
                
            except Exception as e:
                logger.error(f"   ❌ Failed to format message {msg_idx + 1}: {type(e).__name__}: {e}")
                logger.debug(f"   Message data: {json.dumps(msg, indent=2, default=str)[:500]}")
                logger.error(f"   Full traceback: {traceback.format_exc()}")
                continue  # Skip this message and move to next
            
            for uid in active_users:
                try:
                    # PROFESSIONAL DELIVERY: Image + Caption + Buttons
                    if images:
                        try:
                            logger.debug(f"   📸 Sending photo alert to {uid}...")
                            # Send first image with formatted caption and buttons
                            await context.bot.send_photo(
                                chat_id=uid,
                                photo=images[0],
                                caption=text[:1024],  # Telegram limit
                                parse_mode=ParseMode.HTML,
                                reply_markup=keyboard
                            )
                            
                            # Send additional images if multiple
                            if len(images) > 1:
                                media_group = [InputMediaPhoto(img) for img in images[1:3]]
                                await context.bot.send_media_group(chat_id=uid, media=media_group)
                            logger.debug(f"   ✅ Photo alert sent to {uid}")
                        except Exception as photo_error:
                            logger.error(f"   ❌ Photo send failed for {uid}: {type(photo_error).__name__}: {photo_error}")
                            # Fallback to text-only
                            try:
                                logger.debug(f"   📝 Falling back to text-only for {uid}...")
                                await context.bot.send_message(
                                    chat_id=uid,
                                    text=text,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=keyboard,
                                    disable_web_page_preview=False
                                )
                                logger.debug(f"   ✅ Text-only alert sent to {uid}")
                            except Exception as fallback_error:
                                raise fallback_error
                    else:
                        logger.debug(f"   📝 Sending text alert to {uid}...")
                        # Text-only with buttons
                        await context.bot.send_message(
                            chat_id=uid,
                            text=text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=keyboard,
                            disable_web_page_preview=False
                        )
                        logger.debug(f"   ✅ Text alert sent to {uid}")
                
                except Exception as e:
                    error_str = str(e)
                    if "user not found" in error_str.lower() or "chat_id_invalid" in error_str.lower():
                        logger.warning(f"   ⛔ {uid}: User invalid/blocked - deactivating subscription")
                        # Optionally deactivate the user here
                    elif "bot was blocked" in error_str.lower():
                        logger.warning(f"   🚫 {uid}: Bot was blocked by user")
                    elif "bad request" in error_str.lower():
                        logger.error(f"   ⚠️  {uid}: Bad request (likely formatting issue): {error_str[:100]}")
                    else:
                        logger.error(f"   ❌ {uid}: {type(e).__name__}: {error_str[:200]}")
                
                # Rate limit protection
                await asyncio.sleep(0.05)

        
    except Exception as e:
        logger.error(f"❌ Broadcast job critical error: {type(e).__name__}: {e}")
        logger.error(f"   Full traceback: {traceback.format_exc()}")


def run_bot():
    """Run bot with professional alert system"""
    try:
        if not TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN not set!")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("🚀 TELEGRAM BOT INITIALIZATION")
        logger.info("=" * 80)
        logger.info(f"   Token: {TELEGRAM_TOKEN[:15]}...***{TELEGRAM_TOKEN[-5:]}")
        logger.info(f"   Admin ID: {ADMIN_USER_ID}")
        logger.info(f"   Poll Interval: {POLL_INTERVAL} seconds")
        logger.info(f"   Users file: {USERS_FILE}")
        logger.info(f"   Codes file: {CODES_FILE}")
        
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("gen", gen_code))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        if app.job_queue:
            logger.info("   Adding broadcast job...")
            app.job_queue.run_repeating(broadcast_job, interval=POLL_INTERVAL, first=5)
            logger.info(f"   ✅ Job queue running (poll every {POLL_INTERVAL}s)")
        
        # Show active users count on startup
        active_count = len(sm.get_active_users())
        total_count = len(sm.users)
        logger.info(f"   📊 Users: {total_count} total, {active_count} active")
        logger.info("=" * 80 + "\n")
        
        logger.info("📡 Starting polling loop...")
        app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=[])
        
    except KeyboardInterrupt:
        logger.info("⚠️  Bot interrupted by user")
    except Exception as e:
        logger.error(f"❌ CRITICAL BOT ERROR: {e}")
        logger.error(traceback.format_exc())