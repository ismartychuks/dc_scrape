#!/usr/bin/env python3
"""
link_parser.py
Extracts markdown-style links from Discord embed text
Handles formats like: [Active](https://url.com) | [Keepa](https://keepa.com)
"""

import re
from typing import List, Dict, Optional


def extract_markdown_links(text: str) -> List[Dict[str, str]]:
    """
    Extract markdown links from text.
    
    Discord format: [Link Text](https://url.com)
    
    Args:
        text: Raw text containing markdown links
        
    Returns:
        List of dicts with 'text' and 'url' keys
    """
    if not text:
        return []
    
    # Regex pattern for markdown links: [text](url)
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


def categorize_links(links: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Categorize links into groups (eBay, FBA, Buy, etc.)
    
    Args:
        links: List of link dicts with 'text' and 'url'
        
    Returns:
        Dict with categories as keys
    """
    categories = {
        'ebay': [],
        'fba': [],
        'buy': [],
        'other': []
    }
    
    ebay_keywords = ['sold', 'active', 'google', 'ebay']
    fba_keywords = ['keepa', 'amazon', 'selleramp', 'fba', 'camel']
    buy_keywords = ['buy', 'shop', 'purchase', 'checkout', 'cart']
    
    for link in links:
        text_lower = link['text'].lower()
        url_lower = link['url'].lower()
        
        # Check eBay links
        if any(kw in text_lower or kw in url_lower for kw in ebay_keywords):
            categories['ebay'].append(link)
        # Check FBA/Analysis links
        elif any(kw in text_lower or kw in url_lower for kw in fba_keywords):
            categories['fba'].append(link)
        # Check direct buy links
        elif any(kw in text_lower or kw in url_lower for kw in buy_keywords):
            categories['buy'].append(link)
        else:
            categories['other'].append(link)
    
    return categories


def extract_links_from_embed(embed_data: Dict) -> List[Dict[str, str]]:
    """
    Extract ALL links from a Discord embed structure.
    Searches description, fields, and existing links array.
    
    Args:
        embed_data: The embed dict from extract_embed_data()
        
    Returns:
        List of unique links with text and url
    """
    if not embed_data:
        return []
    
    all_links = []
    seen_urls = set()
    
    # 1. Get links from the links array (already extracted by scraper)
    for link in embed_data.get('links', []):
        url = link.get('url', '')
        if url and url not in seen_urls:
            all_links.append(link)
            seen_urls.add(url)
    
    # 2. Parse description for markdown links
    description = embed_data.get('description', '')
    if description:
        md_links = extract_markdown_links(description)
        for link in md_links:
            if link['url'] not in seen_urls:
                all_links.append(link)
                seen_urls.add(link['url'])
    
    # 3. Parse all field values for markdown links
    for field in embed_data.get('fields', []):
        field_value = field.get('value', '')
        if field_value:
            md_links = extract_markdown_links(field_value)
            for link in md_links:
                if link['url'] not in seen_urls:
                    all_links.append(link)
                    seen_urls.add(link['url'])
    
    return all_links


def parse_tag_line(tag: str) -> Dict[str, Optional[str]]:
    """
    Parse the Discord tag line above embeds.
    
    Example: "@Product Flips | [UK] CRW-001-1ER | Casio | Just restocked for £0.00"
    
    Returns:
        Dict with: ping, region, product_code, brand, action, price
    """
    if not tag:
        return {}
    
    parts = [p.strip() for p in tag.split('|')]
    
    result = {
        'ping': None,
        'region': None,
        'product_code': None,
        'brand': None,
        'action': None,
        'price': None,
        'raw': tag
    }
    
    for part in parts:
        # Check for ping (@mention)
        if part.startswith('@'):
            result['ping'] = part
        
        # Check for region code [XX]
        elif part.startswith('[') and part.endswith(']'):
            result['region'] = part.strip('[]')
        
        # Check for action phrase
        elif 'restocked' in part.lower() or 'in stock' in part.lower() or 'available' in part.lower():
            result['action'] = part
            
            # Try to extract price from action
            price_match = re.search(r'[£$€]\s*[\d,]+\.?\d*', part)
            if price_match:
                result['price'] = price_match.group(0)
        
        # Otherwise could be brand or product code
        else:
            if result['product_code'] is None:
                result['product_code'] = part
            elif result['brand'] is None:
                result['brand'] = part
    
    return result


def clean_link_text(text: str, max_length: int = 20) -> str:
    """
    Clean and truncate link text for button display.
    
    Args:
        text: Original link text
        max_length: Maximum length for button text
        
    Returns:
        Cleaned, truncated text
    """
    # Remove common prefixes
    text = text.replace('Click Here!', '').strip()
    text = text.replace('View', '').strip()
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length-3] + '...'
    
    return text or 'Link'


# Emoji mapping for link types
LINK_EMOJIS = {
    'sold': '💰',
    'active': '⚡',
    'google': '🔍',
    'ebay': '🛒',
    'keepa': '📈',
    'amazon': '🔎',
    'selleramp': '💎',
    'camel': '🐫',
    'buy': '🛒',
    'shop': '🏪',
    'cart': '🛒',
    'checkout': '✅',
}


def add_emoji_to_link_text(text: str) -> str:
    """
    Add appropriate emoji prefix to link text.
    
    Args:
        text: Link text (e.g., "Active", "Keepa")
        
    Returns:
        Text with emoji prefix (e.g., "⚡ Active")
    """
    text_lower = text.lower()
    
    for keyword, emoji in LINK_EMOJIS.items():
        if keyword in text_lower:
            return f"{emoji} {text}"
    
    # Default to link emoji
    return f"🔗 {text}"


if __name__ == "__main__":
    # Test cases
    print("=== Testing Markdown Link Extraction ===\n")
    
    test_text = """
    eBay Links: [Sold](https://ebay.com/sold) | [Active](https://ebay.com/active) | [Google](https://google.com)
    FBA Links: [Keepa](https://keepa.com) | [Amazon Search](https://amazon.com) | [SellerAmp](https://selleramp.com)
    """
    
    links = extract_markdown_links(test_text)
    print(f"Extracted {len(links)} links:")
    for link in links:
        print(f"  - {link['text']}: {link['url']}")
    
    print("\n=== Testing Link Categorization ===\n")
    categories = categorize_links(links)
    for cat, cat_links in categories.items():
        if cat_links:
            print(f"{cat.upper()}: {len(cat_links)} links")
            for link in cat_links:
                print(f"  - {link['text']}")
    
    print("\n=== Testing Tag Line Parsing ===\n")
    test_tag = "@Product Flips | [UK] CRW-001-1ER | Casio | Just restocked for £0.00"
    parsed = parse_tag_line(test_tag)
    print(f"Tag: {test_tag}")
    print(f"Parsed: {parsed}")