#!/usr/bin/env python3
"""
Simple viewer to display saved Discord message HTML in a formatted way.
"""

import os
from pathlib import Path
from html.parser import HTMLParser

class HTMLExtractor(HTMLParser):
    """Extract meaningful text from HTML"""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_link = False
        self.current_link = None
        self.links = []
        self.classes = []
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'a':
            self.in_link = True
            self.current_link = attrs_dict.get('href', '')
        if 'class' in attrs_dict:
            self.classes.append(attrs_dict['class'])
    
    def handle_endtag(self, tag):
        if tag == 'a':
            self.in_link = False
            if self.current_link:
                self.current_link = None
    
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text_parts.append(text)
            if self.in_link and self.current_link:
                self.links.append({'text': text, 'url': self.current_link})

def view_inspection_file(filepath):
    """Display contents of an inspection file"""
    
    print(f"\n{'='*80}")
    print(f"📄 File: {os.path.basename(filepath)}")
    print(f"{'='*80}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Extract key info
    parser = HTMLExtractor()
    parser.feed(html)
    
    # Show extracted links
    if parser.links:
        print("🔗 LINKS FOUND:")
        for i, link in enumerate(parser.links, 1):
            print(f"   {i}. [{link['text']}]({link['url']})")
    
    # Show text content
    if parser.text_parts:
        print("\n📝 TEXT CONTENT:")
        # Group by logical sections
        current_section = []
        for text in parser.text_parts:
            if len(current_section) > 0 and len('\n'.join(current_section)) > 150:
                print(f"   {' '.join(current_section)}")
                current_section = []
            current_section.append(text)
        if current_section:
            print(f"   {' '.join(current_section)}")
    
    # Show unique classes
    unique_classes = set()
    for class_str in parser.classes:
        unique_classes.update(class_str.split())
    
    if unique_classes:
        print(f"\n🎯 CSS CLASSES ({len(unique_classes)}):")
        for cls in sorted(list(unique_classes))[:15]:
            print(f"   .{cls}")
    
    print(f"\n{'='*80}\n")

def main():
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("❌ data/ folder not found")
        print("Run: set DEBUG=True && python app.py")
        return
    
    files = list(data_dir.glob("message_inspection_*.html"))
    
    if not files:
        print("❌ No inspection files found")
        print("Run: set DEBUG=True && python app.py")
        return
    
    print(f"\n✅ Found {len(files)} inspection file(s)\n")
    print("Viewing all inspection files...\n")
    
    for filepath in sorted(files):
        view_inspection_file(filepath)

if __name__ == "__main__":
    main()
