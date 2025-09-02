#!/usr/bin/env python3
"""
GitHub Authentication Manager

Handles GitHub API authentication including personal access tokens,
OAuth flows, and credential management for RepoReadme.
"""

import os
import json
from pathlib import Path
from typing import Optional
import keyring

try:
    from github import Github
except ImportError:
    Github = None


class GitHubAuthManager:
    """Manages GitHub authentication and API access."""
    
    def __init__(self, config_dir: Path = None):
        """Initialize GitHub authentication manager."""
        if config_dir is None:
            config_dir = Path.home() / '.reporeadme' / 'config'
        
        self.config_dir = config_dir
        self.config_file = config_dir / 'github_config.json'
        self.github_client: Optional[Github] = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config
        self.load_config()
    
    def load_config(self):
        """Load GitHub configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
        else:
            self.config = {}
    
    def save_config(self):
        """Save GitHub configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            raise RuntimeError(f"Failed to save GitHub config: {e}")
    
    def get_token(self) -> Optional[str]:
        """Get GitHub token from various sources."""
        # Check environment variable first
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token
        
        # Check keyring (secure storage)
        try:
            token = keyring.get_password("reporeadme", "github_token")
            if token:
                return token
        except Exception:
            pass
        
        # Check config file (less secure)
        return self.config.get('github_token')
    
    def set_token(self, token: str, store_in_keyring: bool = True):
        """Set GitHub token and optionally store securely."""
        if store_in_keyring:
            try:
                keyring.set_password("reporeadme", "github_token", token)
                # Remove from config file if stored in keyring
                if 'github_token' in self.config:
                    del self.config['github_token']
                    self.save_config()
                return True
            except Exception:
                # Fallback to config file
                pass
        
        # Store in config file
        self.config['github_token'] = token
        self.save_config()
        return True
    
    def remove_token(self):
        """Remove stored GitHub token."""
        # Remove from keyring
        try:
            keyring.delete_password("reporeadme", "github_token")
        except Exception:
            pass
        
        # Remove from config
        if 'github_token' in self.config:
            del self.config['github_token']
            self.save_config()
    
    def create_client(self, token: str = None) -> Optional[Github]:
        """Create GitHub client with authentication."""
        if Github is None:
            return None
        
        try:
            if token is None:
                token = self.get_token()
            
            if token:
                self.github_client = Github(token)
                # Test the token
                user = self.github_client.get_user()
                return self.github_client
            else:
                # Create public-only client
                self.github_client = Github()
                return self.github_client
                
        except Exception as e:
            raise RuntimeError(f"Failed to create GitHub client: {e}")
    
    def get_authenticated_client(self) -> Optional[Github]:
        """Get authenticated GitHub client."""
        if self.github_client is None:
            self.github_client = self.create_client()
        
        return self.github_client
    
    def test_authentication(self) -> dict:
        """Test GitHub authentication and return status."""
        try:
            client = self.get_authenticated_client()
            if client is None:
                return {
                    'authenticated': False,
                    'error': 'PyGithub not available'
                }
            
            # Test with authenticated user if token exists
            token = self.get_token()
            if token:
                try:
                    user = client.get_user()
                    return {
                        'authenticated': True,
                        'username': user.login,
                        'rate_limit': client.get_rate_limit().core.remaining
                    }
                except Exception as e:
                    return {
                        'authenticated': False,
                        'error': f'Invalid token: {e}'
                    }
            else:
                # Public access only
                try:
                    rate_limit = client.get_rate_limit()
                    return {
                        'authenticated': False,
                        'public_access': True,
                        'rate_limit': rate_limit.core.remaining
                    }
                except Exception as e:
                    return {
                        'authenticated': False,
                        'error': f'GitHub API error: {e}'
                    }
                    
        except Exception as e:
            return {
                'authenticated': False,
                'error': str(e)
            }
    
    def get_rate_limit_info(self) -> dict:
        """Get current rate limit information."""
        try:
            client = self.get_authenticated_client()
            if client is None:
                return {'error': 'No GitHub client available'}
            
            rate_limit = client.get_rate_limit()
            return {
                'core': {
                    'limit': rate_limit.core.limit,
                    'remaining': rate_limit.core.remaining,
                    'reset': rate_limit.core.reset
                },
                'search': {
                    'limit': rate_limit.search.limit,
                    'remaining': rate_limit.search.remaining,
                    'reset': rate_limit.search.reset
                }
            }
        except Exception as e:
            return {'error': str(e)}