"""
RepoReadme - Configuration Management

Handles application configuration, user settings, and template customization
for the RepoReadme automatic README generator.
"""

from .settings import SettingsManager, AppSettings
from .github_auth import GitHubAuthManager

__all__ = ['SettingsManager', 'AppSettings', 'GitHubAuthManager']