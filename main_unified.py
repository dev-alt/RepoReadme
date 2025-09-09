#!/usr/bin/env python3
"""
Unified RepoReadme Application

Main entry point for the unified professional developer suite.
Integrates GitHub analysis, README generation, CV creation, and LinkedIn optimization.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

try:
    from src.unified_gui import UnifiedRepoReadmeGUI
    from src.utils.logger import get_logger
except ImportError:
    from unified_gui import UnifiedRepoReadmeGUI
    from utils.logger import get_logger


def main():
    """Main entry point."""
    logger = get_logger()
    
    try:
        logger.info("Starting Unified RepoReadme Professional Suite")
        
        # Initialize and run the unified GUI
        app = UnifiedRepoReadmeGUI()
        app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("Application closed")


if __name__ == "__main__":
    main()