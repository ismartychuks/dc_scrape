# Discord Data Extraction Debugging Guide

## Quick Start: Enable HTML Inspection

To see exactly how Discord structures its embeds and what data is available:

### Step 1: Enable Debug Mode
```powershell
# On Windows PowerShell:
$env:DEBUG = "True"
python app.py
```

Or add to your `.env` file:
```
DEBUG=True
```

### Step 2: Run the Scraper
```powershell
python app.py
```

The scraper will save the first message from each channel as HTML files.

### Step 3: Inspect the HTML Files
Open the generated files in the `data/` folder:
- `data/message_inspection_<message_id>.html`

View them in:
- Your browser (right-click → Open with → Browser)
- A text editor (Notepad, VS Code)
- Or use the analysis script:

```powershell
python analyze_html.py
```

## What to Look For in the HTML

Based on your Discord screenshots, the embeds contain:

### 1. **Product Links** 🔗
Look for `<a href="...">` tags containing:
- Amazon product links
- eBay auction/listing links  
- StockX links
- Other retailer links

### 2. **Prices** 💰
Look for text containing currency symbols:
- £29.99
- £5.45
- etc.

### 3. **Product Details**
Look for text/fields containing:
- Product name/title
- Type (Restock, New Product, etc.)
- Stock status (in stock, 1+, etc.)
- Product ID/SKU

### 4. **Images** 🖼️
Look for `<img src="...">` tags

## Sharing the HTML with Me

Once you have the HTML files:

1. **Option A: Use the analysis script** (easiest)
   ```powershell
   python analyze_html.py
   ```
   This will extract key information and show it nicely formatted.

2. **Option B: Open in VS Code**
   The HTML files are small and you can share them directly.

3. **Option C: Send via Discord/Chat**
   Copy the content of a message_inspection file and paste it.

## Expected Output

Once I see the HTML structure, I can:
✅ Identify correct CSS selectors for extracting data
✅ Update `extract_embed_data()` function with proper selectors
✅ Add price extraction with correct patterns
✅ Extract all product links properly
✅ Get product IDs and stock info

## Disable Debug Mode

Once we've fixed the extraction:
```powershell
$env:DEBUG = "False"
python app.py
```

Or remove `DEBUG=True` from `.env`

---

**Ready to debug?** Run these commands:
```powershell
set DEBUG=True
python app.py
```

Then share the HTML files from the `data/` folder with me!
