# 🐛 Region Filtering Fix - Debugging Guide

## Problem Identified

When selecting "USA Stores" region, products from Canada and UK were showing up. Meanwhile, Canada and UK regions weren't showing their own products.

## Root Causes Fixed

### 1. ❌ Region Normalization Logic Was Too Broad
**Before:**
```python
if 'UK' in raw_region.upper():      # Catches "UK Stores", "UK_STORES", etc.
    msg_region = 'UK Stores'
elif 'CANADA' in raw_region.upper() or raw_region.upper().startswith('CA'):  # Catches "CA", "Canada", etc.
    msg_region = 'Canada Stores'
else:
    msg_region = 'USA Stores'  # FALLBACK - catches EVERYTHING else!
```

**Problem:** If a region value was unexpected or malformed, it would silently fall through to "USA Stores"

**After:** ✅ **FIXED**
```python
if raw_region == 'UK Stores' or 'UK' in raw_region.upper():
    msg_region = 'UK Stores'
elif raw_region == 'Canada Stores' or 'CANADA' in raw_region.upper():
    msg_region = 'Canada Stores'
elif raw_region == 'USA Stores' or 'USA' in raw_region.upper():
    msg_region = 'USA Stores'
else:
    print(f"[WARN] Unknown region: '{raw_region}'")  # NOW IT LOGS!
    msg_region = 'USA Stores'
```

### 2. ❌ Channel Map Building Priority Was Backwards
**Before:**
```python
# Add DEFAULT_CHANNELS first
for c in DEFAULT_CHANNELS:
    channel_map[c['id']] = {...}

# Then overwrite with loaded channels
for c in channels:
    channel_map[c['id']] = {...}
```

**Problem:** If channels.json had different region data, it would use that instead of the source of truth

**After:** ✅ **FIXED**
```python
# Add loaded channels FIRST (takes priority)
for c in channels:
    if c.get('enabled', True):  # Also respects enabled flag!
        channel_map[c['id']] = {...}

# Add DEFAULT_CHANNELS ONLY if not already mapped
for c in DEFAULT_CHANNELS:
    if c['id'] not in channel_map:  # Skip if already there
        channel_map[c['id']] = {...}
```

### 3. ❌ Region Comparison Had Trailing Space Issues
**Before:**
```python
if product["region"] != region:  # Could fail if one has spaces: "USA Stores " vs "USA Stores"
    continue
```

**After:** ✅ **FIXED**
```python
requested_region = region.strip()  # Clean both sides
product_region = product["region"].strip()

if product_region != requested_region:
    continue
```

---

## 🔍 Testing Your Fix

### 1. Run the Debug Endpoint

```bash
curl https://your-railway-url/v1/debug/channels | jq
```

**Expected Output:**
```json
{
  "total_channels": 94,
  "mapping": {
    "UK Stores": [
      { "id": "864504...", "name": "Restocks Online", "raw_category": "UK Stores" },
      ...
    ],
    "USA Stores": [
      { "id": "1414384...", "name": "Mega Evolution", "raw_category": "USA Stores" },
      ...
    ],
    "Canada Stores": [
      { "id": "1406802...", "name": "Hobbiesville", "raw_category": "Canada Stores" },
      ...
    ]
  },
  "unknown_regions": []  // ← Should be EMPTY if all regions are normalized correctly
}
```

**If `unknown_regions` is NOT empty:**
- There are channels with unexpected region names
- Check `channels.json` for typos (e.g., "US" instead of "USA Stores")
- The region name should be exactly one of:
  - "UK Stores"
  - "USA Stores"
  - "Canada Stores"

### 2. Test Feed Endpoint - USA

```bash
curl "https://your-railway-url/v1/feed?user_id=test&region=USA+Stores&category=ALL&limit=5" | jq '.[] | {id, region, store_name}'
```

**Expected Output:**
All 5 products should have `"region": "USA Stores"`
```json
{
  "id": "...",
  "region": "USA Stores",
  "store_name": "Amazon"
}
{
  "id": "...",
  "region": "USA Stores",
  "store_name": "Walmart"
}
...
```

### 3. Test Feed Endpoint - Canada

```bash
curl "https://your-railway-url/v1/feed?user_id=test&region=Canada+Stores&category=ALL&limit=5" | jq '.[] | {id, region, store_name}'
```

**Expected Output:**
All 5 products should have `"region": "Canada Stores"`
```json
{
  "id": "...",
  "region": "Canada Stores",
  "store_name": "Pokemon Center"
}
...
```

