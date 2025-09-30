"""
README to Project Template Converter

Converts generated README files into portfolio project template JSON files
following the format specified in /project-templates/.
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

try:
    from .analyzers.repository_analyzer import ProjectMetadata
except ImportError:
    from analyzers.repository_analyzer import ProjectMetadata


@dataclass
class ProjectTemplate:
    """Data structure for project template JSON files."""
    id: str
    title: str
    slug: str
    summary: str
    description: str
    category: str
    status: str
    dateCreated: str
    dateUpdated: str
    technologies: List[Dict[str, str]]
    architecture: str
    technicalDetails: List[Dict[str, str]]
    images: List[Dict[str, Any]]
    links: List[Dict[str, str]]
    keyPoints: List[str]


class ReadmeToTemplateConverter:
    """Converts README content to project template JSON format."""
    
    # Category mapping based on technologies and frameworks
    CATEGORY_MAPPING = {
        'react': 'Web Development',
        'vue': 'Web Development', 
        'angular': 'Web Development',
        'svelte': 'Web Development',
        'next.js': 'Web Development',
        'nextjs': 'Web Development',
        'nuxt.js': 'Web Development',
        'gatsby': 'Web Development',
        'html': 'Web Development',
        'css': 'Web Development',
        'javascript': 'Web Development',
        'typescript': 'Web Development',
        'node.js': 'Web Development',
        'express': 'API',
        'fastapi': 'API',
        'flask': 'API',
        'django': 'API',
        'spring': 'API',
        'rails': 'API',
        'unity': 'Game Development',
        'unreal': 'Game Development',
        'godot': 'Game Development',
        'c#': 'Desktop Application',
        '.net': 'Desktop Application',
        'wpf': 'Desktop Application',
        'winforms': 'Desktop Application',
        'electron': 'Desktop Application',
        'tauri': 'Desktop Application',
        'react-native': 'Mobile App',
        'flutter': 'Mobile App',
        'ionic': 'Mobile App',
        'xamarin': 'Mobile App',
        'swift': 'Mobile App',
        'kotlin': 'Mobile App',
    }
    
    # Technology icon mapping
    TECH_ICONS = {
        'react': 'logos:react',
        'vue': 'logos:vue', 
        'angular': 'logos:angular-icon',
        'svelte': 'logos:svelte-icon',
        'next.js': 'logos:nextjs-icon',
        'nextjs': 'logos:nextjs-icon',
        'typescript': 'logos:typescript-icon',
        'javascript': 'logos:javascript',
        'python': 'logos:python',
        'java': 'logos:java',
        'c#': 'logos:c-sharp',
        'c++': 'logos:cplusplus',
        'go': 'logos:go',
        'rust': 'logos:rust',
        'php': 'logos:php',
        'ruby': 'logos:ruby',
        'node.js': 'logos:nodejs-icon',
        'express': 'logos:express',
        'django': 'logos:django-icon',
        'flask': 'logos:flask',
        'fastapi': 'skill-icons:fastapi',
        '.net': 'logos:dotnet',
        'unity': 'logos:unity',
        'html': 'logos:html-5',
        'css': 'logos:css-3',
        'tailwind': 'logos:tailwindcss-icon',
        'bootstrap': 'logos:bootstrap',
        'sass': 'logos:sass',
        'postgresql': 'logos:postgresql',
        'mysql': 'logos:mysql-icon',
        'mongodb': 'logos:mongodb-icon',
        'redis': 'logos:redis',
        'sqlite': 'logos:sqlite',
        'docker': 'logos:docker-icon',
        'git': 'logos:git-icon',
        'github': 'logos:github-icon',
        'aws': 'logos:aws',
        'azure': 'logos:azure-icon',
        'gcp': 'logos:google-cloud',
        'firebase': 'logos:firebase',
        'vercel': 'logos:vercel-icon',
        'netlify': 'logos:netlify-icon',
        'figma': 'logos:figma',
    }
    
    def __init__(self):
        """Initialize the converter."""
        self.project_templates_dir = Path(__file__).parent.parent / "project-templates"
    
    def convert_readme_to_template(
        self, 
        readme_content: str, 
        metadata: ProjectMetadata,
        repo_url: str = None,
        demo_url: str = None
    ) -> ProjectTemplate:
        """Convert README content and metadata to project template format."""
        
        # Generate unique ID from project name
        project_id = self._generate_project_id(metadata.name)
        
        # Determine project category
        category = self._determine_category(metadata)
        
        # Extract key information from README
        summary = self._extract_summary(readme_content, metadata.description)
        description = self._clean_description(metadata.description)
        key_points = self._extract_key_points(readme_content, metadata)
        technical_details = self._extract_technical_details(readme_content, metadata)
        
        # Build technology stack
        technologies = self._build_technology_stack(metadata)
        
        # Determine architecture
        architecture = self._determine_architecture(metadata, category)
        
        # Generate links
        links = self._generate_links(repo_url, demo_url, metadata.name)
        
        # Generate images placeholder
        images = self._generate_image_placeholders(metadata.name)
        
        # Create dates
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return ProjectTemplate(
            id=project_id,
            title=metadata.name,
            slug=project_id,
            summary=summary,
            description=description,
            category=category,
            status="Completed",
            dateCreated=current_date,
            dateUpdated=current_date,
            technologies=technologies,
            architecture=architecture,
            technicalDetails=technical_details,
            images=images,
            links=links,
            keyPoints=key_points
        )
    
    def _generate_project_id(self, name: str) -> str:
        """Generate kebab-case project ID from name."""
        # Remove special characters and convert to lowercase
        clean_name = re.sub(r'[^\w\s-]', '', name.lower())
        # Replace spaces with hyphens
        return re.sub(r'[\s_]+', '-', clean_name).strip('-')
    
    def _determine_category(self, metadata: ProjectMetadata) -> str:
        """Determine project category based on metadata."""
        # Check frameworks and technologies
        all_tech = []
        if metadata.frameworks:
            all_tech.extend([f.lower() for f in metadata.frameworks])
        if metadata.primary_language:
            all_tech.append(metadata.primary_language.lower())
        if metadata.dependencies:
            all_tech.extend([dep.lower() for dep in metadata.dependencies[:10]])  # Limit to avoid too many
        
        # Find category based on technology mapping
        for tech in all_tech:
            if tech in self.CATEGORY_MAPPING:
                return self.CATEGORY_MAPPING[tech]
        
        # Default based on primary language
        if metadata.primary_language:
            lang = metadata.primary_language.lower()
            if lang in ['javascript', 'typescript', 'html', 'css']:
                return "Web Development"
            elif lang in ['python', 'java', 'c#', 'go', 'rust']:
                if any('api' in str(f).lower() or 'server' in str(f).lower() 
                       for f in (metadata.frameworks or [])):
                    return "API"
                else:
                    return "Desktop Application"
            elif lang in ['swift', 'kotlin', 'dart']:
                return "Mobile App"
        
        return "Web Development"  # Default fallback
    
    def _extract_summary(self, readme_content: str, description: str) -> str:
        """Extract a brief summary for the project."""
        if description and len(description) <= 100:
            return description
        
        # Try to find a brief description in README
        lines = readme_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('![') and len(line) <= 100:
                # Clean up markdown formatting
                clean_line = re.sub(r'[*_`]', '', line)
                if len(clean_line) > 20:  # Ensure it's substantial
                    return clean_line
        
        # Fallback to truncated description
        if description:
            return description[:97] + "..." if len(description) > 100 else description
        
        return f"A {self._determine_category(metadata).lower()} project"
    
    def _clean_description(self, description: str) -> str:
        """Clean and format description for template."""
        if not description:
            return "A comprehensive project showcasing modern development practices and technologies."
        
        # Remove excessive newlines and clean up formatting
        cleaned = re.sub(r'\n\s*\n', '\n\n', description.strip())
        
        # Ensure it's substantial
        if len(cleaned) < 50:
            cleaned += f"\n\nThis project demonstrates proficiency in modern development practices and provides a solid foundation for similar applications."
        
        return cleaned
    
    def _extract_key_points(self, readme_content: str, metadata: ProjectMetadata) -> List[str]:
        """Extract key points from README content and metadata."""
        key_points = []
        
        # Extract from features if available
        if metadata.features:
            for feature in metadata.features[:4]:  # Limit to 4 main features
                key_points.append(f"✨ {feature}")
        
        # Add technology highlights
        if metadata.primary_language:
            key_points.append(f"🚀 Built with {metadata.primary_language.title()}")
        
        if metadata.frameworks:
            if len(metadata.frameworks) == 1:
                key_points.append(f"⚡ Powered by {metadata.frameworks[0]}")
            else:
                key_points.append(f"🛠️ Modern stack: {', '.join(metadata.frameworks[:3])}")
        
        # Add architecture/design points
        if any(term in readme_content.lower() for term in ['responsive', 'mobile', 'cross-platform']):
            key_points.append("📱 Responsive design and cross-platform compatibility")
        
        if any(term in readme_content.lower() for term in ['api', 'rest', 'graphql']):
            key_points.append("🔗 RESTful API integration")
        
        if any(term in readme_content.lower() for term in ['docker', 'container', 'deployment']):
            key_points.append("🐳 Containerized deployment ready")
        
        # Ensure we have at least 4 key points
        while len(key_points) < 4:
            if len(key_points) == 0:
                key_points.append("🎯 Modern architecture and clean code")
            elif len(key_points) == 1:
                key_points.append("⚡ Optimized performance and user experience")
            elif len(key_points) == 2:
                key_points.append("🔒 Secure and scalable implementation")
            elif len(key_points) == 3:
                key_points.append("📚 Comprehensive documentation and testing")
        
        return key_points[:8]  # Limit to 8 points max
    
    def _extract_technical_details(self, readme_content: str, metadata: ProjectMetadata) -> List[Dict[str, str]]:
        """Extract technical implementation details."""
        details = []
        
        # Look for code blocks and technical sections
        code_pattern = r'```(\w+)?\n(.*?)\n```'
        code_matches = re.findall(code_pattern, readme_content, re.DOTALL)
        
        for i, (lang, code) in enumerate(code_matches[:3]):  # Limit to 3 examples
            if code.strip() and len(code.strip()) > 20:
                title = f"{lang.title() if lang else 'Code'} Implementation"
                description = f"Core implementation showcasing {lang if lang else 'programming'} best practices"
                details.append({
                    "title": title,
                    "description": description,
                    "codeSnippet": code.strip()[:300] + ("..." if len(code.strip()) > 300 else "")
                })
        
        # Add architecture detail if not enough code examples
        if len(details) < 2:
            if metadata.frameworks:
                details.append({
                    "title": "Architecture Design",
                    "description": f"Implements {metadata.frameworks[0]} architecture with modern design patterns",
                    "codeSnippet": f"// {metadata.frameworks[0]} implementation\n// Clean architecture with separation of concerns"
                })
        
        # Add default technical detail if none found
        if not details:
            details.append({
                "title": "Core Implementation",
                "description": "Modern implementation following industry best practices",
                "codeSnippet": f"// {metadata.primary_language or 'Modern'} implementation\n// Scalable and maintainable code structure"
            })
        
        return details
    
    def _build_technology_stack(self, metadata: ProjectMetadata) -> List[Dict[str, str]]:
        """Build technology stack array with icons and categories."""
        technologies = []
        
        # Add primary language
        if metadata.primary_language:
            lang = metadata.primary_language.lower()
            technologies.append({
                "name": metadata.primary_language.title(),
                "icon": self.TECH_ICONS.get(lang, "mdi:code"),
                "category": "Language"
            })
        
        # Add frameworks
        if metadata.frameworks:
            for framework in metadata.frameworks[:4]:  # Limit to prevent clutter
                fw_lower = framework.lower()
                category = "Framework"
                
                # Determine more specific category
                if any(term in fw_lower for term in ['react', 'vue', 'angular', 'svelte']):
                    category = "Frontend"
                elif any(term in fw_lower for term in ['express', 'flask', 'django', 'spring']):
                    category = "Backend"
                elif any(term in fw_lower for term in ['tailwind', 'bootstrap', 'sass', 'css']):
                    category = "Styling"
                
                technologies.append({
                    "name": framework,
                    "icon": self.TECH_ICONS.get(fw_lower, "mdi:framework"),
                    "category": category
                })
        
        # Add key dependencies
        if metadata.dependencies:
            db_deps = [dep for dep in metadata.dependencies if any(db in dep.lower() for db in ['sql', 'mongo', 'redis', 'database'])]
            for dep in db_deps[:2]:  # Limit database deps
                dep_lower = dep.lower()
                technologies.append({
                    "name": dep,
                    "icon": self.TECH_ICONS.get(dep_lower, "mdi:database"),
                    "category": "Database"
                })
        
        # Ensure we have at least 3 technologies
        while len(technologies) < 3:
            if not any(tech["category"] == "Frontend" for tech in technologies):
                technologies.append({
                    "name": "HTML5",
                    "icon": "logos:html-5",
                    "category": "Frontend"
                })
            elif not any(tech["category"] == "Styling" for tech in technologies):
                technologies.append({
                    "name": "CSS3", 
                    "icon": "logos:css-3",
                    "category": "Styling"
                })
            else:
                technologies.append({
                    "name": "Git",
                    "icon": "logos:git-icon", 
                    "category": "Tools"
                })
        
        return technologies
    
    def _determine_architecture(self, metadata: ProjectMetadata, category: str) -> str:
        """Determine project architecture based on category and technologies."""
        if category == "Web Development":
            if metadata.frameworks and any('next' in f.lower() for f in metadata.frameworks):
                return "Next.js App Router with React Context API"
            elif metadata.frameworks and any('react' in f.lower() for f in metadata.frameworks):
                return "Component-based React architecture with hooks"
            elif metadata.frameworks and any('vue' in f.lower() for f in metadata.frameworks):
                return "Vue.js composition API with reactive state management"
            else:
                return "Modern web architecture with responsive design"
        
        elif category == "Desktop Application":
            if metadata.primary_language and 'c#' in metadata.primary_language.lower():
                return "Model-View-ViewModel (MVVM) architecture"
            else:
                return "Cross-platform desktop architecture"
        
        elif category == "Mobile App":
            if metadata.frameworks and any('react' in f.lower() for f in metadata.frameworks):
                return "React Native with Expo framework"
            else:
                return "Native mobile architecture with modern UI patterns"
        
        elif category == "API":
            return "RESTful API with MVC architectural pattern"
        
        elif category == "Game Development":
            return "Component-based game architecture with Unity"
        
        else:
            return "Modular architecture with clean code principles"
    
    def _generate_links(self, repo_url: str, demo_url: str, project_name: str) -> List[Dict[str, str]]:
        """Generate project links."""
        links = []
        
        if repo_url:
            links.append({
                "type": "github",
                "url": repo_url,
                "label": "Source Code"
            })
        
        if demo_url:
            links.append({
                "type": "demo", 
                "url": demo_url,
                "label": "Live Demo"
            })
        
        # If no links provided, create placeholders
        if not links:
            project_slug = self._generate_project_id(project_name)
            links.append({
                "type": "github",
                "url": f"https://github.com/dev-alt/{project_slug}",
                "label": "Source Code"
            })
        
        return links
    
    def _generate_image_placeholders(self, project_name: str) -> List[Dict[str, Any]]:
        """Generate image placeholders."""
        clean_name = project_name.replace(' ', '')
        
        return [
            {
                "url": f"/Projects/{clean_name}_Main.png",
                "alt": f"{project_name} Main Interface",
                "width": 1920,
                "height": 1080,
                "isFeatured": True
            }
        ]
    
    def save_template(self, template: ProjectTemplate, output_path: str = None) -> str:
        """Save template to JSON file."""
        if not output_path:
            # Default to project-templates directory
            filename = f"{template.id}.json"
            output_path = str(self.project_templates_dir / filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to dict and save
        template_dict = asdict(template)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template_dict, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def convert_and_save(
        self, 
        readme_content: str,
        metadata: ProjectMetadata,
        output_path: str = None,
        repo_url: str = None,
        demo_url: str = None
    ) -> Tuple[ProjectTemplate, str]:
        """Convert README to template and save to file."""
        template = self.convert_readme_to_template(readme_content, metadata, repo_url, demo_url)
        saved_path = self.save_template(template, output_path)
        return template, saved_path


def convert_readme_to_project_template(
    readme_content: str,
    metadata: ProjectMetadata,
    output_path: str = None,
    repo_url: str = None,
    demo_url: str = None
) -> Tuple[ProjectTemplate, str]:
    """Convenience function to convert README to project template."""
    converter = ReadmeToTemplateConverter()
    return converter.convert_and_save(readme_content, metadata, output_path, repo_url, demo_url)