#!/usr/bin/env python3
"""
Test OpenRouter API key persistence specifically.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def test_openrouter_persistence():
    """Test that OpenRouter API key persists correctly."""
    print("🔑 Testing OpenRouter API Key Persistence")
    print("=" * 50)
    
    # Step 1: Save an OpenRouter key
    print("1️⃣ Saving OpenRouter API key...")
    settings_manager = SettingsManager()
    
    test_key = "sk-or-test-persistence-123456789"
    result = settings_manager.set_setting('openrouter_api_key', test_key)
    print(f"   Save result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Step 2: Verify it's saved immediately
    print("2️⃣ Immediate verification...")
    saved_key = settings_manager.get_setting('openrouter_api_key', '')
    print(f"   Retrieved key: '{saved_key[:15]}...' (masked)")
    immediate_match = (saved_key == test_key)
    print(f"   Immediate match: {'✅ YES' if immediate_match else '❌ NO'}")
    
    # Step 3: Create new settings manager (simulate app restart)
    print("3️⃣ Simulating app restart...")
    del settings_manager  # Delete current instance
    fresh_manager = SettingsManager()  # Create new instance
    
    fresh_key = fresh_manager.get_setting('openrouter_api_key', '')
    print(f"   Fresh key: '{fresh_key[:15]}...' (masked)")
    restart_match = (fresh_key == test_key)
    print(f"   Restart match: {'✅ YES' if restart_match else '❌ NO'}")
    
    # Step 4: Check the raw file
    print("4️⃣ Checking raw settings file...")
    try:
        import json
        settings_file = fresh_manager.settings_file
        with open(settings_file, 'r') as f:
            content = json.load(f)
        
        file_key = content.get('openrouter_api_key', 'NOT_FOUND')
        print(f"   File key: '{file_key[:15]}...' (masked)")
        file_match = (file_key == test_key)
        print(f"   File match: {'✅ YES' if file_match else '❌ NO'}")
        
    except Exception as e:
        print(f"   File check error: {e}")
        file_match = False
    
    # Step 5: Cleanup
    print("5️⃣ Cleanup...")
    fresh_manager.set_setting('openrouter_api_key', '')
    print("   Test data cleaned up ✅")
    
    # Final result
    all_passed = result and immediate_match and restart_match and file_match
    
    print(f"\n🎯 RESULT:")
    if all_passed:
        print("✅ OpenRouter API key persistence is working correctly!")
        print("The key will now save and load properly in the application.")
    else:
        print("❌ There are still issues with OpenRouter key persistence:")
        if not result:
            print("   • Key saving failed")
        if not immediate_match:
            print("   • Immediate retrieval failed")
        if not restart_match:
            print("   • Restart persistence failed")
        if not file_match:
            print("   • File persistence failed")
    
    return all_passed

if __name__ == "__main__":
    test_openrouter_persistence()