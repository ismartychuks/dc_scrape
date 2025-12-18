#!/usr/bin/env python3
"""
Quick guide to inspect Discord message HTML structure for debugging.
This helps understand how Discord embeds are built.
"""

import os

print("""
╔════════════════════════════════════════════════════════════════╗
║         DISCORD MESSAGE INSPECTION & DEBUGGING GUIDE           ║
╚════════════════════════════════════════════════════════════════╝

METHOD 1: AUTOMATIC HTML INSPECTION (Recommended)
─────────────────────────────────────────────────

1. Enable DEBUG mode by setting environment variable:
   - Windows: set DEBUG=True
   - Linux: export DEBUG=True
   
2. Start the scraper:
   python app.py
   
3. Wait for first message to be scraped
   
4. Look in the 'data/' folder for files like:
   data/message_inspection_<message_id>.html
   
5. Open these HTML files in a browser or text editor to see:
   - Exact structure of Discord embeds
   - All links (href attributes)
   - Product details (prices, stock, etc.)
   - Form fields and their contents


METHOD 2: MANUAL INSPECTION (Advanced)
───────────────────────────────────────

While the scraper is running:

1. Keep the browser window visible (don't use headless mode):
   set HEADLESS=False
   
2. Open Chrome DevTools while scraper is running:
   Press F12 or Ctrl+Shift+I
   
3. In DevTools Inspector tab:
   - Inspect a Discord message element
   - Look for divs with classes containing "embed"
   - Check for <a href> tags (links)
   - Look for span/div elements containing prices
   - Find product IDs, stock info, etc.

4. Take screenshots or copy the HTML structure


METHOD 3: BROWSER EXTENSION (For manual inspection)
────────────────────────────────────────────────────

1. Open Chrome DevTools (F12)
2. Right-click on a Discord message → "Inspect Element"
3. Look at the HTML tree for:
   - Message structure
   - Embed containers
   - Link elements (<a>)
   - Price indicators (£, $, €)
   - Button/link elements


WHAT TO LOOK FOR IN THE HTML:
──────────────────────────────

Looking at your screenshot, Discord shows:
✓ Product title
✓ Price (£29.99, £5.45, etc.)
✓ Product type (Restock, New Product)
✓ Links to retailers (Amazon, eBay, StockX, etc.)
✓ Stock status
✓ Images/thumbnails

Find the CSS selectors or class names for these elements.


NEXT STEPS:
──────────

1. Enable DEBUG mode and run the scraper
2. Open the generated HTML files in 'data/' folder
3. Share the HTML content with me so I can update the extraction logic
4. I'll add the correct selectors to extract prices, links, and product details


QUICK START:
────────────
""")

# Check if debug files exist
data_dir = "data"
if os.path.exists(data_dir):
    files = [f for f in os.listdir(data_dir) if f.startswith("message_inspection")]
    if files:
        print(f"\n✅ Found {len(files)} inspection file(s):")
        for f in files[:5]:
            print(f"   • {f}")
    else:
        print(f"\n❌ No inspection files found yet.")
        print(f"   Run: set DEBUG=True && python app.py")
else:
    print(f"\n❌ data/ folder not found. Creating it...")
    os.makedirs(data_dir, exist_ok=True)
    print(f"   ✅ Run: set DEBUG=True && python app.py")

print("\n" + "="*60)
