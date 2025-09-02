#!/usr/bin/env python3
"""
RepoReadme - Automatic README Generator

This application analyzes your repositories and generates comprehensive, 
professional README files automatically. Built on proven GitGuard architecture.

Features:
- Multi-platform repository analysis (GitHub, GitLab, local)
- Intelligent project structure detection
- Multiple README templates and formats
- Technology stack identification
- Documentation generation with examples
- Interactive GUI for customization

Usage:
    python main.py

Requirements:
    - Python 3.10+
    - All dependencies from requirements.txt installed
    - GitHub/GitLab credentials (optional for private repos)

Author: RepoReadme Development Team
License: MIT
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (usually comes with Python)")
    
    try:
        from github import Github
    except ImportError:
        missing_deps.append("PyGithub")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import yaml
    except ImportError:
        missing_deps.append("PyYAML")
    
    try:
        import markdown
    except ImportError:
        missing_deps.append("markdown")
    
    try:
        import git
    except ImportError:
        missing_deps.append("GitPython")
    
    if missing_deps:
        print("ERROR: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install dependencies with:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main entry point for RepoReadme application."""
    print("RepoReadme - Automatic README Generator v1.0.0")
    print("=" * 48)
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ All dependencies found")
    print("🚀 Starting RepoReadme GUI...")
    print()
    
    try:
        # Import and start GUI
        from gui import RepoReadmeGUI
        
        app = RepoReadmeGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ Failed to import RepoReadme modules: {e}")
        print("Make sure all source files are present in the src/ directory")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Please check your Python environment and dependencies")
        sys.exit(1)


if __name__ == "__main__":
    main()