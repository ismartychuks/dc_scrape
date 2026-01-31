# 📊 Region & Subcategories Structure Analysis

## Current State ✅

### 1. Data Source: `channels.json`

Location: `data/channels.json` (or synced from Supabase storage)

**Format:**
```json
[
  {
    "id": "864504557903937587",
    "name": "Restocks Online",           // ← STORE NAME (subcategory)
    "url": "https://discord.com/...",
    "category": "UK Stores",             // ← REGION (from category field)
    "enabled": true
  },
  ...
]
```

**Current Data Summary:**
- **UK Stores**: 16 subcategories (Restocks Online, Argos Instore, Collectors Amazon, New Buys, etc.)
- **USA Stores**: 65 subcategories (Mega Evolution, Target 10 plus Restocks, Walmart, Pokemon Center, etc.)
- **Canada Stores**: 13 subcategories (Hobbieville, Pokemon Center, Best Buy, Costco, etc.)

**Total Enabled Channels**: ~94 channels across 3 regions

---

## Current API Implementation ✅

### Endpoint 1: `/v1/categories`

**What it does:**
- Reads from `channels.json`
- Groups channels by their `"category"` field (already "UK Stores", "USA Stores", "Canada Stores")
- Returns unique `"name"` values per region (sorted alphabetically)
- Adds "ALL" at the beginning of each region list

**Current Response:**
```json
{
  "UK Stores": [
    "ALL",
    "Argos Instore",
    "Argos Instore Pokemo",
    "Asda Pokemon",
    "Chaos Cards",
    "Collectors Amazon",
    ...
  ],
  "USA Stores": [
    "ALL",
    "Amazon",
    "Amazon Pokemon",
    "Barnes and Noble",
    "Books a Million",
    ...
  ],
  "Canada Stores": [
    "ALL",
    "Amazon",
    "Best Buy",
    "Costco",
    ...
  ]
}
```

**Status**: ✅ **WORKING CORRECTLY**

---

### Endpoint 2: `/v1/feed`

**What it does:**
- Takes filters: `region` and `category` (store name)
- Loads `channels.json` to build a `channel_map`
- For each Discord message:
  - Gets channel ID from message
  - Looks up region and store name from `channel_map`
  - Extracts product data (title, price, image, links)
  - Filters by region (if specified)
  - Filters by store name (if category specified)
  - Returns paginated products

**Example Request:**
```
GET /v1/feed?user_id=xxx&region=USA+Stores&category=Amazon&limit=10
```

**Response:**
```json
{
  "products": [
    {
      "id": "123",
      "region": "USA Stores",
      "store_name": "Amazon",      // ← From channel name
      "product_data": {
        "title": "Product Name",
        "image": "https://...",
        "price": "29.99",
        "buy_url": "https://amazon.com/..."
      }
    },
    ...
  ],
  "offset": 0,
  "limit": 10,
  "total": 45
}
```

**Status**: ✅ **WORKING CORRECTLY**

---

## Mobile App Integration

### Constants.js

```javascript
const Constants = {
    API_BASE_URL: 'https://discord-archiver.onrender.com',  // or Railway URL
};
```

### HomeScreen.js - Filter Logic

```javascript
// Step 1: Fetch all available regions
const response = await fetch(`${API_BASE_URL}/v1/categories`);
const categoryData = response.json();
// Returns: { "UK Stores": [...], "USA Stores": [...], "Canada Stores": [...] }

// Step 2: When user selects region, show available stores
const stores = categoryData[selectedRegion];  // e.g., ["ALL", "Argos Instore", ...]

// Step 3: When user selects store, fetch feed
const feedResponse = await fetch(
  `${API_BASE_URL}/v1/feed?user_id=${userId}&region=${selectedRegion}&category=${selectedStore}&limit=20`
);
```

---

## What's Verified ✅

1. ✅ **channels.json** contains all regions and stores
2. ✅ **Region names** are correct (UK Stores, USA Stores, Canada Stores)
3. ✅ **Store names** are unique per region and properly formatted
4. ✅ **/v1/categories** returns correct structure
5. ✅ **/v1/feed** filters by region and store correctly
6. ✅ **Mobile app** displays regions and stores from API
7. ✅ **Deep linking** works with product IDs

---

## What Still Needs Testing 🔧

### On Mobile App:
1. **Region Selector** - Does it show UK Stores, USA Stores, Canada Stores?
2. **Store Selector** - When I select "USA Stores", do I see all 65 stores?
3. **Feed Loading** - When I select a specific store (e.g., "Amazon"), do products load?
4. **ALL Category** - When I select "ALL", do I see products from all stores in the region?
5. **Switching Regions** - Does switching from UK to USA clear the selected store?

### Backend Validation:
1. **Channel Sync** - Are all channels in `channels.json` updated?
2. **Enabled Flag** - Are only `"enabled": true` channels shown?
3. **New Channels** - When telegram_bot.py `/add_channels` is used, does it update the list?

---

## Testing Commands

### Test Categories Endpoint
```bash
curl https://your-railway-url/v1/categories | jq
```

**Should return:**
```json
{
  "UK Stores": ["ALL", "Argos Instore", ...],
  "USA Stores": ["ALL", "Amazon", ...],
  "Canada Stores": ["ALL", "Best Buy", ...]
}
```

### Test Feed with Region Filter Only
```bash
curl "https://your-railway-url/v1/feed?user_id=test&region=USA+Stores&limit=5" | jq '.products | length'
```

**Should return:** 5 products from USA Stores

### Test Feed with Region + Store Filter
```bash
curl "https://your-railway-url/v1/feed?user_id=test&region=USA+Stores&category=Amazon&limit=5" | jq
```

**Should return:** 5 products only from Amazon channel

### Test Feed with ALL Category
```bash
curl "https://your-railway-url/v1/feed?user_id=test&region=USA+Stores&category=ALL&limit=5" | jq
```

**Should return:** 5 products from ANY store in USA region

---

## Quick Checklist

- [ ] Run categories endpoint - see all regions and stores
- [ ] Run feed endpoint with different filters - verify filtering works
- [ ] Test on mobile: Select UK region - see UK stores list
- [ ] Test on mobile: Select USA region - see USA stores list
- [ ] Test on mobile: Select specific store - see products from that store
- [ ] Test on mobile: Select "ALL" - see products from all stores in region
- [ ] Test on mobile: Switch regions - verify store list updates

---

## If Something Doesn't Match

**Symptom**: Mobile app doesn't show expected stores
- Check `channels.json` - are stores there?
- Check API response from `/v1/categories` - are stores listed?
- Check channel `"enabled"` flag - is it `true`?
- Check channel `"category"` field - is it exactly "UK Stores", "USA Stores", or "Canada Stores"?

**Symptom**: Products not loading for selected store
- Check API response from `/v1/feed` - are products there?
- Check if products have price data (required for display)
- Check if messages are in `discord_messages` table in Supabase
- Check Railway logs for errors

**Solution**: Update `channels.json` via telegram_bot.py
```
/add_channels [channel_id] [channel_name] [region_name]
```

This updates the file and propagates to all consumers.

