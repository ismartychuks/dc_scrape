# 🔧 Quick Railway Supabase Fix Checklist

## Problem
Category endpoint returns only 3 default channels instead of all channels from Supabase.

## Root Cause
`main_api.py` wasn't loading environment variables, so Supabase credentials weren't available on Railway.

## ✅ What Was Fixed
- Added `load_dotenv()` to load environment variables
- Enhanced error logging in category endpoint  
- Added `/v1/debug/supabase` endpoint to test connectivity
- Updated `/v1/debug/channels` to show data source

## 🚀 Action Items

### 1. Redeploy on Railway
- Push is already done ✓
- Railway should auto-detect the changes
- Check **Deployments** tab to confirm latest deploy

### 2. Verify Environment Variables in Railway
```
Go to: Railway Dashboard → Your Project → Your Service → Variables

Ensure these are set:
✓ SUPABASE_URL=https://your-project.supabase.co  
✓ SUPABASE_KEY=your-anon-key
✓ Other vars (TELEGRAM_TOKEN, etc.)
```

### 3. Test the Fix
Call the debug endpoint:
```bash
curl https://your-railway-app.railway.app/v1/debug/supabase
```

Expected result: All tests show status 200-204 ✓

### 4. Check Categories  
```bash
curl https://your-railway-app.railway.app/v1/categories
```

Expected: `"source": "remote"` with many channels (not defaults)

## 📊 New Endpoints

- **`/v1/debug/supabase`** - Tests all Supabase connectivity  
  Returns detailed test results for storage and REST API

- **`/v1/categories`** - Now includes source info
  Returns: `{"categories": {...}, "source": "remote|local|defaults", "channel_count": N}`

- **`/v1/debug/channels`** - Shows channel source
  Now includes `"channels_source"` field

## 🔍 Troubleshooting

| Problem | Check |
|---------|-------|
| Still showing defaults | `/v1/debug/supabase` tests - see which one fails |
| Status 401/403 | Check API key is correct in Variables |
| Status 404 | Check SUPABASE_URL format (no trailing slash) |
| Connection Error | Verify Supabase project is active |
| Timeout | Check network - may need firewall rules |

## 📝 Files Changed
- `main_api.py` - Added load_dotenv() and better logging
- `RAILWAY_SUPABASE_FIX.md` - Detailed diagnostic guide
