#!/usr/bin/env python3
"""
CV Generator

Generates professional CVs/resumes from GitHub profile data in multiple formats and styles.
Builds on the existing GitHubProfileBuilder to create targeted resume documents.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import tempfile

try:
    from .profile_builder import GitHubProfile, ProfileExporter
    from .utils.logger import get_logger
except ImportError:
    from profile_builder import GitHubProfile, ProfileExporter
    from utils.logger import get_logger


@dataclass
class CVConfig:
    """Configuration for CV generation."""
    
    # CV Style and Format
    cv_style: str = "modern"  # modern, classic, minimal, technical, creative
    cv_format: str = "html"   # html, pdf, json, docx
    
    # Content Selection
    include_summary: bool = True
    include_skills: bool = True
    include_projects: bool = True
    include_experience: bool = True
    include_education: bool = False
    include_certifications: bool = False
    include_achievements: bool = True
    include_contact_info: bool = True
    
    # Project Selection
    max_featured_projects: int = 6
    min_stars_for_projects: int = 1
    prioritize_recent_projects: bool = True
    group_projects_by_type: bool = True
    
    # Skills Configuration
    max_skills_to_show: int = 12
    group_skills_by_category: bool = True
    show_skill_proficiency: bool = True
    
    # Customization
    personal_info: Dict[str, str] = field(default_factory=dict)
    custom_sections: List[Dict[str, Any]] = field(default_factory=list)
    target_role: Optional[str] = None
    target_industry: Optional[str] = None
    
    # Export Options
    include_portfolio_link: bool = True
    include_github_stats: bool = True
    use_professional_language: bool = True


@dataclass
class CVData:
    """Structured CV data for different output formats."""
    
    # Personal Information
    personal_info: Dict[str, str] = field(default_factory=dict)
    
    # Professional Summary
    professional_summary: str = ""
    objective: str = ""
    
    # Skills
    technical_skills: Dict[str, List[str]] = field(default_factory=dict)
    soft_skills: List[str] = field(default_factory=list)
    skill_proficiency: Dict[str, str] = field(default_factory=dict)
    
    # Work Experience (synthesized from projects)
    work_experience: List[Dict[str, Any]] = field(default_factory=list)
    
    # Projects
    featured_projects: List[Dict[str, Any]] = field(default_factory=list)
    project_categories: Dict[str, List[Dict]] = field(default_factory=dict)
    
    # Education & Certifications
    education: List[Dict[str, Any]] = field(default_factory=list)
    certifications: List[Dict[str, Any]] = field(default_factory=list)
    
    # Achievements & Recognition
    achievements: List[str] = field(default_factory=list)
    github_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    generated_date: str = ""
    target_role: Optional[str] = None
    cv_style: str = "modern"


class CVGenerator:
    """Generates professional CVs from GitHub profile data."""
    
    def __init__(self, config: CVConfig = None):
        """Initialize the CV generator."""
        self.config = config or CVConfig()
        self.logger = get_logger()
        
    def generate_cv_from_profile(self, profile: GitHubProfile, 
                               additional_info: Dict[str, Any] = None) -> CVData:
        """Generate CV data from GitHub profile."""
        self.logger.info(f"Generating CV for {profile.username}")
        
        cv_data = CVData()
        cv_data.generated_date = datetime.now().isoformat()
        cv_data.target_role = self.config.target_role
        cv_data.cv_style = self.config.cv_style
        
        # Merge additional personal information
        additional_info = additional_info or {}
        
        # Generate each section
        cv_data.personal_info = self._generate_personal_info(profile, additional_info)
        cv_data.professional_summary = self._generate_professional_summary(profile)
        cv_data.objective = self._generate_objective(profile)
        
        cv_data.technical_skills = self._generate_technical_skills(profile)
        cv_data.soft_skills = self._generate_soft_skills(profile)
        cv_data.skill_proficiency = self._generate_skill_proficiency(profile)
        
        cv_data.work_experience = self._generate_work_experience(profile, additional_info)
        cv_data.featured_projects = self._generate_featured_projects(profile)
        cv_data.project_categories = self._generate_project_categories(profile)
        
        cv_data.education = additional_info.get('education', [])
        cv_data.certifications = additional_info.get('certifications', [])
        
        cv_data.achievements = self._generate_achievements(profile)
        cv_data.github_stats = self._generate_github_stats(profile)
        
        self.logger.info(f"CV generated successfully with {len(cv_data.featured_projects)} projects")
        return cv_data
    
    def _generate_personal_info(self, profile: GitHubProfile, 
                              additional_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate personal information section."""
        info = {
            'name': profile.name or profile.username,
            'username': profile.username,
            'email': profile.email or additional_info.get('email', ''),
            'phone': additional_info.get('phone', ''),
            'location': profile.location or additional_info.get('location', ''),
            'website': profile.website or additional_info.get('website', ''),
            'linkedin': additional_info.get('linkedin', ''),
            'github': profile.profile_url,
            'bio': profile.bio or ''
        }
        
        # Add custom fields from config
        info.update(self.config.personal_info)
        
        # Filter out empty values
        return {k: v for k, v in info.items() if v}
    
    def _generate_professional_summary(self, profile: GitHubProfile) -> str:
        """Generate professional summary based on profile data."""
        if not self.config.include_summary:
            return ""
        
        experience_level = profile.experience_level.lower()
        developer_type = profile.developer_type.lower()
        
        # Count active languages and frameworks
        active_languages = len([lang for lang, pct in profile.languages_percentage.items() if pct > 5])
        total_projects = profile.original_repositories
        total_stars = profile.total_stars_received
        
        # Generate summary based on profile characteristics
        if experience_level in ['senior', 'lead']:
            experience_desc = "seasoned" if experience_level == "senior" else "lead"
        elif experience_level == 'mid-level':
            experience_desc = "experienced"
        else:
            experience_desc = "motivated"
        
        summary_parts = []
        
        # Opening statement
        if self.config.target_role:
            summary_parts.append(f"{experience_desc.capitalize()} {developer_type} developer focused on {self.config.target_role.lower()}")
        else:
            summary_parts.append(f"{experience_desc.capitalize()} {developer_type} developer")
        
        # Technical expertise
        if active_languages > 0:
            top_languages = list(profile.primary_languages[:3])
            if len(top_languages) > 1:
                langs_text = ", ".join(top_languages[:-1]) + f", and {top_languages[-1]}"
            else:
                langs_text = top_languages[0] if top_languages else "multiple programming languages"
            
            summary_parts.append(f"with expertise in {langs_text}")
        
        # Project portfolio
        if total_projects > 5:
            summary_parts.append(f"Maintained a portfolio of {total_projects} open-source projects")
            if total_stars > 10:
                summary_parts.append(f"earning {total_stars} stars from the developer community")
        
        # Specializations
        specializations = []
        if profile.has_web_projects:
            specializations.append("web applications")
        if profile.has_mobile_projects:
            specializations.append("mobile development")
        if profile.has_apis:
            specializations.append("API development")
        if profile.has_cli_tools:
            specializations.append("developer tools")
        if profile.has_libraries:
            specializations.append("library development")
        
        if specializations:
            if len(specializations) > 2:
                spec_text = ", ".join(specializations[:-1]) + f", and {specializations[-1]}"
            elif len(specializations) == 2:
                spec_text = f"{specializations[0]} and {specializations[1]}"
            else:
                spec_text = specializations[0]
            
            summary_parts.append(f"Specialized in {spec_text}")
        
        # Professional qualities
        qualities = []
        if profile.collaboration_score > 60:
            qualities.append("collaborative")
        if profile.innovation_score > 60:
            qualities.append("innovative")
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.7:
            qualities.append("documentation-focused")
        
        if qualities:
            summary_parts.append(f"Known for {' and '.join(qualities)} development practices")
        
        # Target industry alignment
        if self.config.target_industry:
            summary_parts.append(f"Seeking to apply technical skills in the {self.config.target_industry} industry")
        
        return ". ".join(summary_parts) + "."
    
    def _generate_objective(self, profile: GitHubProfile) -> str:
        """Generate career objective."""
        if not self.config.target_role:
            return ""
        
        return (f"Seeking a {self.config.target_role} position where I can leverage my "
               f"expertise in {', '.join(profile.primary_languages[:2])} and proven track record "
               f"of building {profile.original_repositories} open-source projects to drive "
               f"innovative solutions and contribute to team success.")
    
    def _generate_technical_skills(self, profile: GitHubProfile) -> Dict[str, List[str]]:
        """Generate categorized technical skills."""
        if not self.config.include_skills:
            return {}
        
        skills = defaultdict(list)
        
        # Programming Languages
        languages = []
        for lang, percentage in sorted(profile.languages_percentage.items(), 
                                     key=lambda x: x[1], reverse=True)[:self.config.max_skills_to_show]:
            if percentage > 2:  # Only include languages with significant usage
                if self.config.show_skill_proficiency:
                    if percentage >= 25:
                        level = "Expert"
                    elif percentage >= 15:
                        level = "Advanced"
                    elif percentage >= 5:
                        level = "Intermediate"
                    else:
                        level = "Basic"
                    languages.append(f"{lang} ({level})")
                else:
                    languages.append(lang)
        
        if languages:
            skills["Programming Languages"] = languages
        
        # Frameworks and Libraries (inferred from project types and languages)
        frameworks = []
        if "JavaScript" in profile.languages_used or "TypeScript" in profile.languages_used:
            if profile.has_web_projects:
                frameworks.extend(["React", "Node.js", "Express"])
        if "Python" in profile.languages_used:
            frameworks.extend(["Django", "Flask", "FastAPI"])
        if "Java" in profile.languages_used:
            frameworks.extend(["Spring Boot", "Spring Framework"])
        if "C#" in profile.languages_used:
            frameworks.extend([".NET", "ASP.NET Core"])
        
        # Add frameworks from profile data if available
        if hasattr(profile, 'frameworks_used'):
            frameworks.extend(list(profile.frameworks_used.keys())[:5])
        
        if frameworks:
            skills["Frameworks & Libraries"] = list(set(frameworks))[:8]
        
        # Development Tools
        tools = ["Git", "GitHub"]
        if profile.repositories_with_ci > 0:
            tools.extend(["CI/CD", "GitHub Actions"])
        if profile.repositories_with_docker > 0:
            tools.append("Docker")
        if profile.has_web_projects:
            tools.extend(["HTML/CSS", "REST APIs"])
        if profile.has_mobile_projects:
            tools.extend(["Mobile Development", "App Stores"])
        
        # Add tools from profile data if available
        if hasattr(profile, 'tools_used'):
            tools.extend(list(profile.tools_used.keys())[:5])
        
        if tools:
            skills["Development Tools"] = list(set(tools))[:10]
        
        # Databases (if available in profile)
        if hasattr(profile, 'databases_used') and profile.databases_used:
            skills["Databases"] = list(profile.databases_used.keys())[:6]
        
        # Methodologies
        methodologies = []
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.5:
            methodologies.append("Documentation")
        if profile.repositories_with_tests > 0:
            methodologies.append("Test-Driven Development")
        if profile.collaboration_score > 50:
            methodologies.append("Collaborative Development")
        if profile.original_repositories > 10:
            methodologies.append("Open Source Development")
        
        if methodologies:
            skills["Methodologies"] = methodologies
        
        return dict(skills)
    
    def _generate_soft_skills(self, profile: GitHubProfile) -> List[str]:
        """Generate soft skills based on profile analysis."""
        soft_skills = []
        
        # Infer soft skills from profile metrics
        if profile.collaboration_score > 60:
            soft_skills.extend(["Team Collaboration", "Code Review", "Mentoring"])
        
        if profile.innovation_score > 60:
            soft_skills.extend(["Problem Solving", "Creative Thinking", "Innovation"])
        
        if profile.total_forks_received > 20:
            soft_skills.append("Community Building")
        
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.7:
            soft_skills.extend(["Technical Writing", "Documentation"])
        
        if profile.original_repositories > 15:
            soft_skills.extend(["Self-Motivation", "Independent Learning"])
        
        if len(profile.languages_used) > 5:
            soft_skills.append("Adaptability")
        
        if profile.experience_level in ['Senior', 'Lead']:
            soft_skills.extend(["Leadership", "Project Management", "Strategic Planning"])
        
        # Add industry-specific soft skills
        if self.config.target_industry:
            if "fintech" in self.config.target_industry.lower():
                soft_skills.extend(["Attention to Detail", "Risk Assessment"])
            elif "healthcare" in self.config.target_industry.lower():
                soft_skills.extend(["Regulatory Compliance", "Data Privacy"])
            elif "education" in self.config.target_industry.lower():
                soft_skills.extend(["Training", "Communication"])
        
        return list(set(soft_skills))
    
    def _generate_skill_proficiency(self, profile: GitHubProfile) -> Dict[str, str]:
        """Generate skill proficiency levels."""
        proficiency = {}
        
        for lang, percentage in profile.languages_percentage.items():
            if percentage >= 25:
                proficiency[lang] = "Expert"
            elif percentage >= 15:
                proficiency[lang] = "Advanced"
            elif percentage >= 5:
                proficiency[lang] = "Intermediate"
            else:
                proficiency[lang] = "Basic"
        
        return proficiency
    
    def _generate_work_experience(self, profile: GitHubProfile, 
                                additional_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate work experience section."""
        if not self.config.include_experience:
            return []
        
        experience = additional_info.get('work_experience', [])
        
        # If no traditional work experience provided, synthesize from GitHub activity
        if not experience and profile.total_repositories > 5:
            # Create a freelance/open-source developer experience entry
            start_year = datetime.now().year - min(5, profile.total_repositories // 10 + 1)
            
            synthesized_experience = {
                "title": "Open Source Developer" if profile.total_stars_received > 50 else "Software Developer",
                "company": "Freelance / Open Source Community",
                "location": profile.location or "Remote",
                "start_date": f"{start_year}",
                "end_date": "Present",
                "description": self._generate_experience_description(profile),
                "achievements": self._generate_experience_achievements(profile),
                "technologies": profile.primary_languages[:5]
            }
            
            experience.append(synthesized_experience)
        
        return experience
    
    def _generate_experience_description(self, profile: GitHubProfile) -> str:
        """Generate experience description from GitHub profile."""
        descriptions = []
        
        if profile.has_web_projects:
            descriptions.append("Developed and maintained web applications using modern frameworks")
        
        if profile.has_mobile_projects:
            descriptions.append("Built mobile applications for iOS and Android platforms")
        
        if profile.has_apis:
            descriptions.append("Designed and implemented RESTful APIs and backend services")
        
        if profile.has_libraries:
            descriptions.append("Created and maintained open-source libraries and developer tools")
        
        if profile.collaboration_score > 60:
            descriptions.append("Collaborated with distributed teams and contributed to community projects")
        
        if profile.total_stars_received > 100:
            descriptions.append("Gained recognition in the developer community through quality open-source contributions")
        
        return ". ".join(descriptions) + "." if descriptions else "Developed software solutions and contributed to open-source projects."
    
    def _generate_experience_achievements(self, profile: GitHubProfile) -> List[str]:
        """Generate experience achievements from profile metrics."""
        achievements = []
        
        if profile.total_repositories > 20:
            achievements.append(f"Built and maintained {profile.total_repositories} software projects")
        
        if profile.total_stars_received > 50:
            achievements.append(f"Earned {profile.total_stars_received} stars from the developer community")
        
        if profile.total_forks_received > 20:
            achievements.append(f"Projects were forked {profile.total_forks_received} times, demonstrating reusability")
        
        if len(profile.languages_used) > 7:
            achievements.append(f"Demonstrated proficiency in {len(profile.languages_used)} programming languages")
        
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.8:
            achievements.append("Maintained comprehensive documentation across all projects")
        
        return achievements
    
    def _generate_featured_projects(self, profile: GitHubProfile) -> List[Dict[str, Any]]:
        """Generate featured projects for CV."""
        if not self.config.include_projects:
            return []
        
        projects = []
        
        # Get top projects by criteria
        for project in profile.featured_projects[:self.config.max_featured_projects]:
            if project.get('stars', 0) >= self.config.min_stars_for_projects:
                cv_project = {
                    "name": project['name'],
                    "description": self._enhance_project_description(project),
                    "technologies": [project.get('language', 'N/A')],
                    "url": project['url'],
                    "stars": project.get('stars', 0),
                    "highlights": self._generate_project_highlights(project),
                    "type": project.get('project_type', 'other'),
                    "year": self._extract_year_from_date(project.get('updated_at', ''))
                }
                
                # Add topics as additional technologies
                if project.get('topics'):
                    cv_project['technologies'].extend(project['topics'][:3])
                
                projects.append(cv_project)
        
        return projects
    
    def _enhance_project_description(self, project: Dict[str, Any]) -> str:
        """Enhance project description for professional presentation."""
        original_desc = project.get('description', '')
        if not original_desc:
            # Generate description from project name and type
            project_type = project.get('project_type', 'application')
            name = project['name'].replace('-', ' ').replace('_', ' ').title()
            
            type_descriptions = {
                'web-app': f"{name} - A web application",
                'mobile-app': f"{name} - A mobile application",
                'api': f"{name} - An API service",
                'library': f"{name} - A software library",
                'cli-tool': f"{name} - A command-line tool",
                'other': f"{name} - A software project"
            }
            
            return type_descriptions.get(project_type, f"{name} - A software project")
        
        # Clean up and professionalize existing description
        desc = original_desc.strip()
        if not desc.endswith('.'):
            desc += '.'
        
        return desc
    
    def _generate_project_highlights(self, project: Dict[str, Any]) -> List[str]:
        """Generate project highlights/achievements."""
        highlights = []
        
        stars = project.get('stars', 0)
        forks = project.get('forks', 0)
        
        if stars > 100:
            highlights.append(f"Achieved {stars} GitHub stars")
        elif stars > 20:
            highlights.append(f"Gained {stars} stars from community")
        
        if forks > 50:
            highlights.append(f"Forked {forks} times by other developers")
        elif forks > 10:
            highlights.append(f"Forked {forks} times, showing reusability")
        
        if project.get('has_readme'):
            highlights.append("Comprehensive documentation provided")
        
        # Infer highlights from project type
        project_type = project.get('project_type', '')
        if project_type == 'web-app':
            highlights.append("Full-stack web application development")
        elif project_type == 'mobile-app':
            highlights.append("Cross-platform mobile development")
        elif project_type == 'api':
            highlights.append("RESTful API design and implementation")
        elif project_type == 'library':
            highlights.append("Reusable component development")
        
        return highlights
    
    def _generate_project_categories(self, profile: GitHubProfile) -> Dict[str, List[Dict]]:
        """Generate categorized projects."""
        if not self.config.group_projects_by_type:
            return {}
        
        return profile.project_categories
    
    def _generate_achievements(self, profile: GitHubProfile) -> List[str]:
        """Generate achievements section."""
        if not self.config.include_achievements:
            return []
        
        achievements = []
        
        # GitHub-based achievements
        if profile.total_stars_received > 500:
            achievements.append(f"🌟 Earned {profile.total_stars_received} GitHub stars across all projects")
        elif profile.total_stars_received > 100:
            achievements.append(f"⭐ Achieved {profile.total_stars_received} GitHub stars for open-source contributions")
        
        if profile.total_repositories > 50:
            achievements.append(f"🚀 Built and published {profile.total_repositories} software projects")
        
        if profile.collaboration_score > 80:
            achievements.append("🤝 Recognized for exceptional collaborative development practices")
        
        if profile.innovation_score > 80:
            achievements.append("💡 Demonstrated innovation through original project development")
        
        if len(profile.languages_used) > 10:
            achievements.append(f"🔧 Proficient in {len(profile.languages_used)} programming languages and technologies")
        
        # Experience-based achievements
        if profile.experience_level == 'Senior':
            achievements.append("👨‍💻 Senior-level expertise in software development")
        elif profile.experience_level == 'Lead':
            achievements.append("👑 Lead-level technical expertise and project management")
        
        # Add any existing achievements from profile
        if hasattr(profile, 'achievements') and profile.achievements:
            achievements.extend(profile.achievements)
        
        return achievements
    
    def _generate_github_stats(self, profile: GitHubProfile) -> Dict[str, Any]:
        """Generate GitHub statistics for CV."""
        if not self.config.include_github_stats:
            return {}
        
        return {
            "total_repositories": profile.total_repositories,
            "original_projects": profile.original_repositories,
            "total_stars": profile.total_stars_received,
            "total_forks": profile.total_forks_received,
            "languages_used": len(profile.languages_used),
            "collaboration_score": round(profile.collaboration_score, 1),
            "innovation_score": round(profile.innovation_score, 1),
            "primary_languages": profile.primary_languages[:5],
            "developer_type": profile.developer_type,
            "experience_level": profile.experience_level
        }
    
    def _extract_year_from_date(self, date_str: str) -> str:
        """Extract year from ISO date string."""
        try:
            if date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y')
        except:
            pass
        return datetime.now().strftime('%Y')


class CVExporter:
    """Exports CV data to various formats."""
    
    def __init__(self, cv_data: CVData):
        self.cv_data = cv_data
        self.logger = get_logger()
    
    def export_to_json(self, file_path: str):
        """Export CV to JSON format."""
        try:
            cv_dict = asdict(self.cv_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cv_dict, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"CV exported to JSON: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CV to JSON: {e}")
            raise
    
    def export_to_html(self, file_path: str):
        """Export CV to HTML format."""
        try:
            html_content = self._generate_cv_html()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"CV exported to HTML: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CV to HTML: {e}")
            raise
    
    def export_to_pdf(self, file_path: str):
        """Export CV to PDF format."""
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                html_content = self._generate_cv_html()
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            try:
                # Use the same PDF generation methods as ProfileExporter
                success = False
                
                # Method 1: Try weasyprint
                if not success:
                    success = self._pdf_with_weasyprint(temp_html_path, file_path)
                
                # Method 2: Try playwright
                if not success:
                    success = self._pdf_with_playwright(temp_html_path, file_path)
                
                # Method 3: Try wkhtmltopdf
                if not success:
                    success = self._pdf_with_wkhtmltopdf(temp_html_path, file_path)
                
                # Method 4: Try Chrome/Chromium headless
                if not success:
                    success = self._pdf_with_chrome(temp_html_path, file_path)
                
                if not success:
                    raise RuntimeError(
                        "No PDF generation method available. Please install one of the following:\n"
                        "- weasyprint: pip install weasyprint\n"
                        "- playwright: pip install playwright && playwright install chromium\n"
                        "- wkhtmltopdf: Download from https://wkhtmltopdf.org/\n"
                        "- Chrome/Chromium browser"
                    )
                
                self.logger.info(f"CV exported to PDF: {file_path}")
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_html_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to export CV to PDF: {e}")
            raise
    
    def _generate_cv_html(self) -> str:
        """Generate HTML CV based on style."""
        style_generators = {
            'modern': self._generate_modern_cv_html,
            'classic': self._generate_classic_cv_html,
            'minimal': self._generate_minimal_cv_html,
            'technical': self._generate_technical_cv_html,
            'creative': self._generate_creative_cv_html
        }
        
        generator = style_generators.get(self.cv_data.cv_style, self._generate_modern_cv_html)
        return generator()
    
    def _generate_modern_cv_html(self) -> str:
        """Generate modern-style CV HTML."""
        # Generate contact info
        contact_info = []
        if self.cv_data.personal_info.get('email'):
            contact_info.append(f'<span><i class="fas fa-envelope"></i> {self.cv_data.personal_info["email"]}</span>')
        if self.cv_data.personal_info.get('phone'):
            contact_info.append(f'<span><i class="fas fa-phone"></i> {self.cv_data.personal_info["phone"]}</span>')
        if self.cv_data.personal_info.get('location'):
            contact_info.append(f'<span><i class="fas fa-map-marker-alt"></i> {self.cv_data.personal_info["location"]}</span>')
        if self.cv_data.personal_info.get('linkedin'):
            contact_info.append(f'<span><i class="fab fa-linkedin"></i> LinkedIn</span>')
        if self.cv_data.personal_info.get('github'):
            contact_info.append(f'<span><i class="fab fa-github"></i> GitHub</span>')
        
        contact_html = ' | '.join(contact_info)
        
        # Generate skills HTML
        skills_html = ""
        for category, skills_list in self.cv_data.technical_skills.items():
            skills_html += f"""
            <div class="skill-category">
                <h4>{category}</h4>
                <div class="skills-tags">
                    {' '.join(f'<span class="skill-tag">{skill}</span>' for skill in skills_list)}
                </div>
            </div>"""
        
        # Generate projects HTML
        projects_html = ""
        for project in self.cv_data.featured_projects:
            highlights_html = ""
            if project.get('highlights'):
                highlights_html = "<ul>" + "".join(f"<li>{highlight}</li>" for highlight in project['highlights']) + "</ul>"
            
            projects_html += f"""
            <div class="project">
                <div class="project-header">
                    <h4>{project['name']}</h4>
                    <div class="project-meta">
                        <span class="year">{project.get('year', '')}</span>
                        {'<span class="stars">⭐ ' + str(project['stars']) + '</span>' if project.get('stars', 0) > 0 else ''}
                    </div>
                </div>
                <p class="project-description">{project['description']}</p>
                <div class="project-tech">
                    {' '.join(f'<span class="tech-tag">{tech}</span>' for tech in project.get('technologies', []))}
                </div>
                {highlights_html}
            </div>"""
        
        # Generate work experience HTML
        experience_html = ""
        for exp in self.cv_data.work_experience:
            achievements_html = ""
            if exp.get('achievements'):
                achievements_html = "<ul>" + "".join(f"<li>{achievement}</li>" for achievement in exp['achievements']) + "</ul>"
            
            experience_html += f"""
            <div class="experience">
                <div class="experience-header">
                    <h4>{exp['title']}</h4>
                    <div class="experience-meta">
                        <span class="company">{exp['company']}</span>
                        <span class="period">{exp['start_date']} - {exp['end_date']}</span>
                    </div>
                </div>
                <p class="experience-description">{exp['description']}</p>
                {achievements_html}
            </div>"""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.cv_data.personal_info.get('name', 'CV')} - Resume</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
            padding: 20px;
        }}
        
        .cv-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .cv-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        .cv-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .cv-header .title {{
            font-size: 1.2rem;
            margin-bottom: 20px;
            opacity: 0.95;
        }}
        
        .contact-info {{
            font-size: 0.9rem;
            opacity: 0.9;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .contact-info i {{
            margin-right: 5px;
        }}
        
        .cv-body {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #667eea;
            font-size: 1.4rem;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }}
        
        .summary {{
            font-size: 1.05rem;
            line-height: 1.7;
            color: #555;
            text-align: justify;
        }}
        
        .skill-category {{
            margin-bottom: 20px;
        }}
        
        .skill-category h4 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }}
        
        .skills-tags, .project-tech {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .skill-tag, .tech-tag {{
            background: #f0f0f0;
            color: #333;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        
        .tech-tag {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        
        .project {{
            margin-bottom: 25px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background: #fafafa;
        }}
        
        .project-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .project-header h4 {{
            color: #333;
            font-size: 1.1rem;
        }}
        
        .project-meta {{
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
            color: #666;
        }}
        
        .stars {{
            color: #ff9800;
        }}
        
        .project-description {{
            margin-bottom: 15px;
            color: #555;
            font-size: 0.95rem;
        }}
        
        .experience {{
            margin-bottom: 25px;
            padding: 20px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .experience:last-child {{
            border-bottom: none;
        }}
        
        .experience-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }}
        
        .experience-header h4 {{
            color: #333;
            font-size: 1.1rem;
        }}
        
        .experience-meta {{
            text-align: right;
            font-size: 0.9rem;
            color: #666;
        }}
        
        .company {{
            font-weight: 600;
            color: #667eea;
        }}
        
        .period {{
            display: block;
            margin-top: 2px;
        }}
        
        .experience-description {{
            margin-bottom: 15px;
            color: #555;
            font-size: 0.95rem;
        }}
        
        ul {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        
        li {{
            margin-bottom: 5px;
            color: #555;
            font-size: 0.9rem;
        }}
        
        .achievements {{
            margin-bottom: 20px;
        }}
        
        .achievement-item {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 0.9rem;
        }}
        
        .github-stats {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-item .number {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}
        
        .stat-item .label {{
            font-size: 0.8rem;
            color: #666;
            margin-top: 5px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .cv-container {{
                box-shadow: none;
                border-radius: 0;
            }}
            
            .section {{
                page-break-inside: avoid;
            }}
        }}
        
        @media (max-width: 600px) {{
            .cv-header {{
                padding: 30px 20px;
            }}
            
            .cv-header h1 {{
                font-size: 2rem;
            }}
            
            .contact-info {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .project-header, .experience-header {{
                flex-direction: column;
                align-items: start;
            }}
            
            .project-meta, .experience-meta {{
                margin-top: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="cv-container">
        <div class="cv-header">
            <h1>{self.cv_data.personal_info.get('name', 'Professional')}</h1>
            <div class="title">{self.cv_data.target_role or 'Software Developer'}</div>
            <div class="contact-info">
                {contact_html}
            </div>
        </div>
        
        <div class="cv-body">
            {f'''
            <div class="section">
                <h2><i class="fas fa-user"></i> Professional Summary</h2>
                <div class="summary">{self.cv_data.professional_summary}</div>
            </div>
            ''' if self.cv_data.professional_summary else ''}
            
            {f'''
            <div class="section">
                <h2><i class="fas fa-cogs"></i> Technical Skills</h2>
                {skills_html}
            </div>
            ''' if self.cv_data.technical_skills else ''}
            
            {f'''
            <div class="section">
                <h2><i class="fas fa-briefcase"></i> Professional Experience</h2>
                {experience_html}
            </div>
            ''' if self.cv_data.work_experience else ''}
            
            {f'''
            <div class="section">
                <h2><i class="fas fa-code"></i> Featured Projects</h2>
                {projects_html}
            </div>
            ''' if self.cv_data.featured_projects else ''}
            
            {f'''
            <div class="section">
                <h2><i class="fas fa-trophy"></i> Achievements</h2>
                <div class="achievements">
                    {''.join(f'<div class="achievement-item">{achievement}</div>' for achievement in self.cv_data.achievements)}
                </div>
            </div>
            ''' if self.cv_data.achievements else ''}
            
            {f'''
            <div class="section">
                <h2><i class="fab fa-github"></i> GitHub Statistics</h2>
                <div class="github-stats">
                    <div class="stat-item">
                        <span class="number">{self.cv_data.github_stats.get('total_repositories', 0)}</span>
                        <div class="label">Repositories</div>
                    </div>
                    <div class="stat-item">
                        <span class="number">{self.cv_data.github_stats.get('total_stars', 0)}</span>
                        <div class="label">Stars Earned</div>
                    </div>
                    <div class="stat-item">
                        <span class="number">{self.cv_data.github_stats.get('languages_used', 0)}</span>
                        <div class="label">Languages</div>
                    </div>
                    <div class="stat-item">
                        <span class="number">{self.cv_data.github_stats.get('collaboration_score', 0)}</span>
                        <div class="label">Collaboration</div>
                    </div>
                </div>
            </div>
            ''' if self.cv_data.github_stats else ''}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    # Placeholder methods for other CV styles
    def _generate_classic_cv_html(self) -> str:
        """Generate classic-style CV HTML."""
        # Would implement a more traditional, conservative CV style
        return self._generate_modern_cv_html()  # For now, use modern
    
    def _generate_minimal_cv_html(self) -> str:
        """Generate minimal-style CV HTML."""
        # Would implement a clean, minimal CV style
        return self._generate_modern_cv_html()  # For now, use modern
    
    def _generate_technical_cv_html(self) -> str:
        """Generate technical-style CV HTML."""
        # Would implement a technical, code-focused CV style
        return self._generate_modern_cv_html()  # For now, use modern
    
    def _generate_creative_cv_html(self) -> str:
        """Generate creative-style CV HTML."""
        # Would implement a creative, visually striking CV style
        return self._generate_modern_cv_html()  # For now, use modern
    
    # PDF generation methods (reused from ProfileExporter)
    def _pdf_with_weasyprint(self, html_path: str, pdf_path: str) -> bool:
        """Generate PDF using WeasyPrint."""
        try:
            import weasyprint
            from urllib.request import pathname2url
            
            file_url = f"file://{pathname2url(os.path.abspath(html_path))}"
            weasyprint.HTML(url=file_url).write_pdf(pdf_path)
            return True
            
        except ImportError:
            return False
        except Exception as e:
            self.logger.warning(f"WeasyPrint PDF generation failed: {e}")
            return False
    
    def _pdf_with_playwright(self, html_path: str, pdf_path: str) -> bool:
        """Generate PDF using Playwright."""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(f"file://{os.path.abspath(html_path)}")
                page.wait_for_load_state("networkidle")
                
                page.pdf(
                    path=pdf_path,
                    format='A4',
                    print_background=True,
                    margin={'top': '0.5in', 'bottom': '0.5in', 'left': '0.5in', 'right': '0.5in'}
                )
                
                browser.close()
            return True
            
        except ImportError:
            return False
        except Exception as e:
            self.logger.warning(f"Playwright PDF generation failed: {e}")
            return False
    
    def _pdf_with_wkhtmltopdf(self, html_path: str, pdf_path: str) -> bool:
        """Generate PDF using wkhtmltopdf."""
        try:
            import subprocess
            import shutil
            
            if not shutil.which('wkhtmltopdf'):
                return False
            
            cmd = [
                'wkhtmltopdf', '--page-size', 'A4', '--margin-top', '0.75in',
                '--margin-right', '0.75in', '--margin-bottom', '0.75in', '--margin-left', '0.75in',
                '--enable-local-file-access', '--print-media-type', html_path, pdf_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.warning(f"wkhtmltopdf PDF generation failed: {e}")
            return False
    
    def _pdf_with_chrome(self, html_path: str, pdf_path: str) -> bool:
        """Generate PDF using Chrome/Chromium headless."""
        try:
            import subprocess
            import shutil
            import platform
            
            # Find Chrome/Chromium executable
            chrome_paths = []
            if platform.system() == "Windows":
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ]
            elif platform.system() == "Darwin":  # macOS
                chrome_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium",
                ]
            else:  # Linux
                chrome_paths = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]
            
            chrome_exe = None
            for path in chrome_paths:
                if os.path.exists(path) or shutil.which(path):
                    chrome_exe = path
                    break
            
            if not chrome_exe:
                return False
            
            cmd = [
                chrome_exe, '--headless', '--disable-gpu', '--no-sandbox',
                '--disable-dev-shm-usage', '--print-to-pdf=' + pdf_path,
                '--print-to-pdf-no-header', f'file://{os.path.abspath(html_path)}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0 and os.path.exists(pdf_path)
            
        except Exception as e:
            self.logger.warning(f"Chrome PDF generation failed: {e}")
            return False