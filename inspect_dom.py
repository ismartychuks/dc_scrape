#!/usr/bin/env python3
"""
Inspect Discord message HTML structure to find embeds
"""

import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNELS = os.getenv("CHANNELS", "").split(",")

async def inspect_discord():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible so we can see
        context = await browser.new_context(storage_state="data/storage_state.json") if os.path.exists("data/storage_state.json") else await browser.new_context()
        page = await context.new_page()
        
        if CHANNELS:
            channel_url = CHANNELS[0].strip()
            print(f"🔍 Opening: {channel_url}")
            await page.goto(channel_url)
            await page.wait_for_timeout(3000)
            
            # Get all message elements
            messages = await page.locator('div[id^="message-"]').all()
            print(f"Found {len(messages)} messages\n")
            
            if messages:
                msg = messages[0]
                print("=" * 60)
                print("FIRST MESSAGE STRUCTURE")
                print("=" * 60)
                
                # Get HTML
                html = await msg.inner_html()
                print(f"Message HTML length: {len(html)} chars")
                print(f"\nFirst 1000 chars:\n{html[:1000]}\n")
                
                # Find divs
                divs = await msg.locator('div').all()
                print(f"\nTotal <div> elements in message: {len(divs)}")
                
                # Check for specific patterns
                embeds = await msg.locator('div[class*="embed"]').all()
                print(f"Divs with 'embed' in class: {len(embeds)}")
                
                links = await msg.locator('a[href]').all()
                print(f"Links found: {len(links)}")
                for link in links[:5]:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    print(f"   • {text[:30]} → {href[:50]}")
                
                # Look at all divs with class names
                print(f"\nDiv classes in message:")
                for i, div in enumerate(divs[:15]):  # First 15 divs
                    cls = await div.get_attribute('class')
                    style = await div.get_attribute('style')
                    text = await div.inner_text()
                    print(f"   [{i}] class='{cls}'")
                    if style and len(style) < 50:
                        print(f"       style='{style}'")
                    if text and len(text) < 80:
                        print(f"       text='{text}'")
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_discord())
