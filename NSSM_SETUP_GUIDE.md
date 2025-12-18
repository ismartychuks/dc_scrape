# NSSM Setup Guide for Discord Scraper + Telegram Bot on Contabo Windows VPS

## Overview

This guide shows how to set up your Discord scraper and Telegram bot on a Contabo Windows VPS using **NSSM (Non-Sucking Service Manager)** so they run 24/7 with GUI support for CAPTCHA handling.

**NSSM allows:**
✅ GUI apps to run as services  
✅ Automatic restart on VPS reboot  
✅ Handle CAPTCHA and Discord login via browser  
✅ RDP connection to see/interact with the browser  
✅ Survive RDP disconnections  

---

## What We're Setting Up

| Service | Purpose | GUI? | Auto-restart? |
|---------|---------|------|---------------|
| **DiscordScraper** | Scrapes Discord messages | ✅ Yes (for login/CAPTCHA) | ✅ Yes |
| **TelegramBot** | Sends alerts to users | ❌ No (background) | ✅ Yes |

---

## Prerequisites

- Contabo Windows VPS with admin access
- Remote Desktop (RDP) access to VPS
- Python 3.8+ installed
- Virtual environment already set up (`discord` folder)
- All dependencies installed

---

## Step 1: Download NSSM

### Option A: Download Manually (Recommended)

1. Go to: https://nssm.cc/download
2. Download the latest version (e.g., `nssm-2.24-101-g897c7f7.zip`)
3. Extract to: `C:\nssm\` (or any location)

### Option B: Download via PowerShell

```powershell
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://nssm.cc/ci/nssm-2.24-101-g897c7f7.zip" -OutFile "C:\nssm.zip"
Expand-Archive -Path "C:\nssm.zip" -DestinationPath "C:\" -Force
Rename-Item -Path "C:\nssm-2.24-101-g897c7f7" -NewName "nssm" -Force
```

---

## Step 2: Add NSSM to System PATH

This allows you to use `nssm` command from anywhere.

### Via PowerShell (Admin):

```powershell
# Add NSSM to PATH
$nssm_path = "C:\nssm\win64"  # or win32 if 32-bit
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$nssm_path", "Machine")

# Verify
nssm version
```

**Expected output:** `nssm 2.24...`

---

## Step 3: Create Startup Batch Scripts

Create two batch files to launch your Python scripts with the virtual environment activated.

### File 1: Start Discord Scraper
**Save as:** `C:\discord_scraper_start.bat`

```batch
@echo off
cd /d "C:\Users\HP USER\Documents\Data Analyst\discord"
call .\discord\Scripts\activate.bat
python app.py
pause
```

### File 2: Start Telegram Bot
**Save as:** `C:\telegram_bot_start.bat`

```batch
@echo off
cd /d "C:\Users\HP USER\Documents\Data Analyst\discord"
call .\discord\Scripts\activate.bat
python telegram_bot.py
pause
```

---

## Step 4: Install Services with NSSM

### Service 1: Discord Scraper (WITH GUI)

**Run in PowerShell as Administrator:**

```powershell
# Install the service
nssm install DiscordScraper "C:\discord_scraper_start.bat"

# Set to interact with desktop (IMPORTANT for GUI/CAPTCHA)
nssm set DiscordScraper AppInteractive 1

# Set to restart on failure
nssm set DiscordScraper AppRestartDelay 5000

# Set startup type to automatic
nssm set DiscordScraper Start SERVICE_AUTO_START

# Verify
nssm status DiscordScraper
```

### Service 2: Telegram Bot (Background)

**Run in PowerShell as Administrator:**

```powershell
# Install the service
nssm install TelegramBot "C:\telegram_bot_start.bat"

# No GUI needed - leave as default
nssm set TelegramBot AppRestartDelay 5000

# Set startup type to automatic
nssm set TelegramBot Start SERVICE_AUTO_START

# Verify
nssm status TelegramBot
```

---

## Step 5: Start the Services

### Start both services:

```powershell
# Start Discord Scraper
nssm start DiscordScraper

# Start Telegram Bot
nssm start TelegramBot

# Check status
nssm status DiscordScraper
nssm status TelegramBot
```

**Expected output:** `SERVICE_RUNNING`

---

## Step 6: Connect via RDP to See the Browser

### Login to Contabo VPS:

1. Open **Remote Desktop Connection** on your computer
2. Enter VPS IP address
3. Login with your credentials

### When connected:

- You'll see the **Discord Scraper browser window** running
- You can interact with it (login, solve CAPTCHA, etc.)
- The **Telegram Bot** runs silently in background
- **Everything persists even if you disconnect RDP**

---

## CAPTCHA Handling with NSSM

### How it works:

1. **App.py encounters CAPTCHA:**
   - Browser shows CAPTCHA on screen
   - NSSM displays it in your RDP session

2. **You solve it interactively:**
   - Move mouse to CAPTCHA
   - Click/solve the challenge
   - App continues automatically

3. **No timeout issues:**
   - NSSM keeps the browser window alive
   - Even if RDP disconnects, browser keeps running
   - CAPTCHAs can be solved from another RDP session

### Example workflow:

```
1. Connect via RDP
2. See CAPTCHA in browser
3. Solve it
4. Disconnect RDP
5. Bot keeps running
6. Next CAPTCHA? Just RDP back in and solve
```

---

## Step 7: Manage Services

### View service status:

```powershell
# Check all services
nssm status DiscordScraper
nssm status TelegramBot