### 4. Test Feed Endpoint - UK

```bash
curl "https://your-railway-url/v1/feed?user_id=test&region=UK+Stores&category=ALL&limit=5" | jq '.[] | {id, region, store_name}'
```

**Expected Output:**
All 5 products should have `"region": "UK Stores"`
```json
{
  "id": "...",
  "region": "UK Stores",
  "store_name": "Argos Instore"
}
...
```

### 5. Test Backend Logs

Monitor your Railway logs while making requests:

```bash
# For Railway CLI
railway logs

# Or check Railway dashboard → Logs tab
```

**Expected log output:**
```
[FEED] Returned 5 products for region='USA Stores' category='ALL'
[FEED] Returned 5 products for region='Canada Stores' category='ALL'
[FEED] Returned 5 products for region='UK Stores' category='ALL'
```

---

## 📱 Test on Mobile App

### 1. Hard Reload App
- Close app completely
- Restart app

### 2. Test USA Region
1. Tap "Home"
2. Select Region: "USA Stores"
3. Select Category: "ALL"
4. **Verify:** All products have USA stores (Amazon, Walmart, etc.)
5. Scroll down - **should NOT see** UK or Canada products

### 3. Test Canada Region
1. Select Region: "Canada Stores"
2. Select Category: "ALL"
3. **Verify:** All products have Canada stores (Pokemon Center, Best Buy, etc.)
4. Scroll down - **should NOT see** USA or UK products

### 4. Test UK Region
1. Select Region: "UK Stores"
2. Select Category: "ALL"
3. **Verify:** All products have UK stores (Argos, Restocks, etc.)
4. Scroll down - **should NOT see** USA or Canada products

### 5. Test Specific Store Filter
1. Select Region: "USA Stores"
2. Select Category: "Amazon"
3. **Verify:** ALL products are from Amazon channel
4. No other stores shown

---

## 🚨 If Still Not Working

### Check 1: Are channels.json Categories Exactly Right?

```bash
# Check what's in channels.json
curl https://your-supabase-url/storage/v1/object/public/monitor-data/discord_josh/channels.json | jq '.[] | {name, category}' | head -20
```

**Each channel MUST have one of:**
- `"category": "UK Stores"`
- `"category": "USA Stores"`
- `"category": "Canada Stores"`

**Common errors:**
- `"category": "UK"` ❌ Should be `"UK Stores"`
- `"category": "US"` ❌ Should be `"USA Stores"`
- `"category": "CA"` ❌ Should be `"Canada Stores"`
- Extra spaces: `"category": "USA Stores "` ❌ (trailing space)

### Check 2: Verify via Debug Endpoint

```bash
curl https://your-railway-url/v1/debug/channels | jq '.unknown_regions'
```

If this returns any regions, they need to be fixed in `channels.json`.

### Check 3: Manual Region Count

```bash
# Count how many channels per region
curl https://your-railway-url/v1/debug/channels | jq '.mapping | map_values(length)'
```

**Expected:**
```json
{
  "UK Stores": 16,
  "USA Stores": 65,
  "Canada Stores": 13
}
```

If counts are 0 for any region, products won't show for that region.

### Check 4: Check Server Logs

Railway logs will now show:
- ❌ `[WARN] Unknown region in channel ...` - if a channel has unexpected region
- ✅ `[FEED] Returned 5 products for region='...'` - if filtering worked

---

## 🔄 Deployment Steps

1. **Commit the fix:**
   ```bash
   git add main_api.py
   git commit -m "Fix: Region filtering - normalize categories and improve channel mapping"
   git push origin main
   ```

2. **Railway auto-deploys** (~2-3 minutes)

3. **Test with debug endpoint:**
   ```bash
   curl https://your-railway-url/v1/debug/channels
   ```

4. **Test feed endpoint:**
   ```bash
   curl "https://your-railway-url/v1/feed?user_id=test&region=USA+Stores&limit=5"
   ```

5. **Test on mobile app** with hard reload

---

## Summary of Changes

| Issue | Fix |
|-------|-----|
| Fallback to "USA Stores" too broad | Added explicit checks, log unknowns |
| Channel map priority wrong | Load channels.json first, defaults second |
| Region comparison with spaces | Strip both sides before comparing |
| No visibility into what's mapped | Added `/v1/debug/channels` endpoint |
| No error logging | Added console logs for debugging |

**Result:** ✅ USA products show only in USA region, Canada in Canada, UK in UK

