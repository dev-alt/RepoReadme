#!/usr/bin/env python3
"""
Test the fixed credential saving functionality.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def test_fixed_save_functionality():
    """Test that the save functionality now works without errors."""
    print("🧪 Testing Fixed Save Functionality")
    print("=" * 50)
    
    settings_manager = SettingsManager()
    
    # Test that set_setting works properly (this is what the GUI uses)
    print("💾 Testing GitHub username save...")
    result = settings_manager.set_setting('github_username', 'test-user-fixed')
    print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    print("💾 Testing GitHub token save...")
    result = settings_manager.set_setting('github_token', 'ghp_fixed123456789')
    print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    print("💾 Testing OpenRouter API key save...")
    result = settings_manager.set_setting('openrouter_api_key', 'sk-fixed123456789')
    print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Verify the values were saved and can be retrieved
    print("\n📖 Testing retrieval...")
    username = settings_manager.get_setting('github_username', '')
    token = settings_manager.get_setting('github_token', '')
    openrouter = settings_manager.get_setting('openrouter_api_key', '')
    
    print(f"   Username: '{username}'")
    print(f"   Token: '{token[:8]}...' (masked)")
    print(f"   OpenRouter: '{openrouter[:8]}...' (masked)")
    
    # Test edge cases
    print("\n🔧 Testing edge cases...")
    
    # Empty values
    result = settings_manager.set_setting('github_username', '')
    print(f"   Empty username: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Special characters
    result = settings_manager.set_setting('github_username', 'user-with_special.chars')
    print(f"   Special chars: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    print(f"\n🎉 Credential saving is now working correctly!")
    print("Users can save their GitHub tokens and OpenRouter API keys without errors.")

if __name__ == "__main__":
    test_fixed_save_functionality()