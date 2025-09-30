#!/usr/bin/env python3
"""
Test script to verify credential saving and loading functionality.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def test_credential_persistence():
    """Test that credentials can be saved and loaded properly."""
    print("🧪 Testing Credential Persistence")
    print("=" * 50)
    
    # Initialize settings manager
    settings_manager = SettingsManager()
    
    # Test data
    test_username = "test-user"
    test_token = "ghp_test123456789"
    test_openrouter_key = "sk-or-test123456789"
    
    try:
        # Test saving GitHub credentials
        print("💾 Testing GitHub credential saving...")
        settings_manager.set_setting('github_username', test_username)
        settings_manager.set_setting('github_token', test_token)
        settings_manager.save_settings()
        print("✅ GitHub credentials saved")
        
        # Test saving OpenRouter key
        print("💾 Testing OpenRouter key saving...")
        settings_manager.set_setting('openrouter_api_key', test_openrouter_key)
        settings_manager.save_settings()
        print("✅ OpenRouter key saved")
        
        # Test loading credentials
        print("📂 Testing credential loading...")
        loaded_username = settings_manager.get_setting('github_username', '')
        loaded_token = settings_manager.get_setting('github_token', '')
        loaded_openrouter = settings_manager.get_setting('openrouter_api_key', '')
        
        # Verify loaded data
        assert loaded_username == test_username, f"Username mismatch: {loaded_username} != {test_username}"
        assert loaded_token == test_token, f"Token mismatch: {loaded_token} != {test_token}"
        assert loaded_openrouter == test_openrouter_key, f"OpenRouter key mismatch"
        
        print("✅ All credentials loaded correctly")
        
        # Test credential masking for display
        print("🎭 Testing credential masking...")
        if len(loaded_token) > 8:
            masked_token = loaded_token[:4] + "..." + loaded_token[-4:]
            print(f"   • Original token: {loaded_token}")
            print(f"   • Masked token: {masked_token}")
        
        if len(loaded_openrouter) > 8:
            masked_openrouter = loaded_openrouter[:6] + "..." + loaded_openrouter[-4:]
            print(f"   • Original OpenRouter: {loaded_openrouter}")
            print(f"   • Masked OpenRouter: {masked_openrouter}")
        
        # Cleanup test data
        print("🧹 Cleaning up test data...")
        settings_manager.set_setting('github_username', '')
        settings_manager.set_setting('github_token', '')
        settings_manager.set_setting('openrouter_api_key', '')
        settings_manager.save_settings()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_settings_file_location():
    """Test settings file location and accessibility."""
    print(f"\n📍 Testing Settings File Location")
    print("=" * 50)
    
    settings_manager = SettingsManager()
    
    # Get settings file path
    settings_path = settings_manager.settings_file
    print(f"Settings file location: {settings_path}")
    
    # Check if directory exists
    settings_dir = os.path.dirname(settings_path)
    if os.path.exists(settings_dir):
        print(f"✅ Settings directory exists: {settings_dir}")
    else:
        print(f"❌ Settings directory missing: {settings_dir}")
    
    # Check file permissions
    try:
        # Try to write a test setting
        settings_manager.set_setting('test_key', 'test_value')
        settings_manager.save_settings()
        
        # Try to read it back
        test_value = settings_manager.get_setting('test_key', '')
        assert test_value == 'test_value'
        
        # Clean up
        settings_manager.set_setting('test_key', '')
        settings_manager.save_settings()
        
        print("✅ Settings file is writable and readable")
        return True
        
    except Exception as e:
        print(f"❌ Settings file access error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 **CREDENTIAL MANAGEMENT TEST SUITE**")
    print("Testing the new save/load functionality for GitHub and OpenRouter credentials")
    print()
    
    # Run tests
    test1_passed = test_credential_persistence()
    test2_passed = test_settings_file_location()
    
    print(f"\n📊 **TEST RESULTS:**")
    print(f"   • Credential Persistence: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • Settings File Access: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 **ALL TESTS PASSED!**")
        print("The credential management system is working correctly.")
        print("Users can now save their GitHub tokens and OpenRouter API keys!")
    else:
        print(f"\n⚠️  **SOME TESTS FAILED**")
        print("Please check the error messages above.")