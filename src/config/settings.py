#!/usr/bin/env python3
"""
RepoReadme - Settings Management

Manages application settings, user preferences, and configuration
for the RepoReadme automatic README generator.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class AppSettings:
    """Application settings data class."""
    
    # GUI settings
    window_geometry: str = "1400x900"
    window_maximized: bool = False
    theme: str = "default"
    font_size: int = 10
    
    # Template preferences
    default_template: str = "modern"
    include_badges: bool = True
    include_toc: bool = True
    include_screenshots: bool = True
    include_api_docs: bool = True
    include_contributing: bool = True
    include_license_section: bool = True
    include_acknowledgments: bool = True
    emoji_style: str = "unicode"  # unicode, github, none
    badge_style: str = "flat"     # flat, flat-square, plastic
    
    # Analysis settings
    auto_analyze: bool = True
    cache_analysis: bool = True
    max_cache_age_days: int = 7
    exclude_patterns: list = None
    include_hidden_files: bool = False
    
    # Export settings
    default_export_format: str = "markdown"
    auto_timestamp_files: bool = True
    create_backup: bool = True
    export_directory: str = ""
    
    # GitHub settings
    remember_github_token: bool = False
    
    # OpenRouter AI settings
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-3.5-turbo"
    openrouter_enabled: bool = False
    openrouter_enhance_bios: bool = True
    openrouter_max_tokens: int = 1000
    openrouter_temperature: float = 0.7
    github_username: str = ""
    github_token: str = ""  # This should be encrypted in production
    
    # CV and LinkedIn settings
    cv_style: str = "modern"
    linkedin_tone: str = "professional"
    
    # Logging settings
    log_level: str = "INFO"
    keep_logs_days: int = 30
    log_to_file: bool = True
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "node_modules", ".git", "__pycache__", ".venv", 
                "venv", "build", "dist", ".cache", "coverage"
            ]


class SettingsManager:
    """
    Manages application settings with persistence and validation.
    
    Handles loading, saving, and validating user preferences and
    configuration settings for the RepoReadme application.
    """
    
    def __init__(self):
        """Initialize settings manager."""
        self.settings_dir = Path.home() / ".reporeadme" / "config"
        self.settings_file = self.settings_dir / "settings.json"
        self.backup_file = self.settings_dir / "settings_backup.json"
        
        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Load settings
        self.settings = self.load_settings()
    
    def load_settings(self) -> AppSettings:
        """
        Load settings from file.
        
        Returns:
            AppSettings instance with loaded or default values
        """
        if not self.settings_file.exists():
            # Create default settings
            settings = AppSettings()
            self.save_settings(settings)
            return settings
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to AppSettings
            settings = AppSettings(**data)
            
            # Validate and fix any invalid values
            settings = self._validate_settings(settings)
            
            return settings
        
        except Exception as e:
            print(f"Failed to load settings: {e}")
            
            # Try to load backup
            if self.backup_file.exists():
                try:
                    with open(self.backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return AppSettings(**data)
                except Exception:
                    pass
            
            # Return default settings if all else fails
            return AppSettings()
    
    def save_settings(self, settings: AppSettings) -> bool:
        """
        Save settings to file.
        
        Args:
            settings: AppSettings instance to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup of existing settings
            if self.settings_file.exists():
                # Remove existing backup if it exists
                if self.backup_file.exists():
                    self.backup_file.unlink()
                # Create new backup
                self.settings_file.rename(self.backup_file)
            
            # Save new settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(settings), f, indent=2, ensure_ascii=False)
            
            self.settings = settings
            return True
        
        except Exception as e:
            print(f"Failed to save settings: {e}")
            
            # Restore backup if save failed
            if self.backup_file.exists():
                try:
                    self.backup_file.rename(self.settings_file)
                except Exception:
                    pass
            
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value.
        
        Args:
            key: Setting key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        try:
            if '.' in key:
                # Handle nested keys
                keys = key.split('.')
                value = asdict(self.settings)
                for k in keys:
                    value = value[k]
                return value
            else:
                return getattr(self.settings, key, default)
        
        except (AttributeError, KeyError):
            return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a specific setting value.
        
        Args:
            key: Setting key
            value: New value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                return self.save_settings(self.settings)
            else:
                print(f"Unknown setting key: {key}")
                return False
        
        except Exception as e:
            print(f"Failed to set setting {key}: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to default values.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            default_settings = AppSettings()
            return self.save_settings(default_settings)
        
        except Exception as e:
            print(f"Failed to reset settings: {e}")
            return False
    
    def export_settings(self, export_path: str) -> bool:
        """
        Export settings to a file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)
            return True
        
        except Exception as e:
            print(f"Failed to export settings: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            settings = AppSettings(**data)
            settings = self._validate_settings(settings)
            
            return self.save_settings(settings)
        
        except Exception as e:
            print(f"Failed to import settings: {e}")
            return False
    
    def _validate_settings(self, settings: AppSettings) -> AppSettings:
        """
        Validate and fix settings values.
        
        Args:
            settings: Settings to validate
            
        Returns:
            Validated settings
        """
        # Validate window geometry
        if not settings.window_geometry or 'x' not in settings.window_geometry:
            settings.window_geometry = "1400x900"
        
        # Validate template name
        valid_templates = ['modern', 'classic', 'minimalist', 'developer', 'academic', 'corporate']
        if settings.default_template not in valid_templates:
            settings.default_template = "modern"
        
        # Validate emoji style
        valid_emoji_styles = ['unicode', 'github', 'none']
        if settings.emoji_style not in valid_emoji_styles:
            settings.emoji_style = "unicode"
        
        # Validate badge style
        valid_badge_styles = ['flat', 'flat-square', 'plastic']
        if settings.badge_style not in valid_badge_styles:
            settings.badge_style = "flat"
        
        # Validate export format
        valid_formats = ['markdown', 'html', 'pdf']
        if settings.default_export_format not in valid_formats:
            settings.default_export_format = "markdown"
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if settings.log_level not in valid_log_levels:
            settings.log_level = "INFO"
        
        # Validate numeric values
        if settings.font_size < 8 or settings.font_size > 24:
            settings.font_size = 10
        
        if settings.max_cache_age_days < 1:
            settings.max_cache_age_days = 7
        
        if settings.keep_logs_days < 1:
            settings.keep_logs_days = 30
        
        # Ensure exclude patterns is a list
        if not isinstance(settings.exclude_patterns, list):
            settings.exclude_patterns = [
                "node_modules", ".git", "__pycache__", ".venv", 
                "venv", "build", "dist", ".cache", "coverage"
            ]
        
        return settings
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current settings.
        
        Returns:
            Dictionary with settings summary
        """
        return {
            "template": self.settings.default_template,
            "emoji_style": self.settings.emoji_style,
            "badge_style": self.settings.badge_style,
            "auto_analyze": self.settings.auto_analyze,
            "cache_enabled": self.settings.cache_analysis,
            "export_format": self.settings.default_export_format,
            "log_level": self.settings.log_level,
            "settings_file": str(self.settings_file),
            "last_modified": self.settings_file.stat().st_mtime if self.settings_file.exists() else None
        }


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None

def get_settings_manager() -> SettingsManager:
    """Get or create the global settings manager instance."""
    global _settings_manager
    
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    
    return _settings_manager

def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value using the global settings manager."""
    return get_settings_manager().get_setting(key, default)

def set_setting(key: str, value: Any) -> bool:
    """Set a setting value using the global settings manager."""
    return get_settings_manager().set_setting(key, value)