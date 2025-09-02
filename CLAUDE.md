# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RepoReadme is an automatic README generator built in Python 3.10+ that analyzes repositories and generates professional documentation. It features a modular and extensible architecture with clean separation of concerns.

## Development Commands

### Running the Application
```bash
# Launch GUI application
python main.py

# Run CLI demo with options
python demo.py <repository_path> --template modern --output README.md
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
```

### Available CLI Templates
- `modern` - Default template with badges and emojis
- `classic` - Simple, traditional format
- `minimalist` - Ultra-clean design
- `developer` - Technical projects with architecture details
- `academic` - Research projects with citations
- `corporate` - Business projects with compliance info

## Architecture Overview

### Core Components
- **`src/analyzers/`** - Repository analysis engine that detects technologies, project structure, and generates metadata
- **`src/templates/`** - README template system with 6 professional templates using Jinja2
- **`src/gui.py`** - Tkinter-based GUI with repository management, template customization, and real-time preview
- **`src/config/`** - Settings management and GitHub authentication
- **`src/utils/logger.py`** - Comprehensive logging system with rotation and structured output

### Entry Points
- **`main.py`** - GUI application launcher with dependency checking
- **`demo.py`** - Command-line interface for automation and testing

### Key Patterns
- **Dataclass Pattern** - Extensive use for configuration and metadata containers (`ProjectMetadata`, `TemplateConfig`)
- **Factory Pattern** - Template generation with different styles
- **Modular Design** - Clear separation between analysis, templating, GUI, and utilities
- **Reusable Components** - File scanning, progress tracking, configuration management, logging framework

## Configuration

### Settings Files
- **`config/settings.json`** - Application settings and user preferences
- **`src/config/settings.py`** - Settings management logic
- **`src/config/github_auth.py`** - GitHub API authentication

### Directory Structure
- **`cache/`** - Repository analysis caching for performance
- **`logs/`** - Application logs with rotation
- **`output/`** - Generated README files
- **`claude/`** - Claude-related files

## Key Dependencies

### Core Libraries
- **PyGithub** (≥1.55.0) - GitHub API integration
- **GitPython** (≥3.1.0) - Git repository analysis
- **Jinja2** (≥3.0.0) - Template engine
- **PyYAML** (≥6.0.0), **toml** (≥0.10.0) - Configuration file parsing
- **tkinter** - Built-in GUI framework

### Analysis Features
The repository analyzer (`src/analyzers/repository_analyzer.py`) provides:
- Technology stack detection
- Project structure analysis
- Dependency parsing from package files
- License and documentation detection
- Code metrics and statistics generation

## Important Notes

- **No Testing Framework**: The project currently lacks automated tests
- **Python 3.10+ Required**: Uses modern Python features
- **Modern Architecture**: Uses established Python patterns and best practices
- **Multi-Platform Support**: GitHub, GitLab, and local repositories
- **Batch Processing**: Can analyze multiple repositories simultaneously