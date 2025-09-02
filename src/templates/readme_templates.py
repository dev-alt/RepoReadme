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
            'corporate': self._generate_corporate_template
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
        """Generate modern README template with badges, sections, and visual elements."""
        
        # Header section with title and description
        content = []
        
        # Title with emoji
        emoji = "🚀" if config.emoji_style == "unicode" else ""
        content.append(f"# {emoji} {metadata.name}")
        content.append("")
        
        if metadata.description:
            content.append(f"> {metadata.description}")
            content.append("")
        
        # Badges section
        if config.include_badges:
            badges = self._generate_badges(metadata, config)
            if badges:
                content.extend(badges)
                content.append("")
        
        # Table of Contents
        if config.include_toc:
            toc = self._generate_table_of_contents(metadata, config)
            content.extend(toc)
            content.append("")
        
        # Features section
        if metadata.features:
            content.append("## ✨ Features")
            content.append("")
            for feature in metadata.features:
                content.append(f"- {feature}")
            content.append("")
        
        # Technology Stack
        if metadata.languages or metadata.frameworks:
            content.append("## 🛠️ Technology Stack")
            content.append("")
            
            if metadata.primary_language:
                content.append(f"**Primary Language:** {metadata.primary_language.title()}")
                content.append("")
            
            if metadata.frameworks:
                content.append("**Frameworks & Libraries:**")
                for framework in metadata.frameworks:
                    content.append(f"- {framework.title()}")
                content.append("")
            
            if metadata.databases:
                content.append("**Databases:**")
                for db in metadata.databases:
                    content.append(f"- {db.title()}")
                content.append("")
            
            if metadata.tools:
                content.append("**DevOps & Tools:**")
                for tool in metadata.tools:
                    content.append(f"- {tool.title()}")
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
        
        # Installation
        content.append("### Installation")
        content.append("")
        content.append("1. Clone the repository")
        content.append("```bash")
        if metadata.repository_url:
            content.append(f"git clone {metadata.repository_url}")
        else:
            content.append(f"git clone https://github.com/yourusername/{metadata.name}.git")
        content.append(f"cd {metadata.name}")
        content.append("```")
        content.append("")
        
        content.append("2. Install dependencies")
        content.append("```bash")
        if metadata.installation_commands:
            content.append(metadata.installation_commands[0])
        else:
            if metadata.primary_language == 'python':
                content.append("pip install -r requirements.txt")
            elif metadata.primary_language == 'javascript':
                content.append("npm install")
        content.append("```")
        content.append("")
        
        content.append("3. Run the application")
        content.append("```bash")
        if len(metadata.installation_commands) > 1:
            content.append(metadata.installation_commands[1])
        else:
            if metadata.primary_language == 'python':
                content.append("python main.py")
            elif metadata.primary_language == 'javascript':
                content.append("npm start")
        content.append("```")
        content.append("")
        
        # Usage section
        if metadata.usage_examples:
            content.append("## 📖 Usage")
            content.append("")
            for i, example in enumerate(metadata.usage_examples[:3]):
                content.append(f"### Example {i+1}")
                content.append("")
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
        
        # Project Structure
        if metadata.structure:
            content.append("## 📁 Project Structure")
            content.append("")
            content.append("```")
            content.append(f"{metadata.name}/")
            for directory, info in metadata.structure.items():
                if info.get('files', 0) > 0:
                    content.append(f"├── {directory}/")
            content.append("├── README.md")
            if metadata.license:
                content.append("└── LICENSE")
            content.append("```")
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
        
        # Contributing
        if config.include_contributing:
            content.append("## 🤝 Contributing")
            content.append("")
            content.append("Contributions are welcome! Please feel free to submit a Pull Request.")
            content.append("")
            content.append("1. Fork the project")
            content.append("2. Create your feature branch (`git checkout -b feature/AmazingFeature`)")
            content.append("3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)")
            content.append("4. Push to the branch (`git push origin feature/AmazingFeature`)")
            content.append("5. Open a Pull Request")
            content.append("")
        
        # License
        if config.include_license_section and metadata.license:
            content.append("## 📝 License")
            content.append("")
            content.append(f"This project is licensed under the {metadata.license} License - see the [LICENSE](LICENSE) file for details.")
            content.append("")
        
        # Acknowledgments
        if config.include_acknowledgments:
            content.append("## 🙏 Acknowledgments")
            content.append("")
            content.append("- Thanks to all contributors who helped with this project")
            if metadata.frameworks:
                content.append(f"- Built with {', '.join(metadata.frameworks)}")
            content.append("- Inspired by the open source community")
            content.append("")
        
        # Footer
        content.append("---")
        content.append("")
        content.append(f"**{metadata.name}** - Generated with ❤️ by [RepoReadme](https://github.com/yourusername/reporeadme)")
        
        return "\n".join(content)
    
    def _generate_classic_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate classic README template with traditional structure."""
        content = []
        
        # Simple header
        content.append(f"# {metadata.name}")
        content.append("")
        
        if metadata.description:
            content.append(metadata.description)
            content.append("")
        
        # Installation
        content.append("## Installation")
        content.append("")
        if metadata.installation_commands:
            for cmd in metadata.installation_commands[:2]:
                content.append(f"    {cmd}")
        content.append("")
        
        # Usage
        content.append("## Usage")
        content.append("")
        if metadata.usage_examples:
            content.append(metadata.usage_examples[0])
        else:
            content.append("Add usage instructions here.")
        content.append("")
        
        # Features
        if metadata.features:
            content.append("## Features")
            content.append("")
            for feature in metadata.features:
                content.append(f"* {feature}")
            content.append("")
        
        # License
        if metadata.license:
            content.append("## License")
            content.append("")
            content.append(f"Licensed under {metadata.license}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_minimalist_template(self, metadata: ProjectMetadata, config: TemplateConfig) -> str:
        """Generate minimalist README template with clean, simple design."""
        content = []
        
        content.append(f"# {metadata.name}")
        if metadata.description:
            content.append(f"{metadata.description}")
        content.append("")
        
        content.append("## Install")
        content.append("```bash")
        if metadata.installation_commands:
            content.append(metadata.installation_commands[0])
        content.append("```")
        content.append("")
        
        content.append("## Use")
        content.append("```bash")
        if len(metadata.installation_commands) > 1:
            content.append(metadata.installation_commands[1])
        content.append("```")
        content.append("")
        
        if metadata.license:
            content.append(f"## License")
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
            'modern': 'Contemporary design with badges, emojis, and comprehensive sections',
            'classic': 'Traditional README format with essential information',
            'minimalist': 'Clean, simple design with minimal content',
            'developer': 'Technical focus with detailed development information',
            'academic': 'Research project format with citations and methodology',
            'corporate': 'Professional business format with compliance and deployment info'
        }
        return descriptions.get(template_name, 'Unknown template')