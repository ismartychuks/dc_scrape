# 🧪 Railway Supabase Fix - Testing Commands

## Your Railway App URL
Replace `YOUR_APP_URL` with your actual Railway domain (e.g., `https://your-service-xxxxx.railway.app`)

## Test 1: Health Check (Sanity)
```bash
curl https://YOUR_APP_URL/
```

Expected response:
```json
{\"status\": \"online\", \"app\": \"SmartyMetrics API\", \"v\": \"1.0.0\"}
```

## Test 2: Supabase Connectivity Diagnostics ⭐ (MOST IMPORTANT)
```bash
curl https://YOUR_APP_URL/v1/debug/supabase
```

This tells you exactly what's working and what's broken.

**Good response** (if all passing):
```json
{
  \"supabase_url\": \"https://your-project...\",
  \"supabase_key_set\": true,
  \"env_vars_loaded\": true,
  \"tests\": {
    \"storage_head_request\": {\"status\": 200, \"ok\": true},
    \"channels_json_get\": {\"status\": 200, \"content_length\": 1234, \"is_json\": true, \"ok\": true},
    \"rest_api_users\": {\"status\": 200, \"ok\": true}
  }
}
```

**Bad responses** (troubleshooting):
- `env_vars_loaded: false` → Variables NOT set in Railway Dashboard
- `rest_api_users.status: 401` → Wrong/invalid API key
- `rest_api_users.status: 403` → Permission issue
- `rest_api_users.status: 404` → Wrong Supabase URL
- `channels_json_get.status: 404` → Storage path wrong or bucket doesn't exist
- `error: \"Connection refused\"` → Supabase unreachable (firewall/network)
- `error: \"timed out\"` → Supabase not responding

## Test 3: Categories Endpoint (The Real Test)
```bash
curl https://YOUR_APP_URL/v1/categories | jq .
```

**Good response** (channels from Supabase):
```json
{
  \"categories\": {
    \"UK Stores\": [\"ALL\", \"Collectors Amazon\", \"Argos Instore\", \"...more stores...\"],
    \"USA Stores\": [\"ALL\", \"...stores...\"],
    \"Canada Stores\": [\"ALL\", \"...stores...\"]
  },
  \"source\": \"remote\",
  \"channel_count\": 23
}
```

**Bad response** (only defaults):
```json
{
  \"categories\": {
    \"UK Stores\": [\"ALL\", \"Collectors Amazon\", \"Argos Instore\", \"Restocks Online\"],
    \"USA Stores\": [\"ALL\"],
    \"Canada Stores\": [\"ALL\"]
  },
  \"source\": \"defaults\",
  \"channel_count\": 3
}
```

If `source` is \"defaults\", the fix didn't work - see diagnostic test above.

## Test 4: Channel Debug Info
```bash
curl https://YOUR_APP_URL/v1/debug/channels | jq .
```

Shows:
- Total channels loaded
- Which region each channel maps to
- Any unknown/orphaned channels
- **channels_source**: tells you if it came from remote/local/defaults

## Test 5: Check Railway Logs
Go to Railway Dashboard → Your Service → Logs

Look for these messages:
```
[CATEGORIES] Attempting remote fetch from: https://...
[CATEGORIES] Remote response status: 200
[CATEGORIES] ✓ Loaded 23 channels from remote
```

or

```
[CATEGORIES] ✗ Remote channels fetch failed: ConnectionError
[CATEGORIES] ⚠️ Using DEFAULT_CHANNELS (3 channels)
```

---

## Quick Diagnosis Flow

1. **Call `/v1/debug/supabase`**
   - ✓ All ok? → Issue fixed!
   - ✗ Failures? → Check which test failed:

2. **If `env_vars_loaded: false`**
   ```
   → Go to Railway Dashboard
   → Variables tab
   → Add SUPABASE_URL and SUPABASE_KEY
   → Redeploy
   ```

3. **If `storage_head_request` fails**
   ```
   → Check SUPABASE_URL format (no trailing /)
   → Verify storage bucket exists in Supabase
   → Check API key permissions
   ```

4. **If `rest_api_users` fails**  
   ```
   → Check SUPABASE_KEY (should be anon key, not secret)
   → Verify Supabase project is active
   → Check row-level security policies allow read
   ```

---

## One-Liner to Test Everything
```bash
RAILWAY_URL=\"https://YOUR_APP_URL\"; \
echo \"=== Health ===\"  && curl -s $RAILWAY_URL/ | jq . && \
echo \"\\n=== Supabase Diags ===\"  && curl -s $RAILWAY_URL/v1/debug/supabase | jq . && \
echo \"\\n=== Categories ===\"  && curl -s $RAILWAY_URL/v1/categories | jq .source,.channel_count
```

---

## Need More Help?

1. **What does each test mean?**
   - `storage_head_request` = Can we reach Supabase storage?
   - `channels_json_get` = Can we download channels.json file?
   - `rest_api_users` = Can we access REST API database?

2. **Why 3 tests instead of 1?**
   - Storage and REST API are different services
   - Isolating them helps identify exactly what's broken

3. **When should I retry?**
   - After changing variables, wait 10-30 seconds for Railway redeploy
   - Then test again
