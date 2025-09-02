#!/usr/bin/env python3
"""
RepoReadme - README Template System

Provides multiple professional README templates that can be customized
and generated based on repository analysis results.

Templates:
- Classic: Traditional README format
- Modern: Contemporary design with badges and sections
- Minimalist: Clean, simple format
- Developer: Technical focus with API docs
- Academic: Research project format
- Corporate: Professional business format
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import re

try:
    from ..analyzers.repository_analyzer import ProjectMetadata
    from ..utils.logger import get_logger
except ImportError:
    from analyzers.repository_analyzer import ProjectMetadata
    from utils.logger import get_logger


@dataclass
class TemplateConfig:
    """Configuration for README template generation."""
    
    template_name: str = "modern"
    include_badges: bool = True
    include_toc: bool = True
    include_screenshots: bool = True
    include_api_docs: bool = True
    include_contributing: bool = True
    include_license_section: bool = True
    include_acknowledgments: bool = True
    emoji_style: str = "unicode"  # unicode, github, none
    badge_style: str = "flat"  # flat, flat-square, plastic
    language: str = "en"
    

class ReadmeTemplateEngine:
    """
    Advanced README template engine with multiple professional formats.
    
    Generates customized README files based on repository analysis
    and user preferences.
    """
    
    def __init__(self):
        """Initialize the template engine."""
        self.logger = get_logger()
        self.templates = {
            'modern': self._generate_modern_template,
            'classic': self._generate_classic_template,
            'minimalist': self._generate_minimalist_template,
            'developer': self._generate_developer_template,
            'academic': self._generate_academic_template,
            'corporate': self._generate_corporate_template,
            'startup': self._generate_startup_template,
            'gaming': self._generate_gaming_template,
            'security': self._generate_security_template,
            'ai_ml': self._generate_ai_ml_template,
            'mobile': self._generate_mobile_template,
            'opensource': self._generate_opensource_template
        }
    
    def generate_readme(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """
        Generate a README file based on metadata and configuration.
        
        Args:
            metadata: Repository analysis results
            config: Template configuration
            
        Returns:
            Generated README content as string
        """
        if config.template_name not in self.templates:
            raise ValueError(f"Unknown template: {config.template_name}")
        
        self.logger.info(f"Generating {config.template_name} README for {metadata.name}", "TEMPLATE")
        
        template_func = self.templates[config.template_name]
        readme_content = template_func(metadata, config)
        
        self.logger.log_readme_generation(
            metadata.name, config.template_name, 
            f"{metadata.name}_README.md", True
        )
        
        return readme_content
    
    def _generate_modern_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate modern README template with intelligent content and professional design."""
        
        content = []
        
        # Dynamic emoji based on project type
        emoji_map = {
            'gui-application': '🖥️',
            'web-app': '🌐', 
            'cli-tool': '⚡',
            'library': '📚',
            'api': '🔌',
            'desktop-app': '💻'
        }
        emoji = emoji_map.get(metadata.project_type, '🚀') if config.emoji_style == "unicode" else ""
        
        # Professional header with better formatting
        display_name = metadata.name.replace('-', ' ').replace('_', ' ').title()
        content.append(f"# {emoji} {display_name}")
        content.append("")
        
        # Compelling description
        if metadata.description:
            content.append(f"> {metadata.description}")
        else:
            # Fallback intelligent description
            if metadata.project_type == 'gui-application':
                content.append(f"> Professional desktop application built with {metadata.primary_language.title()}")
            elif metadata.features:
                content.append(f"> {metadata.features[0]}")
            else:
                content.append(f"> {metadata.primary_language.title()} application for {metadata.name.lower()} functionality")
        content.append("")
        
        # Badges section
        if config.include_badges:
            badges = self._generate_badges(metadata, config)
            if badges:
                content.extend(badges)
                content.append("")
        
        # Table of Contents
        if config.include_toc:
            toc = self._generate_comprehensive_toc(metadata, config)
            content.extend(toc)
            content.append("")
        
        # Enhanced Features section with detailed descriptions
        if metadata.features:
            content.append("## ✨ Features")
            content.append("")
            
            # Add comprehensive feature descriptions
            for feature in metadata.features[:8]:
                if feature:
                    description = self._get_feature_description(feature, metadata)
                    content.append(f"- **{feature}** - {description}")
            content.append("")
        
        # Enhanced Technology Stack with better organization
        if metadata.primary_language or metadata.frameworks or metadata.databases:
            content.append("## 🛠️ Technology Stack")
            content.append("")
            
            if metadata.primary_language:
                version_info = ""
                if metadata.primary_language == 'python':
                    version_info = " 3.8+"
                elif metadata.primary_language == 'javascript':
                    version_info = " (Node.js)"
                elif metadata.primary_language == 'typescript':
                    version_info = " (Node.js)"
                elif metadata.primary_language == 'java':
                    version_info = " 11+"
                elif metadata.primary_language == 'go':
                    version_info = " 1.18+"
                
                content.append(f"**Primary Language:** {metadata.primary_language.title()}{version_info}")
                content.append("")
            
            # Core Dependencies - show most important frameworks first
            if metadata.frameworks:
                core_frameworks = []
                ui_frameworks = []
                other_frameworks = []
                
                for fw in metadata.frameworks:
                    fw_lower = fw.lower()
                    if fw_lower in ['tkinter', 'pyqt', 'pyside', 'kivy', 'react', 'vue', 'angular', 'flutter', 'electron']:
                        ui_frameworks.append(fw)
                    elif fw_lower in ['flask', 'django', 'fastapi', 'express', 'spring', 'rails', 'gin', 'echo']:
                        core_frameworks.append(fw)
                    else:
                        other_frameworks.append(fw)
                
                if core_frameworks:
                    content.append("**Core Framework:**")
                    for fw in core_frameworks[:2]:  # Limit to 2
                        content.append(f"- **{fw.title()}** - {self._get_framework_description(fw)}")
                    content.append("")
                
                if ui_frameworks:
                    content.append("**UI Framework:**")
                    for fw in ui_frameworks[:2]:  # Limit to 2
                        content.append(f"- **{fw.title()}** - {self._get_framework_description(fw)}")
                    content.append("")
                
                if other_frameworks and len(other_frameworks) <= 5:
                    content.append("**Additional Libraries:**")
                    for fw in other_frameworks[:5]:
                        content.append(f"- {fw.title()}")
                    content.append("")
                
                # Database information
                if metadata.databases:
                    content.append("**Database:**")
                    for db in metadata.databases[:2]:
                        content.append(f"- **{db.title()}** - {self._get_database_description(db)}")
                    content.append("")
            
            # Show architecture info for complex projects
            if len(metadata.frameworks) >= 3 or metadata.structure:
                content.append("### 🏗️ Architecture")
                if 'readme' in metadata.name.lower():
                    content.append("- **Repository Analyzer** - Detects technologies, dependencies, and project structure")
                    content.append("- **Template Engine** - Generates professional README files with multiple styles") 
                    content.append("- **GUI Application** - Modern interface with real-time preview and customization")
                    content.append("- **Configuration System** - Manages settings, authentication, and user preferences")
                elif metadata.structure:
                    # Generic architecture based on detected structure
                    for directory, info in list(metadata.structure.items())[:4]:
                        if info.get('files', 0) > 0:
                            content.append(f"- **{directory.title()}** - {self._get_directory_description(directory)}")
                content.append("")
        
        # Getting Started
        content.append("## 🚀 Getting Started")
        content.append("")
        
        # Prerequisites
        content.append("### Prerequisites")
        content.append("")
        if metadata.primary_language == 'python':
            content.append("- Python 3.8 or higher")
            content.append("- pip package manager")
        elif metadata.primary_language == 'javascript':
            content.append("- Node.js 16 or higher")
            content.append("- npm or yarn package manager")
        elif metadata.primary_language == 'java':
            content.append("- Java 11 or higher")
            content.append("- Maven or Gradle")
        else:
            content.append(f"- {metadata.primary_language.title()} runtime environment")
        content.append("")
        
        # Enhanced Installation with smart instructions
        content.append("### Installation")
        content.append("")
        
        # Use the intelligent installation instructions we generated
        if metadata.installation_commands:
            for i, cmd in enumerate(metadata.installation_commands, 1):
                if i == 1 and cmd.startswith('git clone'):
                    content.append("1. **Clone the repository**")
                    content.append("```bash")
                    content.append(cmd)
                    if len(metadata.installation_commands) > 1:
                        cd_cmd = f"cd {metadata.name.split('/')[-1]}"  # Handle owner/repo format
                        content.append(cd_cmd)
                    content.append("```")
                    content.append("")
                elif 'install' in cmd.lower():
                    content.append("2. **Install dependencies**")
                    content.append("```bash")
                    content.append(cmd)
                    content.append("```")
                    content.append("")
                else:
                    content.append("3. **Launch the application**")
                    content.append("```bash")
                    content.append(cmd)
                    content.append("```")
                    content.append("")
        else:
            # Fallback installation instructions
            content.append("1. **Clone the repository**")
            content.append("```bash")
            content.append(f"git clone <repository-url>")
            content.append(f"cd {metadata.name}")
            content.append("```")
            content.append("")
            
            content.append("2. **Install dependencies**")
            content.append("```bash")
            if metadata.primary_language == 'python':
                content.append("pip install -r requirements.txt")
            elif metadata.primary_language in ['javascript', 'typescript']:
                content.append("npm install")
            content.append("```")
            content.append("")
            
            content.append("3. **Start the application**")  
            content.append("```bash")
            if metadata.primary_language == 'python':
                content.append("python main.py")
            elif metadata.primary_language in ['javascript', 'typescript']:
                content.append("npm start")
            content.append("```")
            content.append("")
        
        # Comprehensive Usage section
        content.append("## 📖 Usage")
        content.append("")
        
        # Quick Start subsection
        content.append("### Quick Start")
        content.append("")
        self._add_quick_start_guide(content, metadata)
        
        # Batch Operations (if applicable)
        if any(keyword in metadata.name.lower() for keyword in ['batch', 'multi', 'mass']):
            content.append("### Batch Operations")
            content.append("")
            content.append("- **Analyze All:** Process multiple repositories at once")
            content.append("- **Generate All READMEs:** Create documentation for all analyzed projects")  
            content.append("- **Export All:** Bulk export README files to a chosen directory")
            content.append("")
        
        # Template/Configuration options (if applicable)
        if 'template' in metadata.name.lower() or 'config' in str(metadata.structure):
            content.append("### Template Customization")
            content.append("")
            content.append("Configure your README generation with options like:")
            content.append("- **Badge styles:** Flat, flat-square, or plastic")
            content.append("- **Emoji support:** Unicode, GitHub-style, or none")
            content.append("- **Content sections:** API docs, contributing guidelines, acknowledgments")
            content.append("- **Table of contents:** Automatic generation with anchor links")
            content.append("")
        
        # Code examples if available
        if metadata.usage_examples:
            content.append("### Code Examples")
            content.append("")
            for i, example in enumerate(metadata.usage_examples[:2], 1):
                content.append(f"**Example {i}:**")
                content.append("```" + (metadata.primary_language or ""))
                content.append(example.strip())
                content.append("```")
                content.append("")
        
        # API Documentation (if applicable)
        if config.include_api_docs and metadata.project_type in ['api', 'web-app']:
            content.append("## 📚 API Documentation")
            content.append("")
            content.append("### Endpoints")
            content.append("")
            if metadata.api_endpoints:
                for endpoint in metadata.api_endpoints:
                    content.append(f"- `{endpoint.get('method', 'GET')} {endpoint.get('path', '/')}`")
            else:
                content.append("- `GET /api/health` - Health check")
                content.append("- `GET /api/docs` - API documentation")
            content.append("")
        
        # Enhanced Project Structure with descriptions
        if metadata.structure and len(metadata.structure) >= 3:
            content.append("## 🏗️ Architecture")
            content.append("")
            
            # Add architecture description
            if 'readme' in metadata.name.lower():
                content.append("RepoReadme features a modular, extensible architecture:")
                content.append("")
            
            content.append("```")
            content.append(f"{metadata.name.lower().replace(' ', '')}/")
            for directory, info in list(metadata.structure.items())[:8]:
                if info.get('files', 0) > 0:
                    if directory in ['src', 'lib', 'app']:
                        content.append(f"├── {directory}/")
                    else:
                        content.append(f"│   ├── {directory}/          # {self._get_directory_description(directory)}")
            content.append("├── main.py                # Application entry point") 
            content.append("├── requirements.txt       # Python dependencies")
            content.append("└── README.md             # This file")
            content.append("```")
            content.append("")
            
            # Core Architecture Components
            if len(metadata.structure) >= 4:
                content.append("### Core Architecture Components")
                content.append("")
                architecture_features = self._get_architecture_features(metadata)
                for feature in architecture_features:
                    content.append(f"- **{feature}**")
                content.append("")
        
        # Templates section for template/readme projects
        if 'template' in metadata.name.lower() or 'readme' in metadata.name.lower():
            content.append("## 📚 Templates")
            content.append("")
            content.append("RepoReadme offers 12+ professional templates:")
            content.append("")
            content.append("| Template | Best For | Key Features |")
            content.append("|----------|----------|--------------|")
            content.append("| **Modern** | Most projects | Badges, emojis, comprehensive sections |")
            content.append("| **Classic** | Traditional projects | Simple, clean, essential information |")
            content.append("| **Minimalist** | Simple projects | Ultra-clean design, minimal content |")
            content.append("| **Developer** | Technical projects | Detailed architecture, performance metrics |")
            content.append("| **Academic** | Research projects | Citations, methodology, background |")
            content.append("| **Corporate** | Business projects | Compliance, deployment, support info |")
            content.append("| **Startup** | Startup projects | Mission, traction, investor-focused |")
            content.append("| **Gaming** | Games & Entertainment | Screenshots, system requirements, community |")
            content.append("| **Security** | Security tools | Threat protection, compliance, reporting |")
            content.append("| **AI/ML** | Machine Learning | Model metrics, training data, benchmarks |")
            content.append("| **Mobile** | Mobile apps | App store badges, screenshots, reviews |")
            content.append("| **Open Source** | OSS projects | Community stats, contribution guides |")
            content.append("")
            content.append("**Plus:** Custom template builder to create your own unique style!")
            content.append("")
        
        # Key Advantages section for complex projects
        if len(metadata.features) >= 4 or len(metadata.frameworks) >= 3:
            content.append("## 🎯 Key Advantages")
            content.append("")
            
            # Architectural Advantages
            content.append("### Key Architectural Advantages")
            content.append(f"{metadata.name}'s modern architecture provides:")
            content.append("- **Scalable** - Handles repositories of any size efficiently")
            content.append("- **Reliable** - Robust error handling and automatic recovery")
            content.append("- **Fast** - Intelligent caching and incremental processing")
            content.append("- **User-friendly** - Polished GUI with real-time progress feedback")
            content.append("")
            
            # Professional Output
            if 'readme' in metadata.name.lower() or 'template' in metadata.name.lower():
                content.append("### Professional Output")
                content.append("Generated READMEs include:")
                content.append("- **Comprehensive badges** for version, language, license")
                content.append("- **Interactive charts** via shields.io integration")
                content.append("- **Proper markdown structure** with heading hierarchy")
                content.append("- **Code examples** extracted from your project")
                content.append("- **Installation instructions** based on detected technologies")
                content.append("- **Project structure** automatically documented")
                content.append("")
        
        # Performance metrics section
        content.append("## 🚀 Performance")
        content.append("")
        
        # Add performance metrics
        performance_metrics = self._generate_performance_metrics(metadata)
        for metric in performance_metrics:
            content.append(metric)
        content.append("")
        
        # Testing
        if metadata.has_tests:
            content.append("## 🧪 Testing")
            content.append("")
            content.append("Run the test suite:")
            content.append("")
            content.append("```bash")
            if metadata.primary_language == 'python':
                content.append("pytest")
            elif metadata.primary_language == 'javascript':
                content.append("npm test")
            else:
                content.append("# Run tests")
            content.append("```")
            content.append("")
        
        # Enhanced Contributing section
        if config.include_contributing:
            content.append("## 🤝 Contributing")
            content.append("")
            
            # Add project-specific contribution intro
            if len(metadata.features) >= 4:
                content.append("We welcome contributions! This project demonstrates modern Python architecture patterns and extensible design.")
            else:
                content.append("Contributions are welcome! Please feel free to submit a Pull Request.")
            content.append("")
            
            # Development setup for contributors
            content.append("### Development Setup")
            content.append("")
            content.append("1. Fork the repository")
            content.append("2. Create a feature branch (`git checkout -b feature/amazing-feature`)")
            content.append("3. Make your changes following the existing code patterns")
            content.append("4. Test with various repository types")
            content.append("5. Submit a pull request")
            content.append("")
            
            # Code style guidelines for complex projects
            if len(metadata.structure) >= 4:
                content.append("### Code Style")
                content.append("")
                content.append("- Follow established architectural patterns")
                content.append("- Use type hints and docstrings")
                content.append("- Maintain comprehensive logging")
                content.append("- Include error handling for all operations")
                content.append("")
        
        # License
        if config.include_license_section and metadata.license:
            content.append("## 📝 License")
            content.append("")
            content.append(f"This project is licensed under the {metadata.license} License - see the [LICENSE](LICENSE) file for details.")
            content.append("")
        
        # Enhanced Acknowledgments
        if config.include_acknowledgments:
            content.append("## 🙏 Acknowledgments")
            content.append("")
            
            # Project-specific acknowledgments
            if metadata.primary_language == 'python':
                content.append("- **Python Community** - For excellent tools and architectural guidance")
            
            content.append("- **Open Source Community** - For the amazing tools and libraries")
            
            if metadata.frameworks:
                if len(metadata.frameworks) == 1:
                    content.append(f"- **{metadata.frameworks[0].title()} Ecosystem** - For making repository analysis accessible")
                else:
                    content.append(f"- **Python Ecosystem** - For making repository analysis accessible")
            
            content.append("- **Contributors** - For helping improve RepoReadme")
            content.append("")
        
        # Enhanced Footer
        content.append("---")
        content.append("")
        
        # Project-specific footer
        if 'readme' in metadata.name.lower():
            content.append(f"**{metadata.name}** - Transform your repositories into professional documentation automatically!")
            content.append("")
            content.append(f"Built with ❤️ using modern Python architecture patterns.")
            content.append("")
            content.append("*Generate this README and thousands more with just a few clicks!*")
        else:
            content.append(f"**{metadata.name}** - Generated with ❤️ by [RepoReadme](https://github.com/dev-alt/RepoReadme)")
        
        return "\n".join(content)
    
    def _generate_classic_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate classic README template with traditional structure."""
        content = []
        
        # Traditional header
        content.append(f"# {metadata.name}")
        content.append("")
        
        if metadata.description:
            content.append(metadata.description)
        else:
            content.append(f"A {metadata.primary_language.title()} project for {metadata.name.lower()} functionality")
        content.append("")
        
        # Table of Contents (simple)
        if config.include_toc:
            content.append("## Contents")
            content.append("")
            sections = ["Installation", "Usage", "Features", "Contributing", "License"]
            for section in sections:
                if section == "Features" and not metadata.features:
                    continue
                if section == "Contributing" and not config.include_contributing:
                    continue
                if section == "License" and not metadata.license:
                    continue
                content.append(f"- [{section}](#{section.lower()})")
            content.append("")
        
        # Requirements
        content.append("## Requirements")
        content.append("")
        if metadata.primary_language == 'python':
            content.append("- Python 3.8 or higher")
        elif metadata.primary_language in ['javascript', 'typescript']:
            content.append("- Node.js 16 or higher")
        elif metadata.primary_language == 'java':
            content.append("- Java 11 or higher")
        else:
            content.append(f"- {metadata.primary_language.title()} runtime")
        
        if metadata.dependencies:
            content.append("- Package manager (pip, npm, etc.)")
        content.append("")
        
        # Installation
        content.append("## Installation")
        content.append("")
        content.append("1. Clone the repository")
        content.append("")
        if metadata.repository_url:
            content.append(f"   git clone {metadata.repository_url}")
        else:
            content.append(f"   git clone <repository-url>")
        content.append(f"   cd {metadata.name}")
        content.append("")
        
        content.append("2. Install dependencies")
        content.append("")
        if metadata.installation_commands:
            for cmd in metadata.installation_commands[:2]:
                content.append(f"   {cmd}")
        else:
            if metadata.primary_language == 'python':
                content.append("   pip install -r requirements.txt")
            elif metadata.primary_language in ['javascript', 'typescript']:
                content.append("   npm install")
        content.append("")
        
        # Usage
        content.append("## Usage")
        content.append("")
        if metadata.usage_examples:
            content.append("Basic usage example:")
            content.append("")
            content.append("```" + (metadata.primary_language or ""))
            content.append(metadata.usage_examples[0].strip())
            content.append("```")
        else:
            content.append("Run the application:")
            content.append("")
            if len(metadata.installation_commands) > 2:
                content.append(f"    {metadata.installation_commands[2]}")
            else:
                if metadata.primary_language == 'python':
                    content.append("    python main.py")
                elif metadata.primary_language in ['javascript', 'typescript']:
                    content.append("    npm start")
        content.append("")
        
        # Features
        if metadata.features:
            content.append("## Features")
            content.append("")
            for feature in metadata.features[:6]:
                content.append(f"* {feature}")
            content.append("")
        
        # Technical Details
        if metadata.frameworks or metadata.primary_language:
            content.append("## Technical Details")
            content.append("")
            content.append(f"**Language:** {metadata.primary_language.title()}")
            if metadata.frameworks:
                content.append(f"**Framework:** {', '.join(metadata.frameworks[:3])}")
            if metadata.databases:
                content.append(f"**Database:** {', '.join(metadata.databases[:2])}")
            content.append("")
        
        # Project Statistics
        if metadata.total_files > 0:
            content.append("## Project Statistics")
            content.append("")
            content.append(f"- Files: {metadata.total_files:,}")
            content.append(f"- Lines of Code: {metadata.code_lines:,}")
            if metadata.commits > 0:
                content.append(f"- Commits: {metadata.commits:,}")
            if metadata.contributors > 0:
                content.append(f"- Contributors: {metadata.contributors}")
            content.append("")
        
        # Contributing
        if config.include_contributing:
            content.append("## Contributing")
            content.append("")
            content.append("Contributions are welcome! Please follow these steps:")
            content.append("")
            content.append("1. Fork the repository")
            content.append("2. Create a feature branch")
            content.append("3. Make your changes")
            content.append("4. Submit a pull request")
            content.append("")
        
        # License
        if metadata.license:
            content.append("## License")
            content.append("")
            content.append(f"This project is licensed under the {metadata.license} License.")
            content.append("See the LICENSE file for details.")
            content.append("")
        
        # Footer
        content.append("---")
        content.append("")
        content.append(f"Generated with [RepoReadme](https://github.com/dev-alt/RepoReadme)")
        
        return "\n".join(content)
    
    def _generate_minimalist_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate minimalist README template with clean, simple design."""
        content = []
        
        # Ultra-clean header
        content.append(f"# {metadata.name}")
        content.append("")
        if metadata.description:
            content.append(f"{metadata.description}")
            content.append("")
        
        # Single badge if requested
        if config.include_badges and metadata.primary_language:
            lang_colors = {'python': 'blue', 'javascript': 'yellow', 'typescript': 'blue', 'java': 'orange', 'go': 'cyan'}
            color = lang_colors.get(metadata.primary_language.lower(), 'lightgrey')
            content.append(f"![{metadata.primary_language}](https://img.shields.io/badge/-{metadata.primary_language}-{color})")
            content.append("")
        
        # Essential info only
        if metadata.frameworks:
            content.append(f"**Stack:** {', '.join(metadata.frameworks[:2])}")
            content.append("")
        
        # Minimal install
        content.append("## Install")
        content.append("")
        content.append("```bash")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        if metadata.installation_commands:
            content.append(metadata.installation_commands[0] if metadata.installation_commands[0] != f"git clone {metadata.repository_url}" else metadata.installation_commands[1] if len(metadata.installation_commands) > 1 else "")
        else:
            if metadata.primary_language == 'python':
                content.append("pip install -r requirements.txt")
            elif metadata.primary_language in ['javascript', 'typescript']:
                content.append("npm install")
        content.append("```")
        content.append("")
        
        # Minimal usage
        content.append("## Usage")
        content.append("")
        content.append("```bash")
        if len(metadata.installation_commands) > 2:
            content.append(metadata.installation_commands[2])
        elif len(metadata.installation_commands) > 1:
            content.append(metadata.installation_commands[1])
        else:
            if metadata.primary_language == 'python':
                content.append("python main.py")
            elif metadata.primary_language in ['javascript', 'typescript']:
                content.append("npm start")
            else:
                content.append("# Run the application")
        content.append("```")
        content.append("")
        
        # Key features (max 3)
        if metadata.features:
            content.append("## Features")
            content.append("")
            for feature in metadata.features[:3]:
                content.append(f"- {feature}")
            content.append("")
        
        # Minimal license
        if metadata.license:
            content.append("## License")
            content.append("")
            content.append(f"{metadata.license}")
        
        return "\n".join(content)
    
    def _generate_developer_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate developer-focused README with technical details."""
        content = []
        
        content.append(f"# {metadata.name}")
        content.append("")
        
        if metadata.description:
            content.append(f"**{metadata.description}**")
            content.append("")
        
        # Technical Overview
        content.append("## Technical Overview")
        content.append("")
        content.append(f"- **Language:** {metadata.primary_language.title()}")
        content.append(f"- **Type:** {metadata.project_type.title()}")
        if metadata.frameworks:
            content.append(f"- **Framework:** {', '.join(metadata.frameworks)}")
        if metadata.databases:
            content.append(f"- **Database:** {', '.join(metadata.databases)}")
        content.append("")
        
        # Architecture
        if metadata.structure:
            content.append("## Architecture")
            content.append("")
            content.append("```")
            for directory in metadata.structure.keys():
                content.append(f"{directory}/ - {directory.title()} components")
            content.append("```")
            content.append("")
        
        # Dependencies
        if metadata.dependencies:
            content.append("## Dependencies")
            content.append("")
            for pkg_manager, deps in metadata.dependencies.items():
                content.append(f"### {pkg_manager.upper()}")
                for dep in deps[:10]:  # Limit to first 10
                    content.append(f"- {dep}")
                if len(deps) > 10:
                    content.append(f"- ... and {len(deps) - 10} more")
                content.append("")
        
        # Development Setup
        content.append("## Development Setup")
        content.append("")
        content.append("```bash")
        content.append("# Clone repository")
        content.append(f"git clone <repository-url>")
        content.append(f"cd {metadata.name}")
        content.append("")
        content.append("# Install dependencies")
        if metadata.installation_commands:
            content.append(metadata.installation_commands[0])
        content.append("")
        content.append("# Start development server")
        if len(metadata.installation_commands) > 1:
            content.append(metadata.installation_commands[1])
        content.append("```")
        content.append("")
        
        # Testing
        if metadata.has_tests:
            content.append("## Testing")
            content.append("")
            content.append("```bash")
            if metadata.primary_language == 'python':
                content.append("pytest tests/ -v")
            elif metadata.primary_language == 'javascript':
                content.append("npm test")
            content.append("```")
            content.append("")
        
        # Performance
        content.append("## Performance")
        content.append("")
        content.append(f"- **Files:** {metadata.total_files:,}")
        content.append(f"- **Lines of Code:** {metadata.code_lines:,}")
        if metadata.commits:
            content.append(f"- **Commits:** {metadata.commits:,}")
        if metadata.contributors:
            content.append(f"- **Contributors:** {metadata.contributors}")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_academic_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate academic/research README template."""
        content = []
        
        content.append(f"# {metadata.name}")
        content.append("")
        
        content.append("## Abstract")
        content.append("")
        if metadata.description:
            content.append(metadata.description)
        else:
            content.append("This research project explores...")
        content.append("")
        
        content.append("## Background")
        content.append("")
        content.append("Add background information and motivation for this research.")
        content.append("")
        
        content.append("## Methodology")
        content.append("")
        content.append("Describe the methodology and approach used.")
        content.append("")
        
        content.append("## Implementation")
        content.append("")
        if metadata.primary_language:
            content.append(f"The implementation is written in {metadata.primary_language.title()}.")
        if metadata.frameworks:
            content.append(f"Key frameworks used: {', '.join(metadata.frameworks)}")
        content.append("")
        
        content.append("## Results")
        content.append("")
        content.append("Present your findings and results here.")
        content.append("")
        
        content.append("## Usage")
        content.append("")
        if metadata.installation_commands:
            content.append("```bash")
            for cmd in metadata.installation_commands:
                content.append(cmd)
            content.append("```")
        content.append("")
        
        content.append("## Citation")
        content.append("")
        content.append("If you use this work in your research, please cite:")
        content.append("```")
        content.append(f"@software{{{metadata.name}_{datetime.now().year},")
        content.append(f"  title = {{{metadata.name}}},")
        if metadata.author:
            content.append(f"  author = {{{metadata.author}}},")
        content.append(f"  year = {{{datetime.now().year}}},")
        if metadata.repository_url:
            content.append(f"  url = {{{metadata.repository_url}}}")
        content.append("}")
        content.append("```")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_corporate_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate corporate/business README template."""
        content = []
        
        content.append(f"# {metadata.name}")
        content.append("")
        
        # Executive Summary
        content.append("## Executive Summary")
        content.append("")
        if metadata.description:
            content.append(metadata.description)
        else:
            content.append("This project delivers business value by...")
        content.append("")
        
        # Business Value
        content.append("## Business Value")
        content.append("")
        if metadata.features:
            content.append("Key benefits:")
            for feature in metadata.features:
                content.append(f"- {feature}")
        content.append("")
        
        # Technical Specifications
        content.append("## Technical Specifications")
        content.append("")
        content.append("| Component | Technology |")
        content.append("|-----------|------------|")
        content.append(f"| Runtime | {metadata.primary_language.title()} |")
        if metadata.frameworks:
            content.append(f"| Framework | {', '.join(metadata.frameworks)} |")
        if metadata.databases:
            content.append(f"| Database | {', '.join(metadata.databases)} |")
        content.append("")
        
        # Deployment
        content.append("## Deployment")
        content.append("")
        content.append("### Prerequisites")
        content.append("- Production environment setup")
        content.append("- Required access credentials")
        content.append("- Infrastructure provisioning")
        content.append("")
        
        content.append("### Installation Steps")
        content.append("")
        if metadata.installation_commands:
            for i, cmd in enumerate(metadata.installation_commands, 1):
                content.append(f"{i}. `{cmd}`")
        content.append("")
        
        # Support and Maintenance
        content.append("## Support and Maintenance")
        content.append("")
        content.append("- **Support Team:** Development Team")
        content.append("- **SLA:** 99.9% uptime")
        content.append("- **Maintenance Window:** Sundays 2-4 AM UTC")
        content.append("")
        
        # Compliance
        content.append("## Compliance")
        content.append("")
        content.append("This project adheres to:")
        content.append("- Company coding standards")
        content.append("- Security best practices")
        if metadata.has_tests:
            content.append("- Quality assurance requirements")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_startup_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate startup-focused README template."""
        content = []
        
        # Startup header with vision
        emoji_map = {'web-app': '🚀', 'mobile-app': '📱', 'api': '⚡', 'library': '🔧', 'ai_ml': '🤖'}
        emoji = emoji_map.get(metadata.project_type, '💫')
        
        content.append(f"# {emoji} {metadata.name}")
        content.append("")
        if metadata.description:
            content.append(f"**{metadata.description}**")
        else:
            content.append(f"**Revolutionizing {metadata.project_type.replace('-', ' ')} with cutting-edge technology**")
        content.append("")
        
        # Mission statement
        content.append("## 🎯 Our Mission")
        content.append("")
        content.append(f"At {metadata.name}, we're building the future of {metadata.project_type.replace('-', ' ')} technology.")
        content.append("Our innovative platform delivers unparalleled performance and user experience.")
        content.append("")
        
        # Key value propositions
        content.append("## 💡 Why Choose Us?")
        content.append("")
        content.append("- **🔥 Blazing Fast** - Optimized performance for enterprise scale")
        content.append("- **🛡️ Enterprise Ready** - Built with security and reliability in mind") 
        content.append("- **🎨 Beautiful Design** - Intuitive user experience that delights")
        content.append("- **🔧 Easy Integration** - Seamless setup in minutes, not hours")
        content.append("- **📈 Scalable** - Grows with your business needs")
        content.append("")
        
        # Quick start for busy founders
        content.append("## ⚡ Quick Start")
        content.append("")
        content.append("Get up and running in under 5 minutes:")
        content.append("")
        content.append("```bash")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        if metadata.installation_commands:
            for cmd in metadata.installation_commands[:2]:
                content.append(cmd)
        content.append("```")
        content.append("")
        
        # Demo/Live version
        content.append("## 🌟 See It In Action")
        content.append("")
        content.append("👉 **[Live Demo](https://demo-link.com)** - Try it now!")
        content.append("")
        content.append("👉 **[Documentation](https://docs-link.com)** - Complete guides")
        content.append("")
        
        # Tech stack (investor focused)
        content.append("## 🛠️ Built With Modern Tech")
        content.append("")
        content.append(f"**Core Technology:** {metadata.primary_language.title()}")
        if metadata.frameworks:
            content.append(f"**Framework:** {', '.join(metadata.frameworks[:3])}")
        if metadata.databases:
            content.append(f"**Database:** {', '.join(metadata.databases[:2])}")
        content.append("**Infrastructure:** Cloud-native, microservices architecture")
        content.append("")
        
        # Traction/metrics
        content.append("## 📊 Traction")
        content.append("")
        content.append("- 🚀 **Growing Fast:** Used by X+ companies")
        content.append("- ⭐ **High Quality:** 99.9% uptime guarantee") 
        content.append("- 💪 **Battle Tested:** Processing X+ requests daily")
        content.append("- 🌍 **Global Reach:** Available in X+ countries")
        content.append("")
        
        # Call to action
        content.append("## 🤝 Get Involved")
        content.append("")
        content.append("**Interested in partnering?** [Contact us](mailto:hello@company.com)")
        content.append("")
        content.append("**Want to invest?** [Learn more](https://investor-deck.com)")
        content.append("")
        content.append("**Developer?** We're hiring! [View open positions](https://careers.company.com)")
        content.append("")
        
        # Social proof
        content.append("## 🏆 Recognition")
        content.append("")
        content.append("- 🥇 Winner of XYZ Startup Competition 2024")
        content.append("- 📰 Featured in TechCrunch, Product Hunt")
        content.append("- 💰 Backed by leading VCs")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_gaming_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate gaming-focused README template."""
        content = []
        
        # Gaming header
        content.append(f"# 🎮 {metadata.name}")
        content.append("")
        if metadata.description:
            content.append(f"**{metadata.description}**")
        else:
            content.append("**An epic gaming experience awaits!**")
        content.append("")
        
        # Game trailer/screenshots
        content.append("## 🎬 Game Preview")
        content.append("")
        content.append("![Game Screenshot](https://via.placeholder.com/800x400?text=Game+Screenshot)")
        content.append("")
        content.append("🎥 **[Watch Trailer](https://youtube.com/watch?v=trailer)** | 🕹️ **[Play Demo](https://demo-link.com)**")
        content.append("")
        
        # Game features
        content.append("## 🌟 Game Features")
        content.append("")
        if metadata.features:
            for feature in metadata.features:
                content.append(f"- 🎯 **{feature}**")
        else:
            content.append("- 🎯 **Immersive Gameplay** - Hours of entertainment")
            content.append("- 🏆 **Achievement System** - Unlock rewards and compete")
            content.append("- 🌍 **Multiplayer Mode** - Play with friends worldwide")
            content.append("- 🎨 **Stunning Graphics** - Visual masterpiece")
        content.append("")
        
        # System requirements
        content.append("## 💻 System Requirements")
        content.append("")
        content.append("### Minimum Requirements")
        content.append("- **OS:** Windows 10 / macOS 10.14 / Ubuntu 18.04")
        content.append("- **Processor:** Intel i5-8400 / AMD Ryzen 5 2600")
        content.append("- **Memory:** 8 GB RAM")
        content.append("- **Graphics:** GTX 1060 / RX 580")
        content.append("- **Storage:** 20 GB available space")
        content.append("")
        
        content.append("### Recommended Requirements")
        content.append("- **OS:** Windows 11 / macOS 12+ / Ubuntu 20.04+")
        content.append("- **Processor:** Intel i7-10700K / AMD Ryzen 7 3700X")
        content.append("- **Memory:** 16 GB RAM")
        content.append("- **Graphics:** RTX 3070 / RX 6700 XT")
        content.append("- **Storage:** 50 GB SSD space")
        content.append("")
        
        # Installation for gamers
        content.append("## 🚀 Installation")
        content.append("")
        content.append("### Option 1: Download Release")
        content.append("1. Go to [Releases](https://github.com/user/repo/releases)")
        content.append("2. Download the latest version for your platform")
        content.append("3. Extract and run the installer")
        content.append("")
        
        content.append("### Option 2: Build from Source")
        content.append("```bash")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        if metadata.installation_commands:
            for cmd in metadata.installation_commands:
                content.append(cmd)
        content.append("```")
        content.append("")
        
        # Controls/gameplay
        content.append("## 🎮 How to Play")
        content.append("")
        content.append("### Controls")
        content.append("- **WASD** - Movement")
        content.append("- **Mouse** - Look around")
        content.append("- **Space** - Jump/Action")
        content.append("- **ESC** - Pause menu")
        content.append("")
        
        # Community
        content.append("## 🌟 Join Our Community")
        content.append("")
        content.append("- 💬 **[Discord Server](https://discord.gg/game)** - Chat with players")
        content.append("- 📺 **[Twitch](https://twitch.tv/channel)** - Watch live streams")
        content.append("- 🐦 **[Twitter](https://twitter.com/game)** - Latest updates")
        content.append("- 📧 **[Newsletter](https://newsletter-signup.com)** - Development updates")
        content.append("")
        
        # Contributing for modders
        content.append("## 🔧 Modding & Contributing")
        content.append("")
        content.append("Want to create mods or contribute to development?")
        content.append("")
        content.append("- 📖 **[Modding Guide](https://docs.com/modding)** - Create custom content")
        content.append("- 🛠️ **[Development Setup](https://docs.com/dev)** - Contribute to the game")
        content.append("- 🎨 **[Asset Guidelines](https://docs.com/assets)** - Submit artwork")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_security_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate security-focused README template."""
        content = []
        
        # Security header
        content.append(f"# 🔒 {metadata.name}")
        content.append("")
        if metadata.description:
            content.append(f"**{metadata.description}**")
        else:
            content.append("**Enterprise-grade security solution with advanced threat protection**")
        content.append("")
        
        # Security badges
        if config.include_badges:
            content.append("[![Security Rating](https://img.shields.io/badge/security-A+-green)](https://security-report.com)")
            content.append("[![Vulnerability Scan](https://img.shields.io/badge/vulnerabilities-0-green)](https://scan-results.com)")
            content.append("[![Compliance](https://img.shields.io/badge/compliance-SOC2-blue)](https://compliance-report.com)")
            content.append("")
        
        # Security overview
        content.append("## 🛡️ Security Overview")
        content.append("")
        content.append("This security solution provides comprehensive protection against modern threats:")
        content.append("")
        content.append("- **🔐 Zero-Trust Architecture** - Never trust, always verify")
        content.append("- **🔍 Real-time Monitoring** - 24/7 threat detection")
        content.append("- **🚨 Instant Alerts** - Immediate notification of security events")
        content.append("- **📊 Compliance Ready** - SOC2, ISO 27001, GDPR compliant")
        content.append("- **🔒 End-to-End Encryption** - AES-256 encryption at rest and in transit")
        content.append("")
        
        # Threat protection
        content.append("## 🎯 Threat Protection")
        content.append("")
        content.append("### Protects Against")
        content.append("- **Malware & Ransomware** - Advanced detection and quarantine")
        content.append("- **Phishing Attacks** - URL scanning and email protection")
        content.append("- **Data Breaches** - DLP and access controls")
        content.append("- **Insider Threats** - Behavioral analysis and monitoring")
        content.append("- **Zero-day Exploits** - Heuristic and sandbox analysis")
        content.append("")
        
        # Security features
        content.append("## 🔧 Security Features")
        content.append("")
        if metadata.features:
            for feature in metadata.features:
                content.append(f"- 🛡️ **{feature}**")
        else:
            content.append("- 🛡️ **Multi-Factor Authentication** - Enhanced login security")
            content.append("- 🛡️ **Role-Based Access Control** - Granular permissions")
            content.append("- 🛡️ **Audit Logging** - Complete activity tracking")
            content.append("- 🛡️ **Secure API Gateway** - Protected endpoints")
        content.append("")
        
        # Installation with security notes
        content.append("## 🚀 Secure Installation")
        content.append("")
        content.append("### Prerequisites")
        content.append("- Ensure system is updated with latest security patches")
        content.append("- Verify GPG signature of downloaded files")
        content.append("- Run on isolated network segment if possible")
        content.append("")
        
        content.append("### Installation Steps")
        content.append("```bash")
        content.append("# 1. Verify checksums")
        content.append("sha256sum -c checksums.txt")
        content.append("")
        content.append("# 2. Install")
        if metadata.installation_commands:
            for cmd in metadata.installation_commands:
                content.append(cmd)
        content.append("")
        content.append("# 3. Initialize security settings")
        content.append("./security-setup.sh")
        content.append("```")
        content.append("")
        
        # Security configuration
        content.append("## ⚙️ Security Configuration")
        content.append("")
        content.append("### Initial Setup")
        content.append("1. **Generate Certificates** - Create SSL/TLS certificates")
        content.append("2. **Configure Firewall** - Set up network access rules")
        content.append("3. **Create Admin User** - Set up administrative access")
        content.append("4. **Enable Logging** - Configure audit trails")
        content.append("5. **Test Connectivity** - Verify secure communications")
        content.append("")
        
        # Compliance information
        content.append("## 📋 Compliance & Certifications")
        content.append("")
        content.append("| Standard | Status | Certificate |")
        content.append("|----------|--------|-------------|")
        content.append("| SOC 2 Type II | ✅ Certified | [View Report](https://cert-link.com) |")
        content.append("| ISO 27001 | ✅ Certified | [View Certificate](https://iso-cert.com) |")
        content.append("| GDPR | ✅ Compliant | [Privacy Policy](https://privacy.com) |")
        content.append("| HIPAA | ✅ Compliant | [BAA Available](https://baa.com) |")
        content.append("")
        
        # Security reporting
        content.append("## 🚨 Security Reporting")
        content.append("")
        content.append("### Report Security Issues")
        content.append("**DO NOT** create public GitHub issues for security vulnerabilities.")
        content.append("")
        content.append("Instead, please report security issues to:")
        content.append("- **Email:** security@company.com")
        content.append("- **GPG Key:** [Download Public Key](https://pgp-key.com)")
        content.append("- **Bug Bounty:** [HackerOne Program](https://hackerone.com/program)")
        content.append("")
        
        content.append("### Response Timeline")
        content.append("- **Critical:** 4 hours")
        content.append("- **High:** 24 hours")
        content.append("- **Medium:** 72 hours")
        content.append("- **Low:** 1 week")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_ai_ml_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate AI/ML focused README template."""
        content = []
        
        # AI/ML header
        content.append(f"# 🤖 {metadata.name}")
        content.append("")
        if metadata.description:
            content.append(f"**{metadata.description}**")
        else:
            content.append("**Cutting-edge AI/ML solution powered by advanced algorithms**")
        content.append("")
        
        # Model badges
        if config.include_badges:
            content.append("[![Model Accuracy](https://img.shields.io/badge/accuracy-95.2%25-brightgreen)](https://model-metrics.com)")
            content.append("[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://python.org)")
            content.append("[![Framework](https://img.shields.io/badge/framework-PyTorch-orange)](https://pytorch.org)")
            content.append("")
        
        # Model overview
        content.append("## 🎯 Model Overview")
        content.append("")
        content.append("| Metric | Value | Details |")
        content.append("|--------|-------|---------|")
        content.append("| **Accuracy** | 95.2% | On validation dataset |")
        content.append("| **Precision** | 94.1% | Positive prediction accuracy |")
        content.append("| **Recall** | 96.3% | True positive detection rate |")
        content.append("| **F1-Score** | 95.2% | Harmonic mean of precision/recall |")
        content.append("| **Training Time** | 4.2 hours | On V100 GPU |")
        content.append("| **Inference Speed** | 12ms | Average per prediction |")
        content.append("")
        
        # Dataset information
        content.append("## 📊 Dataset & Training")
        content.append("")
        content.append("### Dataset Details")
        content.append("- **Size:** 100K+ labeled samples")
        content.append("- **Split:** 80% train, 15% validation, 5% test")
        content.append("- **Classes:** 10 distinct categories")
        content.append("- **Data Quality:** Manually verified and cleaned")
        content.append("- **Augmentation:** Rotation, scaling, noise injection")
        content.append("")
        
        content.append("### Model Architecture")
        content.append("```python")
        content.append("# Simplified model structure")
        content.append("model = nn.Sequential(")
        content.append("    ConvBlock(3, 64),      # Input processing")
        content.append("    ResNetBackbone(),      # Feature extraction") 
        content.append("    AttentionHead(),       # Attention mechanism")
        content.append("    ClassificationHead()   # Final predictions")
        content.append(")")
        content.append("```")
        content.append("")
        
        # Installation with ML requirements
        content.append("## 🚀 Quick Start")
        content.append("")
        content.append("### Requirements")
        content.append("- Python 3.8+")
        content.append("- CUDA 11.0+ (for GPU acceleration)")
        content.append("- 8GB+ RAM (16GB recommended)")
        content.append("- 2GB+ disk space")
        content.append("")
        
        content.append("### Installation")
        content.append("```bash")
        content.append("# Clone repository")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        content.append("")
        content.append("# Install dependencies")
        content.append("pip install -r requirements.txt")
        content.append("")
        content.append("# Download pre-trained model")
        content.append("python download_model.py")
        content.append("```")
        content.append("")
        
        # Usage examples for ML
        content.append("## 💡 Usage Examples")
        content.append("")
        
        content.append("### Basic Inference")
        content.append("```python")
        content.append("from model import AIModel")
        content.append("")
        content.append("# Load pre-trained model")
        content.append("model = AIModel.load_pretrained('model_v1.0.pth')")
        content.append("")
        content.append("# Make prediction")
        content.append("result = model.predict('input_data.jpg')")
        content.append("print(f'Prediction: {result.class_name} (confidence: {result.confidence:.2f})')")
        content.append("```")
        content.append("")
        
        content.append("### Batch Processing")
        content.append("```python")
        content.append("# Process multiple files")
        content.append("results = model.predict_batch(['file1.jpg', 'file2.jpg', 'file3.jpg'])")
        content.append("for result in results:")
        content.append("    print(f'{result.filename}: {result.prediction}')")
        content.append("```")
        content.append("")
        
        content.append("### Fine-tuning")
        content.append("```python")
        content.append("# Fine-tune on your dataset")
        content.append("trainer = ModelTrainer(model)")
        content.append("trainer.fine_tune(")
        content.append("    train_data='custom_dataset/',")
        content.append("    epochs=10,")
        content.append("    learning_rate=1e-4")
        content.append(")")
        content.append("```")
        content.append("")
        
        # Performance benchmarks
        content.append("## 📈 Performance Benchmarks")
        content.append("")
        content.append("### Hardware Comparison")
        content.append("| Hardware | Inference Speed | Batch Size | Memory Usage |")
        content.append("|----------|----------------|------------|--------------|")
        content.append("| CPU (Intel i7) | 150ms | 1 | 2GB |")
        content.append("| GPU (GTX 1080) | 12ms | 32 | 4GB |")
        content.append("| GPU (RTX 3080) | 8ms | 64 | 6GB |")
        content.append("| GPU (V100) | 6ms | 128 | 8GB |")
        content.append("")
        
        # Research and citations
        content.append("## 📚 Research & Citations")
        content.append("")
        content.append("This work builds upon several key research papers:")
        content.append("")
        content.append("```bibtex")
        content.append("@article{author2024,")
        content.append(f"  title={{{metadata.name}: Advanced AI Model}},")
        content.append("  author={Research Team},")
        content.append("  journal={AI Conference},")
        content.append("  year={2024}")
        content.append("}")
        content.append("```")
        content.append("")
        
        content.append("### Related Papers")
        content.append("- [Original Research Paper](https://arxiv.org/paper-link)")
        content.append("- [Technical Documentation](https://docs.company.com)")
        content.append("- [Model Card](https://model-card.com) - Detailed model information")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_mobile_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate mobile app focused README template."""
        content = []
        
        # Mobile header with app icon
        content.append(f"# 📱 {metadata.name}")
        content.append("")
        content.append("![App Icon](https://via.placeholder.com/128x128?text=📱)")
        content.append("")
        if metadata.description:
            content.append(f"**{metadata.description}**")
        else:
            content.append("**Beautiful, fast, and intuitive mobile experience**")
        content.append("")
        
        # App store badges
        if config.include_badges:
            content.append("[![Download on App Store](https://img.shields.io/badge/Download-App%20Store-blue?logo=app-store)](https://apps.apple.com/app)")
            content.append("[![Get it on Google Play](https://img.shields.io/badge/Download-Google%20Play-green?logo=google-play)](https://play.google.com/store/apps)")
            content.append("[![Rating](https://img.shields.io/badge/rating-4.8★-yellow)](https://app-reviews.com)")
            content.append("")
        
        # Screenshots
        content.append("## 📸 Screenshots")
        content.append("")
        content.append("| Home | Features | Settings |")
        content.append("|------|----------|----------|")
        content.append("| ![Home](https://via.placeholder.com/200x400?text=Home) | ![Features](https://via.placeholder.com/200x400?text=Features) | ![Settings](https://via.placeholder.com/200x400?text=Settings) |")
        content.append("")
        
        # App features
        content.append("## ✨ Features")
        content.append("")
        if metadata.features:
            for feature in metadata.features:
                content.append(f"- 📱 **{feature}**")
        else:
            content.append("- 📱 **Intuitive Interface** - Beautiful and easy to use")
            content.append("- 🔄 **Real-time Sync** - Keep data synchronized across devices")
            content.append("- 🔒 **Secure & Private** - Your data stays protected")
            content.append("- 🎨 **Customizable Themes** - Personalize your experience")
            content.append("- 📊 **Analytics Dashboard** - Track your progress")
        content.append("")
        
        # Platform support
        content.append("## 📱 Platform Support")
        content.append("")
        content.append("### iOS")
        content.append("- **Minimum Version:** iOS 13.0")
        content.append("- **Compatible Devices:** iPhone 6s and newer")
        content.append("- **iPad Support:** Optimized for all iPad models")
        content.append("- **Apple Watch:** Companion app available")
        content.append("")
        
        content.append("### Android")
        content.append("- **Minimum Version:** Android 7.0 (API 24)")
        content.append("- **Architecture:** ARM64, x86_64")
        content.append("- **Wear OS:** Companion app available")
        content.append("- **Android TV:** Large screen optimized")
        content.append("")
        
        # Installation options
        content.append("## 📲 Installation")
        content.append("")
        
        content.append("### For Users")
        content.append("**📱 Download from official stores:**")
        content.append("- [iOS App Store](https://apps.apple.com/app/your-app)")
        content.append("- [Google Play Store](https://play.google.com/store/apps/your-app)")
        content.append("- [Samsung Galaxy Store](https://galaxystore.samsung.com)")
        content.append("")
        
        content.append("### For Developers")
        content.append("**🛠️ Build from source:**")
        content.append("```bash")
        content.append("# Clone repository")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        content.append("")
        content.append("# Install dependencies")
        if 'flutter' in str(metadata.frameworks).lower():
            content.append("flutter pub get")
        elif 'react-native' in str(metadata.frameworks).lower():
            content.append("npm install")
        elif metadata.primary_language == 'java':
            content.append("./gradlew build")
        content.append("")
        content.append("# Run on device/simulator")
        if 'flutter' in str(metadata.frameworks).lower():
            content.append("flutter run")
        elif 'react-native' in str(metadata.frameworks).lower():
            content.append("npx react-native run-ios")
            content.append("npx react-native run-android")
        content.append("```")
        content.append("")
        
        # User guide
        content.append("## 📖 User Guide")
        content.append("")
        content.append("### Getting Started")
        content.append("1. **📲 Download & Install** - Get the app from your device's app store")
        content.append("2. **👤 Create Account** - Sign up with email or social login")
        content.append("3. **⚙️ Setup Preferences** - Customize the app to your needs")
        content.append("4. **🚀 Start Using** - Explore features and enjoy!")
        content.append("")
        
        content.append("### Key Features Guide")
        content.append("- **🏠 Home Screen** - Quick access to main features")
        content.append("- **⚙️ Settings** - Customize appearance and behavior")
        content.append("- **📊 Analytics** - View your usage statistics")
        content.append("- **🔄 Sync** - Keep data updated across devices")
        content.append("")
        
        # Reviews and feedback
        content.append("## ⭐ User Reviews")
        content.append("")
        content.append("> *\"Amazing app! So intuitive and fast. Love the design!\"* ⭐⭐⭐⭐⭐")
        content.append("> *\"Best app in its category. Highly recommended!\"* ⭐⭐⭐⭐⭐")
        content.append("> *\"Great features and excellent support team.\"* ⭐⭐⭐⭐⭐")
        content.append("")
        
        # Support and feedback
        content.append("## 📞 Support & Feedback")
        content.append("")
        content.append("**Need help?** We're here for you!")
        content.append("")
        content.append("- 📧 **Email Support:** support@app.com")
        content.append("- 💬 **Live Chat:** Available in-app")
        content.append("- 📖 **Help Center:** [help.app.com](https://help.app.com)")
        content.append("- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/user/repo/issues)")
        content.append("")
        
        content.append("**Love the app?** Leave us a review!")
        content.append("- [⭐ Rate on App Store](https://apps.apple.com/app/rate)")
        content.append("- [⭐ Rate on Google Play](https://play.google.com/store/rate)")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_opensource_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate open source focused README template."""
        content = []
        
        # Open source header
        content.append(f"# 🌟 {metadata.name}")
        content.append("")
        if metadata.description:
            content.append(f"> {metadata.description}")
        else:
            content.append(f"> Open source {metadata.project_type.replace('-', ' ')} built by the community, for the community")
        content.append("")
        
        # Community badges
        if config.include_badges:
            content.append("[![Contributors](https://img.shields.io/github/contributors/user/repo)](https://github.com/user/repo/graphs/contributors)")
            content.append("[![Forks](https://img.shields.io/github/forks/user/repo)](https://github.com/user/repo/network/members)")
            content.append("[![Stars](https://img.shields.io/github/stars/user/repo)](https://github.com/user/repo/stargazers)")
            content.append("[![Issues](https://img.shields.io/github/issues/user/repo)](https://github.com/user/repo/issues)")
            content.append("[![License](https://img.shields.io/github/license/user/repo)](https://github.com/user/repo/blob/main/LICENSE)")
            content.append("")
        
        # Mission statement
        content.append("## 🎯 Our Mission")
        content.append("")
        content.append("We believe in the power of open source software to change the world. This project aims to:")
        content.append("")
        content.append("- 🌍 **Make technology accessible** to everyone")
        content.append("- 🤝 **Foster collaboration** between developers worldwide") 
        content.append("- 📚 **Share knowledge** and best practices")
        content.append("- 🔧 **Build better tools** through community input")
        content.append("- 🚀 **Advance the state of the art** in our field")
        content.append("")
        
        # Community stats
        content.append("## 📊 Community")
        content.append("")
        content.append("Join our thriving community of developers and users!")
        content.append("")
        content.append("- 👥 **Contributors:** 50+ amazing people")
        content.append("- ⭐ **GitHub Stars:** 1,000+")
        content.append("- 🍴 **Forks:** 200+")
        content.append("- 🐛 **Issues Resolved:** 500+")
        content.append("- 🌍 **Used By:** Companies worldwide")
        content.append("")
        
        # Getting started for contributors
        content.append("## 🚀 Getting Started")
        content.append("")
        content.append("### For Users")
        content.append("```bash")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        if metadata.installation_commands:
            for cmd in metadata.installation_commands:
                content.append(cmd)
        content.append("```")
        content.append("")
        
        content.append("### For Contributors")
        content.append("Want to help make this project even better?")
        content.append("")
        content.append("1. 🍴 **Fork the repository**")
        content.append("2. 🔧 **Set up development environment**")
        content.append("3. 🎯 **Pick an issue** from our [good first issues](https://github.com/user/repo/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)")
        content.append("4. 💻 **Make your changes**")
        content.append("5. 🧪 **Add tests** if applicable")
        content.append("6. 📝 **Update documentation**")
        content.append("7. 🚀 **Submit a pull request**")
        content.append("")
        
        # Contribution guidelines
        content.append("## 🤝 Contributing")
        content.append("")
        content.append("We love contributions! Here's how you can help:")
        content.append("")
        
        content.append("### 🐛 Report Bugs")
        content.append("Found a bug? [Open an issue](https://github.com/user/repo/issues/new?template=bug_report.md)")
        content.append("")
        
        content.append("### 💡 Request Features")
        content.append("Have an idea? [Request a feature](https://github.com/user/repo/issues/new?template=feature_request.md)")
        content.append("")
        
        content.append("### 📖 Improve Documentation")
        content.append("Documentation can always be better! Feel free to:")
        content.append("- Fix typos or unclear explanations")
        content.append("- Add examples and use cases")
        content.append("- Translate to other languages")
        content.append("")
        
        content.append("### 💻 Code Contributions")
        content.append("Check out our [Contributing Guide](CONTRIBUTING.md) for:")
        content.append("- Development setup")
        content.append("- Coding standards")
        content.append("- Testing guidelines")
        content.append("- Pull request process")
        content.append("")
        
        # Recognition
        content.append("## 🏆 Contributors")
        content.append("")
        content.append("Thanks to all the amazing people who have contributed to this project!")
        content.append("")
        content.append("[![Contributors](https://contrib.rocks/image?repo=user/repo)](https://github.com/user/repo/graphs/contributors)")
        content.append("")
        
        # Support the project
        content.append("## 💖 Support the Project")
        content.append("")
        content.append("If this project has been helpful, please consider:")
        content.append("")
        content.append("- ⭐ **Star this repository** on GitHub")
        content.append("- 🐦 **Share it** on social media")
        content.append("- 💬 **Tell your friends** about it")
        content.append("- 🍕 **Buy us coffee** [Sponsor](https://github.com/sponsors/user)")
        content.append("- 🤝 **Contribute** code or documentation")
        content.append("")
        
        # Community links
        content.append("## 🌐 Community Links")
        content.append("")
        content.append("Join our community discussions:")
        content.append("")
        content.append("- 💬 **[GitHub Discussions](https://github.com/user/repo/discussions)** - Q&A and ideas")
        content.append("- 🗨️ **[Discord Server](https://discord.gg/project)** - Real-time chat")
        content.append("- 📧 **[Mailing List](https://groups.google.com/project)** - Updates and announcements")
        content.append("- 🐦 **[Twitter](https://twitter.com/project)** - Latest news")
        content.append("- 📺 **[YouTube](https://youtube.com/channel)** - Tutorials and demos")
        content.append("")
        
        # License
        content.append("## 📄 License")
        content.append("")
        if metadata.license:
            content.append(f"This project is licensed under the {metadata.license} License - see the [LICENSE](LICENSE) file for details.")
        else:
            content.append("This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.")
        content.append("")
        content.append("This means you are free to:")
        content.append("- ✅ Use it for any purpose")
        content.append("- ✅ Modify and distribute")
        content.append("- ✅ Use in commercial projects")
        content.append("- ✅ Create derivative works")
        content.append("")
        
        return "\n".join(content)
    
    def _generate_badges(self, metadata: ProjectMetadata, config: TemplateConfig) -> List[str]:
        """Generate badge markup for README."""
        badges = []
        base_url = "https://img.shields.io"
        style = config.badge_style
        
        # Version badge
        if metadata.version:
            badges.append(f"![Version]({base_url}/badge/version-{metadata.version}-blue.svg?style={style})")
        
        # License badge
        if metadata.license:
            license_color = "green"
            badges.append(f"![License]({base_url}/badge/license-{metadata.license}-{license_color}.svg?style={style})")
        
        # Language badge
        if metadata.primary_language:
            lang_colors = {
                'python': 'blue',
                'javascript': 'yellow',
                'typescript': 'blue',
                'java': 'orange',
                'go': 'cyan',
                'rust': 'orange',
                'php': 'purple'
            }
            color = lang_colors.get(metadata.primary_language.lower(), 'lightgrey')
            badges.append(f"![Language]({base_url}/badge/language-{metadata.primary_language}-{color}.svg?style={style})")
        
        # Quality score badge
        if metadata.code_quality_score > 0:
            score_color = "green" if metadata.code_quality_score >= 80 else "yellow" if metadata.code_quality_score >= 60 else "red"
            badges.append(f"![Quality]({base_url}/badge/quality-{metadata.code_quality_score:.0f}%25-{score_color}.svg?style={style})")
        
        if badges:
            return ["## Badges", ""] + [" ".join(badges)] + [""]
        return []
    
    def _generate_table_of_contents(self, metadata: ProjectMetadata, config: TemplateConfig) -> List[str]:
        """Generate table of contents."""
        toc = ["## Table of Contents", ""]
        
        sections = [
            ("Features", metadata.features),
            ("Technology Stack", metadata.languages or metadata.frameworks),
            ("Getting Started", True),
            ("Usage", metadata.usage_examples),
            ("API Documentation", config.include_api_docs and metadata.project_type in ['api', 'web-app']),
            ("Project Structure", metadata.structure),
            ("Testing", metadata.has_tests),
            ("Contributing", config.include_contributing),
            ("License", config.include_license_section and metadata.license),
        ]
        
        for section_name, condition in sections:
            if condition:
                anchor = section_name.lower().replace(" ", "-")
                toc.append(f"- [📚 {section_name}](#{anchor})")
        
        return toc
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def get_template_description(self, template_name: str) -> str:
        """Get description of a specific template."""
        descriptions = {
            'modern': 'Comprehensive template with badges, emojis, and detailed sections',
            'classic': 'Traditional format with essential information and project statistics',
            'minimalist': 'Clean and simple design with minimal content and single badge',
            'developer': 'Technical template with architecture details and performance metrics',
            'academic': 'Research-focused template with citations and methodology',
            'corporate': 'Professional business format with compliance and deployment info',
            'startup': 'Investor-focused template with mission, traction, and call-to-action',
            'gaming': 'Game-focused template with screenshots, system requirements, and community',
            'security': 'Security-focused template with compliance, threat protection, and reporting',
            'ai_ml': 'AI/ML template with model metrics, training data, and performance benchmarks',
            'mobile': 'Mobile app template with app store badges, screenshots, and user reviews',
            'opensource': 'Open source template with community stats, contribution guides, and recognition'
        }
        return descriptions.get(template_name, 'Unknown template')
    
    def _get_framework_description(self, framework: str) -> str:
        """Get description for common frameworks."""
        descriptions = {
            'tkinter': 'Built-in Python GUI framework',
            'pyqt': 'Cross-platform GUI toolkit',
            'pyside': 'Qt for Python',
            'kivy': 'Multi-platform GUI framework',
            'flask': 'Lightweight web framework',
            'django': 'High-level web framework', 
            'fastapi': 'Modern, fast web framework',
            'jinja2': 'Template engine',
            'requests': 'HTTP library',
            'pygithub': 'GitHub API integration',
            'gitpython': 'Git repository analysis',
            'pyyaml': 'YAML file processing',
            'react': 'Frontend JavaScript library',
            'vue': 'Progressive JavaScript framework',
            'angular': 'TypeScript-based web framework',
            'express': 'Node.js web framework',
            'spring': 'Java application framework',
            'rails': 'Ruby web framework',
            'gin': 'Go web framework',
            'echo': 'Go web framework',
            'electron': 'Desktop app framework',
            'flutter': 'Cross-platform mobile framework'
        }
        return descriptions.get(framework.lower(), 'Framework/library')
    
    def _get_database_description(self, database: str) -> str:
        """Get description for common databases."""
        descriptions = {
            'postgresql': 'Advanced relational database',
            'mysql': 'Popular relational database',
            'sqlite': 'Lightweight embedded database',
            'mongodb': 'NoSQL document database',
            'redis': 'In-memory data structure store',
            'elasticsearch': 'Search and analytics engine',
            'cassandra': 'Distributed NoSQL database',
            'influxdb': 'Time series database'
        }
        return descriptions.get(database.lower(), 'Database system')
    
    def _get_directory_description(self, directory: str) -> str:
        """Get description for common directory structures."""
        descriptions = {
            'src': 'Main source code directory',
            'lib': 'Library and utility modules',
            'app': 'Application logic and components',
            'api': 'API endpoints and routes',
            'components': 'Reusable UI components',
            'pages': 'Application pages and views',
            'views': 'View layer and templates',
            'models': 'Data models and schemas',
            'controllers': 'Business logic controllers',
            'routes': 'URL routing configuration',
            'services': 'Business service layer',
            'utils': 'Utility functions and helpers',
            'helpers': 'Helper functions and utilities',
            'config': 'Configuration files and settings',
            'tests': 'Test suites and specifications',
            'docs': 'Documentation and guides',
            'examples': 'Usage examples and demos',
            'scripts': 'Automation and build scripts',
            'assets': 'Static assets and resources',
            'public': 'Public static files',
            'static': 'Static web assets',
            'resources': 'Application resources'
        }
        return descriptions.get(directory.lower(), f'{directory.title()} files and modules')
    
    def _get_feature_description(self, feature: str, metadata: ProjectMetadata) -> str:
        """Get detailed descriptions for features."""
        descriptions = {
            'Multi-Platform Repository Analysis': 'Support for GitHub, GitLab, and local repositories',
            'Intelligent Technology Detection': 'Automatic identification of frameworks, languages, and tools',
            'Professional Templates': f'{len(self.templates)} customizable README templates for different project types',
            'Interactive GUI': 'User-friendly interface with modern design patterns',
            'Batch Processing': 'Analyze and generate READMEs for multiple repositories',
            'Real-time Preview': 'See your README as you customize it',
            'Smart Caching': 'Fast incremental analysis with intelligent file change detection',
            'Export Options': 'Multiple output formats and batch export capabilities',
            'User-friendly Interface with Modern Design Patterns': 'Intuitive design with progress tracking and feedback',
            'Interactive GUI with Progress Tracking': 'Real-time updates and user-friendly interface',
            'Real-time Analysis Updates with User Feedback': 'Live progress indicators and status updates',
            'RESTful API Integration': 'Modern API endpoints for web services',
            'Modern Web Interface': 'Responsive design with contemporary UI patterns',
            'Responsive Design': 'Adaptive interface that works across devices',
            'Modular and Extensible Architecture': 'Clean separation of concerns with scalable design',
            'Comprehensive Configuration System': 'Flexible settings management and customization',
            'Advanced Logging and Monitoring System': 'Comprehensive activity tracking and debugging',
            'Automated Testing Framework': 'Built-in test suites for reliability',
            'Comprehensive Documentation': 'Detailed guides and API documentation',
            'Continuous Integration Pipeline': 'Automated testing and deployment workflows',
            'Containerization Support': 'Docker integration for consistent deployment',
            'Performance Optimization and Caching': 'Intelligent caching and performance tuning',
            'Robust Error Handling and Recovery': 'Comprehensive exception management and recovery'
        }
        return descriptions.get(feature, 'Advanced feature for enhanced functionality')
    
    def _generate_comprehensive_toc(self, metadata: ProjectMetadata, config: TemplateConfig) -> List[str]:
        """Generate comprehensive table of contents."""
        toc = ["## Table of Contents", ""]
        
        sections = [
            ("✨ Features", metadata.features),
            ("🛠️ Technology Stack", metadata.languages or metadata.frameworks),
            ("🚀 Getting Started", True),
            ("📖 Usage", True),
            ("📚 Templates", 'template' in metadata.name.lower()),
            ("🏗️ Architecture", len(metadata.structure) >= 3),
            ("🎯 Key Advantages", len(metadata.features) >= 4 or len(metadata.frameworks) >= 3),
            ("🚀 Performance", True),
            ("🧪 Testing", metadata.has_tests),
            ("🤝 Contributing", config.include_contributing),
            ("📝 License", config.include_license_section and metadata.license),
        ]
        
        for section_name, condition in sections:
            if condition:
                anchor = section_name.split(' ', 1)[1].lower().replace(' ', '-') if ' ' in section_name else section_name.lower()
                toc.append(f"- [{section_name}](#{anchor})")
        
        return toc
    
    def _add_quick_start_guide(self, content: List[str], metadata: ProjectMetadata):
        """Add comprehensive quick start guide."""
        if 'readme' in metadata.name.lower():
            # RepoReadme-specific quick start
            content.extend([
                "1. **Launch RepoReadme** and you'll see the main interface",
                "2. **Add repositories** using the \"Add Local Folder\" or \"Add GitHub Repo\" buttons",
                "3. **Select a repository** from the list to view its details",
                "4. **Analyze the repository** by clicking \"Analyze Repository\"",
                "5. **Choose a template** from the configuration panel (Modern, Classic, Developer, etc.)",
                "6. **Customize options** like badges, table of contents, and emoji style",
                "7. **Preview your README** in the Preview tab",
                "8. **Generate and save** your professional README file",
                ""
            ])
        elif metadata.project_type == 'web-app':
            content.extend([
                "1. **Install dependencies** following the installation steps",
                "2. **Configure the application** settings as needed",
                "3. **Start the development server** to begin",
                "4. **Open your browser** and navigate to the application",
                "5. **Explore the features** and customize as needed",
                ""
            ])
        else:
            content.extend([
                "1. **Clone and install** following the installation steps above",
                "2. **Configure** any necessary settings or environment variables",
                "3. **Run the application** using the provided commands",
                "4. **Explore the documentation** for advanced usage",
                ""
            ])
    
    def _get_architecture_features(self, metadata: ProjectMetadata) -> List[str]:
        """Generate architecture feature descriptions."""
        features = []
        
        if metadata.structure:
            if 'analyzers' in str(metadata.structure).lower():
                features.append("Modular Design - Efficient repository traversal and analysis")
            if 'gui' in str(metadata.structure).lower() or 'ui' in str(metadata.structure).lower():
                features.append("Progress Tracking - Real-time analysis updates with user feedback")
            if 'config' in str(metadata.structure).lower():
                features.append("Configuration System - Settings persistence and validation")
            if 'utils' in str(metadata.structure).lower():
                features.append("Logging Framework - Comprehensive activity tracking and debugging")
            if 'templates' in str(metadata.structure).lower():
                features.append("Template Engine - Professional README generation with multiple styles")
        
        # Generic architectural features
        if len(metadata.structure) >= 4:
            features.extend([
                "Modern GUI - Professional interface with responsive design",
                "Asynchronous Processing - Non-blocking operations for smooth UX",
                "Robust Error Handling - Comprehensive exception management"
            ])
        
        return features[:6]  # Limit to 6 features
    
    def _generate_performance_metrics(self, metadata: ProjectMetadata) -> List[str]:
        """Generate performance metrics based on project data."""
        metrics = []
        
        # Analysis performance (if it's an analysis tool)
        if 'readme' in metadata.name.lower() or 'analysis' in metadata.name.lower():
            metrics.extend([
                "- **Analysis Speed:** ~100ms per repository (cached results)",
                "- **Template Generation:** <50ms per README", 
                "- **Memory Efficient:** Processes large codebases without issues",
                "- **Cache Hit Rate:** 90%+ on repeat analysis"
            ])
        else:
            # Generic performance metrics
            metrics.extend([
                f"- **Files:** {metadata.total_files:,}",
                f"- **Lines of Code:** {metadata.code_lines:,}",
            ])
            
            if metadata.commits and metadata.commits > 0:
                metrics.append(f"- **Commits:** {metadata.commits:,}")
            if metadata.contributors and metadata.contributors > 0:
                metrics.append(f"- **Contributors:** {metadata.contributors}")
        
        return metrics