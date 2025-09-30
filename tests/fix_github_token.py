#!/usr/bin/env python3
"""
Script to clean up the corrupted GitHub token with newlines.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
except ImportError:
    from config.settings import SettingsManager

def fix_github_token():
    """Fix the GitHub token by removing whitespace."""
    print("🔧 Fixing GitHub Token")
    print("=" * 30)
    
    settings_manager = SettingsManager()
    
    # Get current token
    current_token = settings_manager.get_setting('github_token', '')
    print(f"Current token length: {len(current_token)}")
    print(f"Token ends with newline: {current_token.endswith('\\n')}")
    print(f"Token repr: {repr(current_token[:20])}...")
    
    # Clean the token
    clean_token = current_token.strip()
    print(f"Cleaned token length: {len(clean_token)}")
    print(f"Clean token repr: {repr(clean_token[:20])}...")
    
    if current_token != clean_token:
        print("🔧 Token needs cleaning - saving cleaned version...")
        result = settings_manager.set_setting('github_token', clean_token)
        print(f"Save result: {'✅ SUCCESS' if result else '❌ FAILED'}")
        
        # Verify the fix
        verify_token = settings_manager.get_setting('github_token', '')
        print(f"Verification - Token ends with newline: {verify_token.endswith('\\n')}")
        
        if not verify_token.endswith('\\n'):
            print("✅ Token successfully cleaned!")
            return True
        else:
            print("❌ Token still has issues")
            return False
    else:
        print("✅ Token is already clean")
        return True

if __name__ == "__main__":
    success = fix_github_token()
    
    if success:
        print("\\n🎉 GitHub token is now clean and should work properly!")
    else:
        print("\\n❌ Failed to clean the token")