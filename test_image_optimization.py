
import re
import urllib.parse

def optimize_image_url(url: str) -> str:
    if not url: return url
    
    # 1. Decode Discord Proxy URLs
    if "images-ext-1.discordapp.net" in url or "images-ext-2.discordapp.net" in url:
        match = re.search(r'/external/[^/]+/(https?)/(.*)', url)
        if match:
            protocol = match.group(1)
            rest = match.group(2)
            url = f"{protocol}://{rest}"
            print(f"Decoded Discord Proxy: {url}")
            
    # 2. Amazon Image Optimization
    if "media-amazon.com" in url or "ssl-images-amazon.com" in url:
        new_url = re.sub(r'\._[A-Z_]+[0-9]+_\.', '.', url)
        if "?" in new_url:
            new_url = new_url.split("?")[0]
        print(f"Optimized Amazon: {new_url}")
        return new_url

    # 3. eBay Image Optimization
    # Pattern: s-l300.jpg -> s-l1600.jpg
    if "ebayimg.com" in url:
        if re.search(r's-l\d+\.', url):
            new_url = re.sub(r's-l\d+\.', 's-l1600.', url)
            print(f"Optimized eBay: {new_url}")
            return new_url
        
    return url

# Test Cases
tests = [
    "https://images-ext-1.discordapp.net/external/qUoo6m-VPmSseo3A3czy64HQsj-ftLppTvsW4GIcqCg/https/m.media-amazon.com/images/I/511nSF7YpmL._SL160_.jpg?format=webp",
    "https://i.ebayimg.com/images/g/AbC/s-l300.jpg",
    "https://i.ebayimg.com/images/g/AbC/s-l500.png",  # Should handle other extensions? usually jpg but regex handles dot
    "https://images-ext-2.discordapp.net/external/xyz/https/i.ebayimg.com/images/g/xyz/s-l64.jpg" 
]

for t in tests:
    print(f"\nOriginal: {t}")
    print(f"Final:    {optimize_image_url(t)}")
