#!/usr/bin/env python3
"""Quick test to verify no syntax errors in app.py"""

import sys
sys.path.insert(0, '.')

try:
    import app
    print("✅ app.py loads successfully - no syntax errors")
    print(f"✅ Found {len([x for x in dir(app) if not x.startswith('_')])} functions/classes")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"⚠️ Import warning (may be normal): {e}")
    print("But no syntax errors detected")
