#!/usr/bin/env python3
"""
Analyze saved Discord message HTML to identify CSS selectors for data extraction.
"""

import os
import re
from pathlib import Path

def analyze_html_file(filepath):
    """Analyze an HTML file to find potential selectors"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"\n{'='*70}")
    print(f"ANALYZING: {os.path.basename(filepath)}")
    print(f"{'='*70}")
    print(f"File size: {len(html)} bytes")
    
    # Find all unique class names
    classes = set(re.findall(r'class="([^"]*)"', html))
    print(f"\n📋 Unique classes found: {len(classes)}")
    for cls in sorted(classes)[:20]:
        if cls and 'h' not in cls[:1]:
            print(f"   .{cls}")
    
    # Look for links
    links = re.findall(r'href="([^"]*)"', html)
    print(f"\n🔗 Links found: {len(set(links))}")
    for link in sorted(set(links))[:10]:
        if link.startswith('http'):
            print(f"   {link[:60]}...")
    
    # Look for prices
    prices = re.findall(r'[£$€]\s*[\d,]+\.?\d*', html)
    print(f"\n💰 Prices found: {len(prices)}")
    for price in set(prices):
        print(f"   {price}")
    
    # Look for common keywords
    keywords = ['price', 'stock', 'product', 'link', 'embed', 'image', 'url', 'button']
    print(f"\n🔍 Keyword occurrences:")
    for kw in keywords:
        count = len(re.findall(kw, html, re.IGNORECASE))
        if count > 0:
            print(f"   '{kw}': {count} times")
    
    # Look for img tags
    imgs = re.findall(r'<img[^>]*src="([^"]*)"', html)
    print(f"\n🖼️ Images found: {len(imgs)}")
    for img in imgs[:5]:
        print(f"   {img[:70]}...")
    
    # Look for div/span with data attributes
    data_attrs = re.findall(r'(data-[^=]*="[^"]*")', html)
    if data_attrs:
        print(f"\n📊 Data attributes found: {len(set(data_attrs))}")
        for attr in list(set(data_attrs))[:5]:
            print(f"   {attr}")
    
    print("\n" + "="*70)
    print("💡 TIP: Look for patterns in these selectors to extract:")
    print("   - Prices (numbers with £/$//€)")
    print("   - Links (href attributes)")
    print("   - Product IDs (numbers)")
    print("   - Stock status (keywords like 'stock', 'available')")
    print("="*70 + "\n")

def main():
    """Analyze all inspection files in data/ folder"""
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("❌ data/ folder not found")
        print("Run: set DEBUG=True && python app.py")
        return
    
    files = list(data_dir.glob("message_inspection_*.html"))
    
    if not files:
        print("❌ No inspection files found in data/")
        print()
        print("This means:")
        print("  1. DEBUG mode was not enabled when running scraper")
        print("  2. Scraper hasn't run yet")
        print()
        print("FIX: Run these commands:")
        print()
        print("  PowerShell:")
        print("    $env:DEBUG = 'True'")
        print("    python app.py")
        print()
        print("  OR Command Prompt:")
        print("    set DEBUG=True")
        print("    python app.py")
        print()
        print("  OR just double-click:")
        print("    run_debug.bat")
        print()
        print("Wait 1-2 minutes for scraper to scan channels, then run:")
        print("  python analyze_html.py")
        print()
        
        # Check if DEBUG is set
        import os
        debug_val = os.getenv("DEBUG", "(not set)")
        if debug_val == "(not set)":
            print("⚠️  Current DEBUG value: (not set)")
        else:
            print(f"Current DEBUG value: {debug_val}")
        return
    
    print(f"\n✅ Found {len(files)} inspection file(s)\n")
    
    for filepath in files[:3]:  # Analyze first 3
        analyze_html_file(filepath)

if __name__ == "__main__":
    main()
