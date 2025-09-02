"""
RepoReadme - Automatic README Generator

A comprehensive tool for analyzing repositories and generating professional
README files automatically.

Key Components:
- analyzers: Repository analysis and technology detection
- generators: README generation with multiple templates  
- templates: Customizable README templates and formats
- utils: Utility functions and shared components
- config: Configuration management and settings

Architecture:
Based on proven GitGuard patterns with modular design for extensibility
and maintainability.

Features:
- Multi-platform repository support (GitHub, GitLab, local)
- Intelligent project structure analysis
- Technology stack detection and documentation
- Multiple README formats and templates
- Interactive GUI for customization
- Batch processing capabilities

Author: RepoReadme Development Team
License: MIT
"""

__version__ = "1.0.0"
__author__ = "RepoReadme Development Team"
__license__ = "MIT"

# Core modules
from . import analyzers
from . import generators  
from . import templates
from . import utils
from . import config

__all__ = [
    "analyzers",
    "generators", 
    "templates",
    "utils",
    "config"
]