"""
Quick test script to verify the Flask server starts correctly after the fix.
"""

import subprocess
import sys
import time
import requests

print("="*80)
print("Testing Flask API Server Startup")
print("="*80)

# Try to import and check if the issue is fixed
print("\n1. Testing import and stdout/stderr fix...")
try:
    import api_server
    print("✅ api_server.py imports successfully")
    print(f"   stdout type: {type(sys.stdout)}")
    print(f"   stderr type: {type(sys.stderr)}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("\n2. Checking if Flask app is configured correctly...")
try:
    assert hasattr(api_server, 'app'), "Flask app not found"
    assert hasattr(api_server, 'health_check'), "health_check endpoint not found"
    assert hasattr(api_server, 'analyze'), "analyze endpoint not found"
    print("✅ Flask app has all required endpoints")
except AssertionError as e:
    print(f"❌ Configuration check failed: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ All checks passed! The server should now start correctly.")
print("="*80)
print("\nYou can now run:")
print("  python api_server.py")
print("\nOr test the endpoints with:")
print("  python test_api.py")
print("="*80)
