#!/usr/bin/env python3
"""
Debug script to test GitHub username validation and API calls.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.settings import SettingsManager
    from src.github_data_manager import GitHubDataManager
except ImportError:
    from config.settings import SettingsManager
    from github_data_manager import GitHubDataManager

def test_github_username():
    """Test what username is stored and if it's valid."""
    print("🐙 GitHub Username Debug Test")
    print("=" * 40)
    
    # Check stored username
    settings_manager = SettingsManager()
    stored_username = settings_manager.get_setting('github_username', '')
    stored_token = settings_manager.get_setting('github_token', '')
    
    print(f"📝 Stored username: '{stored_username}'")
    print(f"📝 Stored token: {'***' if stored_token else 'None'}")
    
    if not stored_username:
        print("❌ No username stored - this could be the issue!")
        return False
    
    if not stored_username.strip():
        print("❌ Username is empty/whitespace - this could be the issue!")
        return False
    
    # Test username validity (basic checks)
    username = stored_username.strip()
    print(f"📝 Cleaned username: '{username}'")
    
    # Basic username validation
    if len(username) == 0:
        print("❌ Username is empty after cleaning")
        return False
    
    if ' ' in username:
        print("❌ Username contains spaces (invalid)")
        return False
    
    if not username.replace('-', '').replace('_', '').isalnum():
        print("❌ Username contains invalid characters")
        return False
    
    print("✅ Username appears valid")
    
    # Test GitHub API call
    print(f"\n🌐 Testing GitHub API call...")
    try:
        github_manager = GitHubDataManager()
        
        # Set token if available
        if stored_token:
            github_manager.set_github_token(stored_token)
            print("✅ Token configured")
        else:
            github_manager.set_username_only(username)
            print("ℹ️  Using public access (no token)")
        
        # Try to get user info
        print(f"📡 Calling GitHub API for user '{username}'...")
        
        # This will help us see exactly what's happening
        from github import Github
        
        if stored_token:
            g = Github(stored_token)
        else:
            g = Github()
        
        user = g.get_user(username)
        print(f"✅ API call successful!")
        print(f"   • User login: {user.login}")
        print(f"   • User name: {user.name}")
        print(f"   • Public repos: {user.public_repos}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub API call failed: {e}")
        
        if "404" in str(e):
            print(f"💡 Suggestion: User '{username}' may not exist on GitHub")
            print(f"   Check: https://github.com/{username}")
        
        return False

if __name__ == "__main__":
    success = test_github_username()
    
    if not success:
        print(f"\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Verify the GitHub username is correct")
        print("2. Check that the user exists: https://github.com/USERNAME")
        print("3. Try with a different username")
        print("4. Check your internet connection")
    else:
        print(f"\n✅ GitHub username and API access are working correctly!")