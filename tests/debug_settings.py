#!/usr/bin/env python3
"""
Debug script to see what's actually saved in settings.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def debug_settings_persistence():
    """Debug what's actually being saved and loaded."""
    print("🔍 Debugging Settings Persistence")
    print("=" * 50)
    
    settings_manager = SettingsManager()
    
    # Check what's currently in settings
    print("📖 Current settings values:")
    username = settings_manager.get_setting('github_username', 'NOT_FOUND')
    token = settings_manager.get_setting('github_token', 'NOT_FOUND')
    openrouter = settings_manager.get_setting('openrouter_api_key', 'NOT_FOUND')
    
    print(f"   GitHub username: '{username}'")
    print(f"   GitHub token: '{token}'")
    print(f"   OpenRouter key: '{openrouter}'")
    
    # Test saving new values
    print(f"\n💾 Testing saves:")
    
    test_username = "debug-user"
    test_token = "ghp_debug123456789"
    test_openrouter = "sk-debug123456789"
    
    # Save each one
    result1 = settings_manager.set_setting('github_username', test_username)
    print(f"   Username save: {'✅' if result1 else '❌'}")
    
    result2 = settings_manager.set_setting('github_token', test_token)
    print(f"   Token save: {'✅' if result2 else '❌'}")
    
    result3 = settings_manager.set_setting('openrouter_api_key', test_openrouter)
    print(f"   OpenRouter save: {'✅' if result3 else '❌'}")
    
    # Read them back immediately
    print(f"\n📖 Immediate read-back:")
    username_back = settings_manager.get_setting('github_username', 'NOT_FOUND')
    token_back = settings_manager.get_setting('github_token', 'NOT_FOUND')
    openrouter_back = settings_manager.get_setting('openrouter_api_key', 'NOT_FOUND')
    
    print(f"   Username: '{username_back}' {'✅' if username_back == test_username else '❌'}")
    print(f"   Token: '{token_back}' {'✅' if token_back == test_token else '❌'}")
    print(f"   OpenRouter: '{openrouter_back}' {'✅' if openrouter_back == test_openrouter else '❌'}")
    
    # Check the actual settings file content
    print(f"\n📁 Raw settings file content:")
    try:
        settings_file = settings_manager.settings_file
        print(f"   File location: {settings_file}")
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                content = json.load(f)
            
            print(f"   File exists: ✅")
            print(f"   Keys in file: {list(content.keys())}")
            
            # Check specific values
            print(f"   Raw github_username: '{content.get('github_username', 'NOT_IN_FILE')}'")
            print(f"   Raw github_token: '{content.get('github_token', 'NOT_IN_FILE')}'")
            print(f"   Raw openrouter_api_key: '{content.get('openrouter_api_key', 'NOT_IN_FILE')}'")
            
        else:
            print(f"   File exists: ❌")
            
    except Exception as e:
        print(f"   Error reading file: {e}")
    
    # Test with fresh settings manager
    print(f"\n🔄 Testing with fresh SettingsManager:")
    new_settings_manager = SettingsManager()
    
    fresh_username = new_settings_manager.get_setting('github_username', 'NOT_FOUND')
    fresh_token = new_settings_manager.get_setting('github_token', 'NOT_FOUND')
    fresh_openrouter = new_settings_manager.get_setting('openrouter_api_key', 'NOT_FOUND')
    
    print(f"   Fresh username: '{fresh_username}'")
    print(f"   Fresh token: '{fresh_token}'")
    print(f"   Fresh openrouter: '{fresh_openrouter}'")

if __name__ == "__main__":
    debug_settings_persistence()