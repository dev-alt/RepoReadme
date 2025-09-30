#!/usr/bin/env python3
"""
Test to verify the unknown setting keys are resolved.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def test_settings_keys():
    """Test that cv_style and linkedin_tone are now recognized."""
    print("🔧 Testing Settings Keys Fix")
    print("=" * 40)
    
    settings_manager = SettingsManager()
    
    # Test the previously unknown keys
    print("📝 Testing cv_style...")
    result1 = settings_manager.set_setting('cv_style', 'technical')
    print(f"   Result: {'✅ SUCCESS' if result1 else '❌ FAILED'}")
    
    print("📝 Testing linkedin_tone...")
    result2 = settings_manager.set_setting('linkedin_tone', 'enthusiastic')
    print(f"   Result: {'✅ SUCCESS' if result2 else '❌ FAILED'}")
    
    # Test reading them back
    print("\n📖 Reading values back...")
    cv_style = settings_manager.get_setting('cv_style', 'NOT_FOUND')
    linkedin_tone = settings_manager.get_setting('linkedin_tone', 'NOT_FOUND')
    
    print(f"   cv_style: '{cv_style}'")
    print(f"   linkedin_tone: '{linkedin_tone}'")
    
    # Reset to defaults
    print("\n🔄 Resetting to defaults...")
    settings_manager.set_setting('cv_style', 'modern')
    settings_manager.set_setting('linkedin_tone', 'professional')
    
    success = result1 and result2 and cv_style != 'NOT_FOUND' and linkedin_tone != 'NOT_FOUND'
    
    if success:
        print("\n✅ All setting keys now work correctly!")
        print("No more 'Unknown setting key' errors should appear.")
    else:
        print("\n❌ There are still issues with the setting keys.")
    
    return success

if __name__ == "__main__":
    test_settings_keys()