# View service details
nssm dump DiscordScraper
```

### Stop a service:

```powershell
nssm stop DiscordScraper
nssm stop TelegramBot
```

### Remove a service:

```powershell
nssm remove DiscordScraper confirm
nssm remove TelegramBot confirm
```

### View logs:

```powershell
# NSSM stores logs in event viewer
# Open Event Viewer → Windows Logs → Application
# Look for DiscordScraper or TelegramBot entries
```

---

## Step 8: Auto-Start on VPS Reboot

Services are already set to auto-start. Verify:

```powershell
# Check startup type
nssm get DiscordScraper Start
nssm get TelegramBot Start

# Should return: SERVICE_AUTO_START
```

### Restart VPS to test:

```powershell
Restart-Computer -Force
```

After restart:
- Services auto-start
- Connect via RDP
- Both services running automatically ✓

---

## Troubleshooting

### Service won't start

```powershell
# Check status and error
nssm status DiscordScraper
nssm query DiscordScraper

# Check Windows Event Viewer
# Event Viewer → Windows Logs → Application → Look for errors
```

**Common issues:**
- Batch file path incorrect → Fix path in bat file
- Virtual environment not activated → Check `.bat` script
- Permissions issue → Run PowerShell as Administrator

### Browser doesn't appear in RDP

```powershell
# Ensure AppInteractive is set for DiscordScraper
nssm set DiscordScraper AppInteractive 1

# Restart service
nssm restart DiscordScraper
```

### CAPTCHA timeout

```powershell
# Increase app timeout in app.py
# Search for: PLAYWRIGHT_TIMEOUT or similar
# Increase value from default to 120+ seconds

# Then restart:
nssm restart DiscordScraper
```

### High CPU/Memory usage

```powershell
# Reduce poll interval in telegram_bot.py
# Change: POLL_INTERVAL = 10
# To: POLL_INTERVAL = 30  (check every 30 seconds instead)

# Restart service
nssm restart TelegramBot
```

---

## Complete Setup Checklist

- [ ] NSSM downloaded and extracted to `C:\nssm\`
- [ ] NSSM added to PATH (can run `nssm version`)
- [ ] `C:\discord_scraper_start.bat` created and tested
- [ ] `C:\telegram_bot_start.bat` created and tested
- [ ] DiscordScraper service installed with `AppInteractive 1`
- [ ] TelegramBot service installed
- [ ] Both services set to `SERVICE_AUTO_START`
- [ ] Both services started and showing `SERVICE_RUNNING`
- [ ] Can RDP in and see Discord browser
- [ ] Telegram alerts working
- [ ] VPS rebooted and services auto-started

---

## Quick Reference Commands

```powershell
# Check all services
Get-Service | Where-Object {$_.Name -like "*Scraper*" -or $_.Name -like "*Bot*"}

# View service config
nssm dump DiscordScraper
nssm dump TelegramBot

# Edit service settings (GUI)
nssm edit DiscordScraper
nssm edit TelegramBot

# Check logs
Get-EventLog Application -Source nssm -Newest 20

# Start both
nssm start DiscordScraper; nssm start TelegramBot

# Stop both
nssm stop DiscordScraper; nssm stop TelegramBot

# Restart both
nssm restart DiscordScraper; nssm restart TelegramBot
```

---

## Security Notes

⚠️ **Important:**
- Don't leave RDP session open unnecessarily
- Use strong Contabo VPS password
- Keep Discord credentials secure
- Limit who has RDP access

---

## Next Steps

1. **Follow this guide step-by-step**
2. **Test locally first** (optional) - run both scripts manually
3. **Deploy to Contabo VPS** - follow Steps 1-5
4. **Verify both services** are running
5. **Connect via RDP** and test Discord login/CAPTCHA
6. **Monitor logs** for any issues

---

## Support

If you encounter issues:

1. **Check Event Viewer** for error messages
2. **Verify batch file paths** - use absolute paths
3. **Test batch file manually** - double-click it
4. **Restart services** - `nssm restart DiscordScraper`
5. **Check Python installation** - `python --version`
6. **Verify virtual environment** - `.bat` script activates it

---

**You're all set!** Your Discord scraper and Telegram bot will now run 24/7 on your Contabo VPS with full GUI support for CAPTCHAs. 🚀
