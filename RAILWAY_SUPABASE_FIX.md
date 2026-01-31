# 🚨 Railway Supabase Connectivity Fix

## Problem Diagnosed
The category endpoint on Railway is returning **default values** instead of your actual channels from Supabase. This means Supabase is unreachable from your Railway deployment.

---

## Root Causes

### 1. ❌ **Missing `load_dotenv()` in main_api.py**
   - **Issue**: `supabase_utils.py` calls `load_dotenv()`, but it loads from `.env` file on the local system
   - **In Railway**: `.env` files don't exist; you need environment variables set in Railway Dashboard
   - **Result**: `SUPABASE_URL` and `SUPABASE_KEY` weren't being loaded properly

### 2. ❌ **Silent Failures with No Logging**
   - **Issue**: The category endpoint silently caught all exceptions and fell back to defaults
   - **Result**: You couldn't see that Supabase requests were failing
   - **Impact**: Default 3 channels returned instead of actual ones

### 3. ❌ **Possible Railway Configuration Issues**
   - Missing or incorrect environment variables in Railway Dashboard
   - Network connectivity issues between Railway and Supabase
   - Incorrect Supabase URL or API key format

---

## ✅ What I Fixed

### Changes to `main_api.py`:

1. **Added `load_dotenv()` import and call**
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # Load environment variables
   ```

2. **Enhanced error logging in `/v1/categories` endpoint**
   ```python
   # Now shows:
   # - Exact URL being requested
   # - HTTP status code
   # - Response body on errors
   # - Connection timeout vs other errors
   # - Source of data (remote, local file, or defaults)
   ```

3. **Added new debug endpoints**:
   - `/v1/debug/supabase` - Tests Supabase connectivity
   - `/v1/debug/channels` - Shows channel source and mapping

4. **Improved return values**
   - `/v1/categories` now returns: `{"categories": {...}, "source": "remote|local|defaults", "channel_count": N}`

---

## 🔍 Diagnostic Steps

### Step 1: Verify Environment Variables on Railway

1. Go to [Railway Dashboard](https://railway.app)
2. Select your project → your service
3. Click **Variables** tab
4. Confirm these are set:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-api-key
   ```

### Step 2: Test New Debug Endpoint

Call the new Supabase connectivity test:
```bash
curl https://your-railway-app.railway.app/v1/debug/supabase
```

**Expected response** (if working):
```json
{
  "supabase_url": "https://your-project...",
  "supabase_key_set": true,
  "env_vars_loaded": true,
  "tests": {
    "storage_head_request": {"status": 200, "ok": true},
    "channels_json_get": {"status": 200, "content_length": 1234, "is_json": true, "ok": true},
    "rest_api_users": {"status": 200, "ok": true}
  }
}
```

**Problem indicators**:
- `env_vars_loaded: false` → Variables not set in Railway
- `status: 401` or `403` → Invalid API key
- `status: 404` → Wrong Supabase URL
- `ConnectionError` → Network/firewall issue
- `Timeout` → Supabase server not responding

### Step 3: Check Category Endpoint Response

```bash
curl https://your-railway-app.railway.app/v1/categories
```

**Good response** (channels from remote):
```json
{
  "categories": {
    "UK Stores": ["ALL", "Collectors Amazon", "Argos Instore", ...],
    "USA Stores": ["ALL", ...],
    ...
  },
  "source": "remote",
  "channel_count": 23
}
```

**Bad response** (only defaults):
```json
{
  "categories": {...},
  "source": "defaults",
  "channel_count": 3
}
```

### Step 4: Check Railway Logs

1. Go to Railway Dashboard → Your service
2. Click **Logs** tab
3. Look for these messages:
   - ✓ `[CATEGORIES] ✓ Loaded X channels from remote` → Working!
   - ✗ `[CATEGORIES] ✗ Remote channels fetch failed` → Problem needs diagnosis
   - ⚠️ `[CATEGORIES] ⚠️ Using DEFAULT_CHANNELS` → Supabase unreachable

---

## 🛠️ Common Fixes

### Fix 1: Variables Not Set in Railway

1. Go to Railway Dashboard
2. Select project → service
3. Click **Variables**
4. Add/update:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   ```
5. **Redeploy** the service (Railway usually auto-redeploys)

### Fix 2: Wrong Supabase URL Format

Ensure URL has NO trailing slash:
- ✓ Correct: `https://abcxyz.supabase.co`
- ✗ Wrong: `https://abcxyz.supabase.co/`

### Fix 3: Using Wrong API Key

Get the correct key from Supabase:
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Click **Settings** → **API**
4. Copy **anon public** key (NOT the secret key)

### Fix 4: Network/Firewall Issue

If `/v1/debug/supabase` shows `ConnectionError`:
1. Check if Supabase has IP whitelisting enabled
2. Add Railway's IP range to Supabase whitelist (if applicable)
3. Verify Supabase project is active (not paused)

---

## 📋 What to Report if Still Broken

Once you've deployed these changes and set variables correctly, if it's STILL showing defaults:

1. **Curl the debug endpoint** and paste response:
   ```bash
   curl https://your-railway-app.railway.app/v1/debug/supabase
   ```

2. **Check Railway logs** for:
   - Exact error messages
   - Connection errors
   - HTTP status codes

3. **Verify**:
   - [ ] Environment variables are set in Railway Dashboard
   - [ ] No typos in SUPABASE_URL or SUPABASE_KEY
   - [ ] Supabase project is active
   - [ ] Railway service is redeployed after variable changes

---

## 🎯 Expected Behavior After Fix

✅ **Working**:
- `/v1/categories` returns all channels with `"source": "remote"`
- `/v1/debug/supabase` shows all tests passing
- `/v1/debug/channels` shows proper regional mapping
- Railway logs show `[CATEGORIES] ✓ Loaded X channels from remote`

---

## 📝 Notes

- The app has **3 fallback layers**: remote Supabase → local file → defaults
- **Only the defaults should be used as a last resort** for emergency operation
- If running locally with `.env` file, it will use that (but Railway ignores `.env`)
- Future improvement: Consider caching channels in Railway to reduce Supabase hits
