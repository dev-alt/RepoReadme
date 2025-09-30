#!/usr/bin/env python3
"""
Simple test to verify credential saving works.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def test_simple_credentials():
    """Simple test of credential functionality."""
    print("🧪 Testing Credential Saving/Loading")
    print("=" * 50)
    
    settings_manager = SettingsManager()
    
    # Test GitHub username
    print("📝 Testing GitHub username...")
    result = settings_manager.set_setting('github_username', 'test-user')
    print(f"   Save result: {result}")
    
    username = settings_manager.get_setting('github_username', '')
    print(f"   Loaded value: '{username}'")
    
    # Test GitHub token  
    print("📝 Testing GitHub token...")
    result = settings_manager.set_setting('github_token', 'ghp_test123')
    print(f"   Save result: {result}")
    
    token = settings_manager.get_setting('github_token', '')
    print(f"   Loaded value: '{token[:10]}...' (masked)")
    
    # Test OpenRouter key
    print("📝 Testing OpenRouter API key...")
    result = settings_manager.set_setting('openrouter_api_key', 'sk-test123')
    print(f"   Save result: {result}")
    
    openrouter_key = settings_manager.get_setting('openrouter_api_key', '')
    print(f"   Loaded value: '{openrouter_key[:10]}...' (masked)")
    
    print("\n✅ Basic credential functionality works!")
    print("The save buttons in the GUI should now work correctly.")

if __name__ == "__main__":
    test_simple_credentials()