#!/usr/bin/env python3
"""
Final verification that credential persistence is working correctly.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def final_persistence_test():
    """Final test to verify persistence is working end-to-end."""
    print("🔐 **FINAL CREDENTIAL PERSISTENCE TEST**")
    print("=" * 60)
    
    # Test 1: Save credentials
    print("1️⃣ SAVING CREDENTIALS")
    print("-" * 30)
    
    settings_manager = SettingsManager()
    
    test_username = "final-test-user"
    test_token = "ghp_finaltest123456789"
    test_openrouter = "sk-finaltest123456789"
    
    # Save all credentials
    result1 = settings_manager.set_setting('github_username', test_username)
    result2 = settings_manager.set_setting('github_token', test_token)
    result3 = settings_manager.set_setting('openrouter_api_key', test_openrouter)
    
    print(f"   GitHub Username: {'✅ SAVED' if result1 else '❌ FAILED'}")
    print(f"   GitHub Token:    {'✅ SAVED' if result2 else '❌ FAILED'}")
    print(f"   OpenRouter Key:  {'✅ SAVED' if result3 else '❌ FAILED'}")
    
    save_success = result1 and result2 and result3
    
    # Test 2: Create new settings manager (simulates app restart)
    print(f"\n2️⃣ SIMULATING APP RESTART")
    print("-" * 30)
    
    del settings_manager  # Delete old instance
    fresh_settings_manager = SettingsManager()  # Create new instance
    
    # Load credentials
    loaded_username = fresh_settings_manager.get_setting('github_username', '')
    loaded_token = fresh_settings_manager.get_setting('github_token', '')
    loaded_openrouter = fresh_settings_manager.get_setting('openrouter_api_key', '')
    
    print(f"   GitHub Username: '{loaded_username}'")
    print(f"   GitHub Token:    '{loaded_token[:10]}...' (masked)")
    print(f"   OpenRouter Key:  '{loaded_openrouter[:10]}...' (masked)")
    
    # Test 3: Verify persistence
    print(f"\n3️⃣ PERSISTENCE VERIFICATION")
    print("-" * 30)
    
    username_persisted = (loaded_username == test_username)
    token_persisted = (loaded_token == test_token)
    openrouter_persisted = (loaded_openrouter == test_openrouter)
    
    print(f"   Username Persisted: {'✅ YES' if username_persisted else '❌ NO'}")
    print(f"   Token Persisted:    {'✅ YES' if token_persisted else '❌ NO'}")
    print(f"   OpenRouter Persisted: {'✅ YES' if openrouter_persisted else '❌ NO'}")
    
    all_persisted = username_persisted and token_persisted and openrouter_persisted
    
    # Test 4: Clean up
    print(f"\n4️⃣ CLEANUP")
    print("-" * 30)
    
    fresh_settings_manager.set_setting('github_username', '')
    fresh_settings_manager.set_setting('github_token', '')
    fresh_settings_manager.set_setting('openrouter_api_key', '')
    print("   Test data cleaned up ✅")
    
    # Final result
    print(f"\n🎯 **FINAL RESULT**")
    print("=" * 60)
    
    if save_success and all_persisted:
        print("🎉 **SUCCESS!** Credential persistence is working perfectly!")
        print("✅ GitHub username, token, and OpenRouter API key all persist correctly")
        print("✅ Save buttons in the GUI will now work as expected")
        print("✅ Users won't need to re-enter credentials on app restart")
    else:
        print("❌ **FAILURE!** There are still issues with persistence:")
        if not save_success:
            print("   • Saving credentials failed")
        if not all_persisted:
            print("   • Credentials are not persisting between sessions")
    
    return save_success and all_persisted

if __name__ == "__main__":
    success = final_persistence_test()
    exit(0 if success else 1)