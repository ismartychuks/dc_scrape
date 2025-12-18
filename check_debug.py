#!/usr/bin/env python3
"""
Check if DEBUG environment variable is set correctly.
"""

import os
import sys

print("\n" + "="*60)
print("DEBUG ENVIRONMENT CHECK")
print("="*60 + "\n")

# Check current DEBUG setting
debug_env = os.getenv("DEBUG", "(not set)")
print(f"Current DEBUG environment variable: {debug_env}")

# Check if it's recognized
if debug_env.lower() in ("true", "1", "yes", "on"):
    print("✅ DEBUG will be ENABLED in app.py\n")
elif debug_env == "(not set)":
    print("❌ DEBUG is NOT SET\n")
else:
    print(f"❌ DEBUG value '{debug_env}' is not recognized\n")

print("VALID DEBUG VALUES:")
print("  ✓ True")
print("  ✓ true")
print("  ✓ 1")
print("  ✓ yes")
print("  ✓ on")

print("\nTO ENABLE DEBUG MODE:")
print("\nOption 1 - Command line (PowerShell):")
print("  $env:DEBUG = 'True'")
print("  python app.py")

print("\nOption 2 - Command line (CMD):")
print("  set DEBUG=True")
print("  python app.py")

print("\nOption 3 - Add to .env file:")
print("  DEBUG=True")
print("  (then restart python app.py)")

print("\nOption 4 - Double-click batch file:")
print("  run_debug.bat")

print("\n" + "="*60)

# If not set, offer to set it
if debug_env == "(not set)":
    print("\n⚠️  DEBUG is not currently set!")
    print("\nWould you like me to set it? (Y/n)")
    response = input().strip().lower()
    if response != 'n':
        os.environ['DEBUG'] = 'True'
        print("\n✅ DEBUG set to True for this session")
        print("   (You'll need to set it again next time)")
        print("\n   To make it permanent, add to .env file:")
        print("   DEBUG=True")

print("="*60 + "\n")
