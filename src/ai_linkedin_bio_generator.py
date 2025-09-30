#!/usr/bin/env python3
"""
AI LinkedIn Bio Generator

Advanced AI-powered LinkedIn profile bio generator that analyzes all GitHub repositories
to create compelling, professional, and personalized LinkedIn bios. Uses repository
analysis, technology detection, and AI content generation to produce optimized profiles.
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import Counter
from datetime import datetime
import statistics

try:
    from .utils.logger import get_logger
    from .github_data_manager import GitHubDataManager, GitHubUserData
    from .profile_builder import GitHubProfile
    from .linkedin_generator import LinkedInGenerator, LinkedInConfig
except ImportError:
    from utils.logger import get_logger
    from github_data_manager import GitHubDataManager, GitHubUserData
    from profile_builder import GitHubProfile
    from linkedin_generator import LinkedInGenerator, LinkedInConfig


@dataclass
class AIBioConfig:
    """Configuration for AI bio generation."""
    
    # Bio style and tone
    bio_style: str = "professional"  # professional, creative, technical, executive, startup
    tone: str = "confident"  # confident, humble, enthusiastic, analytical, visionary
    length: str = "medium"  # short (100-150 words), medium (150-250), long (250-400)
    
    # Experience level configuration
    experience_level: str = "recent_graduate"  # recent_graduate, junior, mid_level, senior, lead, executive
    years_experience: int = 0  # Actual years of experience
    career_stage: str = "entry_level"  # entry_level, early_career, mid_career, senior_career, executive
    
    # Content focus
    focus_areas: List[str] = None  # ["technical_skills", "learning", "projects", "potential"]
    target_industry: str = "technology"
    target_role: str = "Software Engineer"
    
    # Technology tracking
    programming_languages: List[str] = None  # ["Python", "JavaScript", "C#"]
    frameworks_libraries: List[str] = None   # ["React", "NextJS", "Avalonia", "Django"]
    tools_platforms: List[str] = None       # ["Docker", "AWS", "Git", "VS Code"]
    databases: List[str] = None             # ["PostgreSQL", "MongoDB", "Redis"]
    specializations: List[str] = None       # ["Web Development", "Mobile Apps", "AI/ML"]
    
    # AI generation preferences
    use_metrics: bool = True  # Include specific numbers and achievements
    include_passion_statement: bool = True
    include_call_to_action: bool = True
    emphasize_collaboration: bool = True
    highlight_innovation: bool = True
    show_learning_mindset: bool = True  # Important for recent graduates
    
    # Keywords and optimization
    primary_keywords: List[str] = None  # Auto-generated if None
    industry_keywords: List[str] = None
    custom_achievements: List[str] = None
    
    # Personalization
    personal_brand_adjectives: List[str] = None  # ["innovative", "eager", "collaborative"]
    value_proposition: str = ""  # What unique value do you bring?
    
    # README and Website Integration (NEW)
    selected_readmes: List[str] = None  # List of repository names to analyze README files
    portfolio_website: str = ""  # Portfolio website URL
    professional_website: str = ""  # Professional/company website URL
    
    def __post_init__(self):
        if self.focus_areas is None:
            # Different focus areas based on experience level
            if self.experience_level == "recent_graduate":
                self.focus_areas = ["learning", "projects", "potential", "technical_skills"]
            elif self.experience_level in ["junior", "mid_level"]:
                self.focus_areas = ["technical_skills", "growth", "collaboration", "results"]
            else:
                self.focus_areas = ["technical_skills", "leadership", "innovation", "results"]
        
        if self.primary_keywords is None:
            self.primary_keywords = []
        if self.industry_keywords is None:
            self.industry_keywords = []
        if self.custom_achievements is None:
            self.custom_achievements = []
        if self.personal_brand_adjectives is None:
            if self.experience_level == "recent_graduate":
                self.personal_brand_adjectives = ["eager", "collaborative", "innovative"]
            else:
                self.personal_brand_adjectives = ["innovative", "results-driven", "collaborative"]
        
        # Initialize technology lists
        if self.programming_languages is None:
            self.programming_languages = []
        if self.frameworks_libraries is None:
            self.frameworks_libraries = []
        if self.tools_platforms is None:
            self.tools_platforms = []
        if self.databases is None:
            self.databases = []
        if self.specializations is None:
            self.specializations = []
        
        # Initialize README and website fields (NEW)
        if self.selected_readmes is None:
            self.selected_readmes = []
            self.tools_platforms = []
        if self.databases is None:
            self.databases = []
        if self.specializations is None:
            self.specializations = []
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = ["technical_skills", "innovation", "results"]
        if self.primary_keywords is None:
            self.primary_keywords = []
        if self.industry_keywords is None:
            self.industry_keywords = []
        if self.custom_achievements is None:
            self.custom_achievements = []
        if self.personal_brand_adjectives is None:
            self.personal_brand_adjectives = ["innovative", "results-driven", "collaborative"]


@dataclass
class AIBioAnalysis:
    """Comprehensive analysis for AI bio generation."""
    
    # Repository insights
    total_repositories: int = 0
    active_repositories: int = 0  # Recently updated
    diverse_projects: List[str] = None
    complexity_score: float = 0.0  # Based on project complexity
    innovation_indicators: List[str] = None
    
    # Technical expertise
    primary_languages: List[str] = None
    frameworks_mastery: List[str] = None
    domain_expertise: List[str] = None  # web, mobile, ai, data, etc.
    architectural_patterns: List[str] = None
    
    # Professional indicators
    leadership_evidence: List[str] = None
    collaboration_metrics: Dict[str, int] = None
    community_impact: Dict[str, Any] = None
    problem_solving_examples: List[str] = None
    
    # Quantifiable achievements
    stars_received: int = 0
    forks_received: int = 0
    contributors_attracted: int = 0
    lines_of_code: int = 0
    projects_deployed: int = 0
    
    # Career progression
    technology_evolution: List[str] = None  # How skills evolved over time
    project_scale_growth: List[str] = None
    responsibility_indicators: List[str] = None
    
    # Unique differentiators
    unique_projects: List[str] = None
    innovative_solutions: List[str] = None
    cross_functional_skills: List[str] = None
    
    def __post_init__(self):
        if self.diverse_projects is None:
            self.diverse_projects = []
        if self.innovation_indicators is None:
            self.innovation_indicators = []
        if self.primary_languages is None:
            self.primary_languages = []
        if self.frameworks_mastery is None:
            self.frameworks_mastery = []
        if self.domain_expertise is None:
            self.domain_expertise = []
        if self.architectural_patterns is None:
            self.architectural_patterns = []
        if self.leadership_evidence is None:
            self.leadership_evidence = []
        if self.collaboration_metrics is None:
            self.collaboration_metrics = {}
        if self.community_impact is None:
            self.community_impact = {}
        if self.problem_solving_examples is None:
            self.problem_solving_examples = []
        if self.technology_evolution is None:
            self.technology_evolution = []
        if self.project_scale_growth is None:
            self.project_scale_growth = []
        if self.responsibility_indicators is None:
            self.responsibility_indicators = []
        if self.unique_projects is None:
            self.unique_projects = []
        if self.innovative_solutions is None:
            self.innovative_solutions = []
        if self.cross_functional_skills is None:
            self.cross_functional_skills = []


@dataclass
class AIGeneratedBio:
    """Generated LinkedIn bio with multiple variations."""
    
    primary_bio: str = ""
    alternative_versions: List[str] = None
    
    # Bio components
    opening_hook: str = ""
    expertise_statement: str = ""
    achievement_highlights: str = ""
    value_proposition: str = ""
    passion_statement: str = ""
    call_to_action: str = ""
    
    # Optimization data
    keyword_density: Dict[str, float] = None
    readability_score: float = 0.0
    engagement_potential: str = ""  # high, medium, low
    
    # SEO optimization
    primary_keywords_used: List[str] = None
    industry_keywords_used: List[str] = None
    search_optimization_score: float = 0.0
    
    # Personalization metrics
    uniqueness_score: float = 0.0
    authenticity_indicators: List[str] = None
    
    def __post_init__(self):
        if self.alternative_versions is None:
            self.alternative_versions = []
        if self.keyword_density is None:
            self.keyword_density = {}
        if self.primary_keywords_used is None:
            self.primary_keywords_used = []
        if self.industry_keywords_used is None:
            self.industry_keywords_used = []
        if self.authenticity_indicators is None:
            self.authenticity_indicators = []


class AILinkedInBioGenerator:
    """AI-powered LinkedIn bio generator using repository analysis."""
    
    def __init__(self, config: AIBioConfig = None):
        self.config = config or AIBioConfig()
        self.logger = get_logger()
        
        # AI content templates and patterns
        self._load_bio_templates()
        self._load_industry_keywords()
        
    def _load_bio_templates(self):
        """Load bio templates for different styles and roles."""
        self.bio_templates = {
            "professional": {
                "opening": [
                    "Experienced {role} with {years}+ years building {domain} solutions",
                    "{experience_level} {role} passionate about {primary_focus}",
                    "Results-driven {role} specializing in {expertise_areas}"
                ],
                "expertise": [
                    "Expert in {technologies} with proven track record in {domains}",
                    "Deep expertise in {tech_stack} and {methodologies}",
                    "Specialized in {focus_areas} with hands-on experience in {technologies}"
                ],
                "achievements": [
                    "Led {achievement_count} successful projects resulting in {impact}",
                    "Built {project_types} serving {scale} users/transactions",
                    "Architected solutions that {specific_outcomes}"
                ],
                "value": [
                    "I transform complex technical challenges into elegant, scalable solutions",
                    "I bridge the gap between innovative technology and business value",
                    "I deliver high-quality software that drives measurable business impact"
                ],
                "passion": [
                    "Passionate about {passion_areas} and continuous learning",
                    "Driven by {motivations} and commitment to excellence",
                    "Enthusiastic about {interests} and emerging technologies"
                ],
                "cta": [
                    "Let's connect to discuss {topics}",
                    "Open to discussing {opportunities}",
                    "Always interested in {collaboration_areas}"
                ]
            },
            "creative": {
                "opening": [
                    "I turn ideas into code and dreams into digital reality ✨",
                    "Creative {role} who loves building things that matter 🚀",
                    "Code artist crafting digital experiences with {technologies}"
                ],
                "expertise": [
                    "My toolkit: {technologies} | My superpower: {unique_skill}",
                    "I speak fluent {languages} and dream in {frameworks}",
                    "From concept to deployment, I create magic with {tech_stack}"
                ],
                "achievements": [
                    "🏆 Built {notable_projects} that {impact_description}",
                    "📈 Delivered {quantified_results} across {project_count} projects",
                    "🌟 Created solutions that {specific_achievements}"
                ],
                "value": [
                    "I believe great software should be both powerful and beautiful",
                    "I combine technical excellence with creative problem-solving",
                    "I build technology that enhances human experiences"
                ],
                "passion": [
                    "When I'm not coding, you'll find me {hobbies} 🎯",
                    "Forever curious about {interests} and {emerging_tech} 🔍",
                    "Passionate about {causes} and {professional_interests} ❤️"
                ],
                "cta": [
                    "Let's create something amazing together! 💡",
                    "Coffee chat about {topics}? ☕",
                    "Always up for discussing {collaboration_areas} 🤝"
                ]
            },
            "technical": {
                "opening": [
                    "Senior {role} with deep expertise in {technical_domains}",
                    "Systems architect building scalable {solution_types}",
                    "Technical leader with {years}+ years in {specializations}"
                ],
                "expertise": [
                    "Core competencies: {technologies} | Architecture: {patterns}",
                    "Full-stack proficiency: {frontend} + {backend} + {infrastructure}",
                    "Technical stack: {detailed_technologies} with {methodologies}"
                ],
                "achievements": [
                    "Architected systems handling {scale} with {performance_metrics}",
                    "Optimized performance by {improvements} across {systems}",
                    "Implemented {solutions} resulting in {technical_outcomes}"
                ],
                "value": [
                    "I design and build robust, scalable systems that perform under pressure",
                    "I solve complex technical challenges with elegant, maintainable code",
                    "I optimize systems for performance, reliability, and scalability"
                ],
                "passion": [
                    "Constantly exploring {emerging_technologies} and {research_areas}",
                    "Dedicated to {technical_practices} and {quality_standards}",
                    "Committed to {technical_growth} and {community_contribution}"
                ],
                "cta": [
                    "Open to discussing architecture, scalability, and {technical_topics}",
                    "Let's talk about {technical_interests} and best practices",
                    "Always interested in {technical_collaboration}"
                ]
            },
            "executive": {
                "opening": [
                    "{title} driving digital transformation through {strategic_focus}",
                    "Technology leader with proven track record of {achievements}",
                    "Executive focused on {business_impact} through {technical_excellence}"
                ],
                "expertise": [
                    "Strategic expertise in {domains} with hands-on {technical_background}",
                    "Leadership in {areas} with deep understanding of {technologies}",
                    "Cross-functional leadership spanning {departments} and {domains}"
                ],
                "achievements": [
                    "Led teams of {team_size}+ delivering {business_outcomes}",
                    "Scaled organizations from {scale_from} to {scale_to}",
                    "Drove {strategic_initiatives} resulting in {business_impact}"
                ],
                "value": [
                    "I align technology strategy with business objectives for maximum impact",
                    "I build high-performing teams that deliver exceptional results",
                    "I transform organizations through strategic technology leadership"
                ],
                "passion": [
                    "Passionate about {leadership_focus} and {organizational_development}",
                    "Committed to {values} and {strategic_vision}",
                    "Driven by {motivations} and {long_term_goals}"
                ],
                "cta": [
                    "Open to board positions and strategic consulting opportunities",
                    "Let's discuss technology leadership and organizational growth",
                    "Interested in {strategic_topics} and {industry_trends}"
                ]
            },
            "startup": {
                "opening": [
                    "Startup veteran building {solutions} that {impact}",
                    "Entrepreneur and {role} creating {innovation_area}",
                    "Full-stack builder turning ideas into scalable products"
                ],
                "expertise": [
                    "End-to-end product development: {technologies} + {business_skills}",
                    "Rapid prototyping and scaling with {tech_stack}",
                    "Product-focused engineering with {domain_expertise}"
                ],
                "achievements": [
                    "Built and launched {products} from 0 to {scale}",
                    "Shipped {feature_count} features reaching {user_count} users",
                    "Created {value_proposition} generating {business_results}"
                ],
                "value": [
                    "I build products that solve real problems for real people",
                    "I move fast, learn quickly, and iterate based on user feedback",
                    "I combine technical execution with product intuition"
                ],
                "passion": [
                    "Obsessed with {product_focus} and {user_experience}",
                    "Always experimenting with {technologies} and {methodologies}",
                    "Excited about {industry_trends} and {emerging_opportunities}"
                ],
                "cta": [
                    "Let's build something amazing together 🚀",
                    "Always interested in {collaboration_opportunities}",
                    "Open to discussing {startup_topics} and new ventures"
                ]
            }
        }
    
    def _load_industry_keywords(self):
        """Load industry-specific keywords for optimization."""
        self.industry_keywords = {
            "technology": [
                "software development", "engineering", "architecture", "scalability",
                "innovation", "digital transformation", "agile", "devops", "cloud",
                "microservices", "API", "full-stack", "backend", "frontend"
            ],
            "fintech": [
                "financial technology", "payments", "blockchain", "cryptocurrency",
                "trading systems", "risk management", "compliance", "regulatory",
                "banking", "investment", "securities", "portfolio management"
            ],
            "healthcare": [
                "healthcare technology", "medical software", "patient care",
                "clinical systems", "healthcare data", "HIPAA", "medical devices",
                "telemedicine", "health informatics", "biotech"
            ],
            "ecommerce": [
                "e-commerce", "online retail", "marketplace", "payment processing",
                "inventory management", "supply chain", "customer experience",
                "conversion optimization", "digital marketing", "analytics"
            ],
            "gaming": [
                "game development", "game engine", "graphics programming",
                "multiplayer systems", "game design", "virtual reality",
                "augmented reality", "mobile gaming", "console development"
            ],
            "ai_ml": [
                "artificial intelligence", "machine learning", "deep learning",
                "neural networks", "data science", "computer vision",
                "natural language processing", "predictive analytics", "automation"
            ]
        }
    
    def analyze_repositories_for_bio(self, github_profile: GitHubProfile) -> AIBioAnalysis:
        """Perform comprehensive analysis of repositories for bio generation."""
        self.logger.info("🔍 Analyzing repositories for AI bio generation...")
        
        analysis = AIBioAnalysis()
        
        # Basic metrics
        analysis.total_repositories = len(github_profile.featured_projects)
        analysis.stars_received = github_profile.total_stars_received
        analysis.forks_received = github_profile.total_forks_received
        
        # Analyze repository diversity and complexity
        analysis.diverse_projects = self._analyze_project_diversity(github_profile)
        analysis.complexity_score = self._calculate_complexity_score(github_profile)
        analysis.innovation_indicators = self._identify_innovation_indicators(github_profile)
        
        # Technical expertise analysis
        analysis.primary_languages = list(github_profile.primary_languages[:5])
        analysis.frameworks_mastery = self._extract_frameworks(github_profile)
        analysis.domain_expertise = self._identify_domain_expertise(github_profile)
        analysis.architectural_patterns = self._identify_architectural_patterns(github_profile)
        
        # Professional indicators
        analysis.leadership_evidence = self._identify_leadership_evidence(github_profile)
        analysis.collaboration_metrics = self._calculate_collaboration_metrics(github_profile)
        analysis.community_impact = self._assess_community_impact(github_profile)
        analysis.problem_solving_examples = self._extract_problem_solving_examples(github_profile)
        
        # Career progression analysis
        analysis.technology_evolution = self._analyze_technology_evolution(github_profile)
        analysis.project_scale_growth = self._analyze_project_scale_growth(github_profile)
        analysis.responsibility_indicators = self._identify_responsibility_indicators(github_profile)
        
        # Unique differentiators
        analysis.unique_projects = self._identify_unique_projects(github_profile)
        analysis.innovative_solutions = self._identify_innovative_solutions(github_profile)
        analysis.cross_functional_skills = self._identify_cross_functional_skills(github_profile)
        
        self.logger.info(f"✅ Repository analysis complete: {analysis.total_repositories} repos analyzed")
        return analysis
    
    def _analyze_project_diversity(self, github_profile: GitHubProfile) -> List[str]:
        """Analyze diversity of projects."""
        diverse_projects = []
        
        # Check project categories
        if hasattr(github_profile, 'project_categories'):
            for category, projects in github_profile.project_categories.items():
                if len(projects) > 0:
                    diverse_projects.append(f"{category.replace('-', ' ').title()}")
        
        # Add language diversity
        if len(github_profile.primary_languages) > 3:
            diverse_projects.append("Multi-language proficiency")
        
        return diverse_projects
    
    def _calculate_complexity_score(self, github_profile: GitHubProfile) -> float:
        """Calculate project complexity score."""
        score = 0.0
        
        # Language diversity (max 30 points)
        language_count = len(github_profile.primary_languages)
        score += min(language_count * 5, 30)
        
        # Repository with documentation (max 20 points)
        if hasattr(github_profile, 'repositories_with_readme'):
            readme_ratio = github_profile.repositories_with_readme / max(github_profile.total_repositories, 1)
            score += readme_ratio * 20
        
        # Testing and CI/CD (max 25 points)
        if hasattr(github_profile, 'repositories_with_tests'):
            test_ratio = github_profile.repositories_with_tests / max(github_profile.total_repositories, 1)
            score += test_ratio * 15
        
        if hasattr(github_profile, 'repositories_with_ci'):
            ci_ratio = github_profile.repositories_with_ci / max(github_profile.total_repositories, 1)
            score += ci_ratio * 10
        
        # Community engagement (max 25 points)
        if github_profile.total_stars_received > 100:
            score += 15
        elif github_profile.total_stars_received > 50:
            score += 10
        elif github_profile.total_stars_received > 10:
            score += 5
        
        if github_profile.total_forks_received > 20:
            score += 10
        elif github_profile.total_forks_received > 5:
            score += 5
        
        return min(score, 100.0)
    
    def _identify_innovation_indicators(self, github_profile: GitHubProfile) -> List[str]:
        """Identify indicators of innovation."""
        indicators = []
        
        # Check for cutting-edge technologies
        modern_languages = {"Rust", "Go", "TypeScript", "Kotlin", "Swift", "Python"}
        if any(lang in modern_languages for lang in github_profile.primary_languages):
            indicators.append("Adopts modern technologies")
        
        # Check for AI/ML projects
        ai_keywords = ["ai", "ml", "machine-learning", "neural", "tensorflow", "pytorch"]
        for project in github_profile.featured_projects:
            if any(keyword in project.get('description', '').lower() for keyword in ai_keywords):
                indicators.append("AI/ML innovation")
                break
        
        # Check for high community engagement
        if github_profile.total_stars_received > 50:
            indicators.append("Community-recognized projects")
        
        # Check for diverse project types
        if hasattr(github_profile, 'project_categories') and len(github_profile.project_categories) > 3:
            indicators.append("Cross-domain expertise")
        
        return indicators
    
    def _extract_frameworks(self, github_profile: GitHubProfile) -> List[str]:
        """Extract frameworks from project analysis."""
        frameworks = []
        
        if hasattr(github_profile, 'frameworks'):
            frameworks.extend(github_profile.frameworks[:8])  # Top 8 frameworks
        
        # Infer frameworks from languages
        language_framework_map = {
            "JavaScript": ["React", "Node.js", "Express"],
            "TypeScript": ["Angular", "React", "Vue.js"],
            "Python": ["Django", "Flask", "FastAPI"],
            "Java": ["Spring", "Spring Boot"],
            "C#": [".NET", "ASP.NET"],
            "Go": ["Gin", "Echo"],
            "Rust": ["Actix", "Rocket"]
        }
        
        for lang in github_profile.primary_languages:
            if lang in language_framework_map:
                frameworks.extend(language_framework_map[lang][:2])
        
        return list(set(frameworks))[:10]  # Remove duplicates, limit to 10
    
    def _identify_domain_expertise(self, github_profile: GitHubProfile) -> List[str]:
        """Identify domain expertise areas."""
        domains = []
        
        # Analyze project types
        if hasattr(github_profile, 'project_categories'):
            category_domain_map = {
                "web-apps": "Web Development",
                "mobile-apps": "Mobile Development", 
                "apis": "API Development",
                "libraries": "Library Development",
                "cli-tools": "DevOps & Automation",
                "data-science": "Data Science",
                "machine-learning": "Machine Learning"
            }
            
            for category in github_profile.project_categories.keys():
                if category in category_domain_map:
                    domains.append(category_domain_map[category])
        
        # Infer from languages
        language_domain_map = {
            "JavaScript": "Frontend Development",
            "TypeScript": "Full-stack Development",
            "Python": "Backend Development",
            "Java": "Enterprise Development",
            "C++": "Systems Programming",
            "Swift": "iOS Development",
            "Kotlin": "Android Development",
            "Go": "Cloud Infrastructure",
            "Rust": "Systems Programming"
        }
        
        for lang in github_profile.primary_languages[:3]:
            if lang in language_domain_map:
                domains.append(language_domain_map[lang])
        
        return list(set(domains))
    
    def _identify_architectural_patterns(self, github_profile: GitHubProfile) -> List[str]:
        """Identify architectural patterns used."""
        patterns = []
        
        # Infer from project descriptions and technologies
        if hasattr(github_profile, 'repositories_with_docker') and github_profile.repositories_with_docker > 0:
            patterns.append("Containerization")
        
        if "microservice" in str(github_profile.featured_projects).lower():
            patterns.append("Microservices")
        
        if any("api" in project.get('name', '').lower() for project in github_profile.featured_projects):
            patterns.append("RESTful APIs")
        
        # Add common patterns based on languages
        if "JavaScript" in github_profile.primary_languages or "TypeScript" in github_profile.primary_languages:
            patterns.extend(["Single Page Applications", "Component Architecture"])
        
        if "Python" in github_profile.primary_languages:
            patterns.append("MVC Architecture")
        
        return patterns
    
    def _identify_leadership_evidence(self, github_profile: GitHubProfile) -> List[str]:
        """Identify evidence of leadership."""
        evidence = []
        
        # High-star repositories indicate thought leadership
        if github_profile.total_stars_received > 100:
            evidence.append("Open source thought leader")
        
        # Multiple contributors on projects
        if github_profile.total_forks_received > 20:
            evidence.append("Collaborative project leader")
        
        # Documentation and README quality
        if hasattr(github_profile, 'repositories_with_readme'):
            readme_ratio = github_profile.repositories_with_readme / max(github_profile.total_repositories, 1)
            if readme_ratio > 0.8:
                evidence.append("Documentation advocate")
        
        # Testing and quality practices
        if hasattr(github_profile, 'repositories_with_tests'):
            test_ratio = github_profile.repositories_with_tests / max(github_profile.total_repositories, 1)
            if test_ratio > 0.5:
                evidence.append("Quality engineering leader")
        
        return evidence
    
    def _calculate_collaboration_metrics(self, github_profile: GitHubProfile) -> Dict[str, int]:
        """Calculate collaboration metrics."""
        return {
            "stars_received": github_profile.total_stars_received,
            "forks_received": github_profile.total_forks_received,
            "public_repos": github_profile.public_repositories,
            "total_repos": github_profile.total_repositories
        }
    
    def _assess_community_impact(self, github_profile: GitHubProfile) -> Dict[str, Any]:
        """Assess community impact."""
        impact = {
            "visibility": "high" if github_profile.total_stars_received > 100 else "medium" if github_profile.total_stars_received > 20 else "low",
            "contribution": "active" if github_profile.public_repositories > 10 else "moderate",
            "influence": "significant" if github_profile.total_forks_received > 50 else "growing"
        }
        
        return impact
    
    def _extract_problem_solving_examples(self, github_profile: GitHubProfile) -> List[str]:
        """Extract problem-solving examples from projects."""
        examples = []
        
        for project in github_profile.featured_projects[:5]:
            if project.get('description'):
                # Look for problem-solving indicators in descriptions
                desc = project['description'].lower()
                if any(word in desc for word in ['optimization', 'improved', 'enhanced', 'automated', 'simplified']):
                    examples.append(f"Optimized {project['name']}")
                elif any(word in desc for word in ['built', 'created', 'developed', 'designed']):
                    examples.append(f"Architected {project['name']}")
        
        return examples
    
    def _analyze_technology_evolution(self, github_profile: GitHubProfile) -> List[str]:
        """Analyze technology evolution over time."""
        evolution = []
        
        # Simple analysis based on language diversity
        if len(github_profile.primary_languages) > 3:
            evolution.append("Multi-language proficiency evolution")
        
        # Modern framework adoption
        modern_frameworks = ["React", "Vue", "Angular", "Django", "Flask", "Spring Boot"]
        if hasattr(github_profile, 'frameworks'):
            modern_count = sum(1 for fw in github_profile.frameworks if fw in modern_frameworks)
            if modern_count > 2:
                evolution.append("Modern framework adoption")
        
        return evolution
    
    def _analyze_project_scale_growth(self, github_profile: GitHubProfile) -> List[str]:
        """Analyze project scale growth."""
        growth = []
        
        # Stars as indicator of project scale
        if github_profile.total_stars_received > 200:
            growth.append("Large-scale project success")
        elif github_profile.total_stars_received > 50:
            growth.append("Medium-scale project impact")
        
        # Repository count growth
        if github_profile.total_repositories > 30:
            growth.append("Extensive portfolio development")
        
        return growth
    
    def _identify_responsibility_indicators(self, github_profile: GitHubProfile) -> List[str]:
        """Identify indicators of responsibility and ownership."""
        indicators = []
        
        # Original vs forked repositories
        if github_profile.original_repositories > github_profile.forked_repositories:
            indicators.append("Original project creator")
        
        # Documentation responsibility
        if hasattr(github_profile, 'repositories_with_readme'):
            readme_ratio = github_profile.repositories_with_readme / max(github_profile.total_repositories, 1)
            if readme_ratio > 0.7:
                indicators.append("Documentation ownership")
        
        # Quality assurance responsibility
        if hasattr(github_profile, 'repositories_with_tests'):
            test_ratio = github_profile.repositories_with_tests / max(github_profile.total_repositories, 1)
            if test_ratio > 0.4:
                indicators.append("Quality assurance leadership")
        
        return indicators
    
    def _identify_unique_projects(self, github_profile: GitHubProfile) -> List[str]:
        """Identify unique or standout projects."""
        unique = []
        
        # High-impact projects (by stars)
        sorted_projects = sorted(github_profile.featured_projects, 
                               key=lambda x: x.get('stars', 0), reverse=True)
        
        for project in sorted_projects[:3]:
            if project.get('stars', 0) > 10:
                unique.append(project['name'])
        
        return unique
    
    def _identify_innovative_solutions(self, github_profile: GitHubProfile) -> List[str]:
        """Identify innovative solutions."""
        solutions = []
        
        # Look for innovation keywords in project descriptions
        innovation_keywords = ['ai', 'ml', 'blockchain', 'automation', 'optimization', 'real-time']
        
        for project in github_profile.featured_projects:
            desc = project.get('description', '').lower()
            if any(keyword in desc for keyword in innovation_keywords):
                solutions.append(f"Innovative {project['name']}")
        
        return solutions[:3]  # Top 3
    
    def _identify_cross_functional_skills(self, github_profile: GitHubProfile) -> List[str]:
        """Identify cross-functional skills."""
        skills = []
        
        # Frontend + Backend
        frontend_langs = {"JavaScript", "TypeScript", "HTML", "CSS"}
        backend_langs = {"Python", "Java", "Go", "C#", "PHP", "Ruby"}
        
        has_frontend = any(lang in frontend_langs for lang in github_profile.primary_languages)
        has_backend = any(lang in backend_langs for lang in github_profile.primary_languages)
        
        if has_frontend and has_backend:
            skills.append("Full-stack development")
        
        # DevOps indicators
        if hasattr(github_profile, 'repositories_with_docker') and github_profile.repositories_with_docker > 0:
            skills.append("DevOps & Infrastructure")
        
        # Data skills
        if "Python" in github_profile.primary_languages:
            skills.append("Data analysis & automation")
        
        # Mobile development
        mobile_langs = {"Swift", "Kotlin", "Dart", "Java"}
        if any(lang in mobile_langs for lang in github_profile.primary_languages):
            skills.append("Mobile development")
        
        return skills
    
    def generate_ai_bio(self, github_profile: GitHubProfile, config: AIBioConfig = None) -> AIGeneratedBio:
        """Generate AI-powered LinkedIn bio."""
        if config:
            self.config = config
        
        self.logger.info("🤖 Generating AI-powered LinkedIn bio...")
        
        # Perform comprehensive analysis
        analysis = self.analyze_repositories_for_bio(github_profile)
        
        # Generate bio components
        bio_components = self._generate_bio_components(github_profile, analysis)
        
        # Assemble primary bio
        primary_bio = self._assemble_primary_bio(bio_components)
        
        # Generate alternative versions
        alternatives = self._generate_alternative_versions(github_profile, analysis, bio_components)
        
        # Create optimization data
        optimization_data = self._calculate_optimization_metrics(primary_bio)
        
        generated_bio = AIGeneratedBio(
            primary_bio=primary_bio,
            alternative_versions=alternatives,
            **bio_components,
            **optimization_data
        )
        
        self.logger.info("✅ AI bio generation complete")
        return generated_bio
    
    def _generate_bio_components(self, github_profile: GitHubProfile, analysis: AIBioAnalysis) -> Dict[str, str]:
        """Generate individual bio components."""
        components = {}
        
        # Get template based on style
        template = self.bio_templates.get(self.config.bio_style, self.bio_templates["professional"])
        
        # Generate opening hook
        components["opening_hook"] = self._generate_opening_hook(github_profile, analysis, template)
        
        # Generate expertise statement
        components["expertise_statement"] = self._generate_expertise_statement(github_profile, analysis, template)
        
        # Generate achievement highlights
        components["achievement_highlights"] = self._generate_achievement_highlights(github_profile, analysis, template)
        
        # Generate value proposition
        components["value_proposition"] = self._generate_value_proposition(github_profile, analysis, template)
        
        # Generate passion statement
        if self.config.include_passion_statement:
            components["passion_statement"] = self._generate_passion_statement(github_profile, analysis, template)
        else:
            components["passion_statement"] = ""
        
        # Generate call to action
        if self.config.include_call_to_action:
            components["call_to_action"] = self._generate_call_to_action(github_profile, analysis, template)
        else:
            components["call_to_action"] = ""
        
        return components
    
    def _generate_opening_hook(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, template: Dict) -> str:
        """Generate opening hook."""
        opening_templates = template.get("opening", [])
        
        # Select template based on analysis
        selected_template = opening_templates[0] if opening_templates else "Experienced {role} with expertise in {technologies}"
        
        # Fill template variables
        variables = {
            "role": self.config.target_role,
            "years": self._estimate_experience_years(github_profile),
            "domain": self._get_primary_domain(analysis),
            "experience_level": self.config.experience_level.title(),
            "primary_focus": self._get_primary_focus(analysis),
            "expertise_areas": ", ".join(analysis.domain_expertise[:2]),
            "technologies": ", ".join(analysis.primary_languages[:3])
        }
        
        return self._fill_template(selected_template, variables)
    
    def _generate_expertise_statement(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, template: Dict) -> str:
        """Generate expertise statement."""
        expertise_templates = template.get("expertise", [])
        
        selected_template = expertise_templates[0] if expertise_templates else "Expert in {technologies} with proven experience in {domains}"
        
        variables = {
            "technologies": ", ".join(analysis.primary_languages[:4]),
            "domains": ", ".join(analysis.domain_expertise[:3]),
            "tech_stack": f"{analysis.primary_languages[0] if analysis.primary_languages else 'modern technologies'}",
            "methodologies": "agile development and DevOps practices",
            "focus_areas": ", ".join(self.config.focus_areas),
            "detailed_technologies": f"{', '.join(analysis.primary_languages[:3])} with {', '.join(analysis.frameworks_mastery[:3])}"
        }
        
        return self._fill_template(selected_template, variables)
    
    def _generate_achievement_highlights(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, template: Dict) -> str:
        """Generate achievement highlights."""
        achievement_templates = template.get("achievements", [])
        
        selected_template = achievement_templates[0] if achievement_templates else "Built {project_count} successful projects with {community_impact}"
        
        variables = {
            "achievement_count": len(github_profile.featured_projects),
            "project_count": analysis.total_repositories,
            "impact": f"{analysis.stars_received} stars and {analysis.forks_received} forks",
            "project_types": ", ".join(analysis.diverse_projects[:3]),
            "scale": self._calculate_impact_scale(analysis),
            "specific_outcomes": self._get_specific_outcomes(analysis),
            "quantified_results": f"{analysis.stars_received} GitHub stars",
            "notable_projects": ", ".join(analysis.unique_projects[:2]),
            "impact_description": "gained significant community recognition",
            "specific_achievements": f"earned {analysis.stars_received} stars across multiple projects"
        }
        
        return self._fill_template(selected_template, variables)
    
    def _generate_value_proposition(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, template: Dict) -> str:
        """Generate value proposition."""
        value_templates = template.get("value", [])
        
        if self.config.value_proposition:
            return self.config.value_proposition
        
        selected_template = value_templates[0] if value_templates else "I deliver high-quality solutions that drive measurable impact"
        
        variables = {}
        
        return self._fill_template(selected_template, variables)
    
    def _generate_passion_statement(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, template: Dict) -> str:
        """Generate passion statement."""
        passion_templates = template.get("passion", [])
        
        selected_template = passion_templates[0] if passion_templates else "Passionate about {passion_areas} and continuous learning"
        
        variables = {
            "passion_areas": ", ".join(analysis.domain_expertise[:2]),
            "motivations": "delivering excellence and driving innovation",
            "interests": ", ".join(analysis.innovation_indicators[:2]),
            "emerging_tech": "emerging technologies",
            "technical_practices": "clean code and best practices",
            "quality_standards": "high-quality software development",
            "technical_growth": "continuous learning",
            "community_contribution": "open source contribution"
        }
        
        return self._fill_template(selected_template, variables)
    
    def _generate_call_to_action(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, template: Dict) -> str:
        """Generate call to action."""
        cta_templates = template.get("cta", [])
        
        selected_template = cta_templates[0] if cta_templates else "Let's connect to discuss {topics}"
        
        variables = {
            "topics": f"{', '.join(analysis.domain_expertise[:2])} and innovation",
            "opportunities": f"{self.config.target_role.lower()} opportunities",
            "collaboration_areas": "technology and product development",
            "technical_topics": "architecture and engineering best practices",
            "technical_interests": f"{analysis.primary_languages[0] if analysis.primary_languages else 'technology'} development",
            "technical_collaboration": "engineering excellence and mentorship"
        }
        
        return self._fill_template(selected_template, variables)
    
    def _assemble_primary_bio(self, components: Dict[str, str]) -> str:
        """Assemble components into primary bio."""
        bio_parts = []
        
        # Add components in order
        if components.get("opening_hook"):
            bio_parts.append(components["opening_hook"])
        
        if components.get("expertise_statement"):
            bio_parts.append(components["expertise_statement"])
        
        if components.get("achievement_highlights"):
            bio_parts.append(components["achievement_highlights"])
        
        if components.get("value_proposition"):
            bio_parts.append(components["value_proposition"])
        
        if components.get("passion_statement"):
            bio_parts.append(components["passion_statement"])
        
        if components.get("call_to_action"):
            bio_parts.append(components["call_to_action"])
        
        # Join with appropriate spacing
        bio = " ".join(bio_parts)
        
        # Ensure proper length
        bio = self._adjust_bio_length(bio)
        
        return bio
    
    def _generate_alternative_versions(self, github_profile: GitHubProfile, analysis: AIBioAnalysis, components: Dict[str, str]) -> List[str]:
        """Generate alternative bio versions."""
        alternatives = []
        
        # Short version
        short_bio = f"{components.get('opening_hook', '')} {components.get('expertise_statement', '')}"
        if components.get("call_to_action"):
            short_bio += f" {components['call_to_action']}"
        alternatives.append(self._adjust_bio_length(short_bio, "short"))
        
        # Creative version (if not already creative style)
        if self.config.bio_style != "creative":
            creative_config = AIBioConfig()
            creative_config.bio_style = "creative"
            creative_components = self._generate_bio_components(github_profile, analysis)
            creative_bio = self._assemble_primary_bio(creative_components)
            alternatives.append(creative_bio)
        
        # Technical version (if not already technical style)
        if self.config.bio_style != "technical":
            technical_config = AIBioConfig()
            technical_config.bio_style = "technical"
            technical_components = self._generate_bio_components(github_profile, analysis)
            technical_bio = self._assemble_primary_bio(technical_components)
            alternatives.append(technical_bio)
        
        return alternatives
    
    def _calculate_optimization_metrics(self, bio: str) -> Dict[str, Any]:
        """Calculate optimization metrics for the bio."""
        metrics = {}
        
        # Keyword density
        metrics["keyword_density"] = self._calculate_keyword_density(bio)
        
        # Readability score
        metrics["readability_score"] = self._calculate_readability_score(bio)
        
        # Engagement potential
        metrics["engagement_potential"] = self._assess_engagement_potential(bio)
        
        # SEO optimization
        metrics["search_optimization_score"] = self._calculate_seo_score(bio)
        
        # Keywords used
        metrics["primary_keywords_used"] = self._extract_used_keywords(bio, self.config.primary_keywords)
        metrics["industry_keywords_used"] = self._extract_used_keywords(bio, self.industry_keywords.get(self.config.target_industry, []))
        
        # Uniqueness and authenticity
        metrics["uniqueness_score"] = self._calculate_uniqueness_score(bio)
        metrics["authenticity_indicators"] = self._identify_authenticity_indicators(bio)
        
        return metrics
    
    def _fill_template(self, template: str, variables: Dict[str, str]) -> str:
        """Fill template with variables, handling missing variables gracefully."""
        # Default values for common template variables
        default_values = {
            'role': 'Software Engineer',
            'years': '3+',
            'domain': 'software development',
            'experience_level': 'Senior',
            'primary_focus': 'innovation',
            'expertise_areas': 'software development',
            'technologies': 'modern technologies',
            'domains': 'technology',
            'tech_stack': 'modern tech stack',
            'methodologies': 'agile and DevOps',
            'focus_areas': 'innovation',
            'detailed_technologies': 'cutting-edge technologies',
            'achievement_count': '5',
            'project_count': '10',
            'impact': 'significant community impact',
            'project_types': 'innovative projects',
            'scale': 'global developers',
            'specific_outcomes': 'improved efficiency',
            'quantified_results': 'measurable results',
            'notable_projects': 'key projects',
            'impact_description': 'gained recognition',
            'specific_achievements': 'delivered value',
            'passion_areas': 'technology and innovation',
            'motivations': 'excellence and growth',
            'interests': 'emerging technologies',
            'emerging_tech': 'AI and machine learning',
            'technical_practices': 'best practices',
            'quality_standards': 'high standards',
            'technical_growth': 'continuous learning',
            'community_contribution': 'open source',
            'research_areas': 'emerging technologies',
            'topics': 'technology and innovation',
            'opportunities': 'new opportunities',
            'collaboration_areas': 'technology projects',
            'technical_topics': 'software architecture',
            'technical_interests': 'technology',
            'technical_collaboration': 'engineering excellence',
            'unique_skill': 'problem solving',
            'hobbies': 'exploring new technologies',
            'technical_domains': 'software engineering',
            'patterns': 'modern architectures',
            'performance_metrics': 'optimal performance',
            'emerging_technologies': 'AI and cloud technologies',
            'solutions': 'innovative software solutions',
            'innovation_area': 'technology innovation',
            'business_skills': 'strategic thinking',
            'domain_expertise': 'full-stack development',
            'feature_count': '50+',
            'user_count': '10,000+',
            'value_proposition': 'cutting-edge solutions',
            'business_results': 'measurable impact',
            'product_focus': 'user experience',
            'user_experience': 'seamless interfaces',
            'methodologies': 'agile practices',
            'industry_trends': 'emerging technologies',
            'emerging_opportunities': 'innovation areas',
            'collaboration_opportunities': 'exciting projects',
            'startup_topics': 'technology and innovation',
            'title': 'Technology Leader',
            'strategic_focus': 'digital innovation',
            'achievements': 'significant milestones',
            'business_impact': 'measurable outcomes',
            'technical_background': 'engineering excellence',
            'areas': 'technology domains',
            'departments': 'engineering teams',
            'team_size': '20+',
            'scale_from': 'startup',
            'scale_to': 'enterprise',
            'strategic_initiatives': 'key programs',
            'leadership_focus': 'team development',
            'organizational_development': 'culture building',
            'values': 'excellence and integrity',
            'strategic_vision': 'technology leadership',
            'motivations': 'driving innovation',
            'long_term_goals': 'industry impact',
            'products': 'innovative solutions',
            'scale': '1M+ users',
            'frontend': 'React/Vue',
            'backend': 'Node.js/Python',
            'infrastructure': 'AWS/Azure'
        }
        
        # Merge provided variables with defaults
        filled_variables = {**default_values, **variables}
        
        try:
            return template.format(**filled_variables)
        except KeyError as e:
            # Handle any remaining missing variables
            missing_key = str(e).strip("'\"")
            filled_variables[missing_key] = f"[{missing_key}]"
            return template.format(**filled_variables)
    
    def _estimate_experience_years(self, github_profile: GitHubProfile) -> str:
        """Estimate experience years based on repository count and activity."""
        repo_count = github_profile.total_repositories
        
        if repo_count > 50:
            return "5+"
        elif repo_count > 30:
            return "3-5"
        elif repo_count > 15:
            return "2-3"
        else:
            return "1-2"
    
    def _get_primary_domain(self, analysis: AIBioAnalysis) -> str:
        """Get primary domain expertise."""
        return analysis.domain_expertise[0] if analysis.domain_expertise else "software development"
    
    def _get_primary_focus(self, analysis: AIBioAnalysis) -> str:
        """Get primary focus area."""
        if analysis.innovation_indicators:
            return analysis.innovation_indicators[0].lower()
        elif analysis.domain_expertise:
            return analysis.domain_expertise[0].lower()
        else:
            return "software development"
    
    def _calculate_impact_scale(self, analysis: AIBioAnalysis) -> str:
        """Calculate impact scale description."""
        stars = analysis.stars_received
        
        if stars > 500:
            return "thousands of developers"
        elif stars > 100:
            return "hundreds of developers"
        elif stars > 20:
            return "dozens of developers"
        else:
            return "the developer community"
    
    def _get_specific_outcomes(self, analysis: AIBioAnalysis) -> str:
        """Get specific outcomes description."""
        if analysis.innovation_indicators:
            return f"enhanced developer productivity through {analysis.innovation_indicators[0].lower()}"
        else:
            return "improved code quality and performance"
    
    def _adjust_bio_length(self, bio: str, target_length: str = None) -> str:
        """Adjust bio length to meet requirements."""
        target_length = target_length or self.config.length
        
        word_count = len(bio.split())
        
        if target_length == "short" and word_count > 50:
            # Truncate to ~50 words
            words = bio.split()[:50]
            bio = " ".join(words) + "..."
        elif target_length == "medium" and word_count > 100:
            # Truncate to ~100 words
            words = bio.split()[:100]
            bio = " ".join(words) + "..."
        elif target_length == "long" and word_count > 150:
            # Truncate to ~150 words
            words = bio.split()[:150]
            bio = " ".join(words) + "..."
        
        return bio
    
    def _calculate_keyword_density(self, bio: str) -> Dict[str, float]:
        """Calculate keyword density."""
        words = bio.lower().split()
        total_words = len(words)
        
        density = {}
        for keyword in self.config.primary_keywords:
            count = sum(1 for word in words if keyword.lower() in word)
            density[keyword] = (count / total_words) * 100 if total_words > 0 else 0
        
        return density
    
    def _calculate_readability_score(self, bio: str) -> float:
        """Calculate readability score (simplified)."""
        sentences = bio.count('.') + bio.count('!') + bio.count('?')
        words = len(bio.split())
        
        if sentences == 0:
            return 50.0  # Neutral score
        
        avg_sentence_length = words / sentences
        
        # Simple readability score (0-100, higher is better)
        if avg_sentence_length <= 15:
            return 85.0  # Good readability
        elif avg_sentence_length <= 20:
            return 70.0  # Fair readability
        else:
            return 55.0  # Could be improved
    
    def _assess_engagement_potential(self, bio: str) -> str:
        """Assess engagement potential."""
        engagement_indicators = [
            "passionate", "innovative", "love", "excited", "driven",
            "enthusiastic", "committed", "dedicated", "obsessed"
        ]
        
        bio_lower = bio.lower()
        indicators_found = sum(1 for indicator in engagement_indicators if indicator in bio_lower)
        
        if indicators_found >= 3:
            return "high"
        elif indicators_found >= 1:
            return "medium"
        else:
            return "low"
    
    def _calculate_seo_score(self, bio: str) -> float:
        """Calculate SEO optimization score."""
        bio_lower = bio.lower()
        
        score = 0.0
        
        # Check for target role
        if self.config.target_role.lower() in bio_lower:
            score += 20
        
        # Check for industry keywords
        industry_keywords = self.industry_keywords.get(self.config.target_industry, [])
        keyword_count = sum(1 for keyword in industry_keywords if keyword in bio_lower)
        score += min(keyword_count * 5, 30)  # Max 30 points
        
        # Check for primary keywords
        primary_keyword_count = sum(1 for keyword in self.config.primary_keywords if keyword.lower() in bio_lower)
        score += min(primary_keyword_count * 10, 30)  # Max 30 points
        
        # Check for action words
        action_words = ["built", "created", "developed", "led", "managed", "designed", "architected"]
        action_count = sum(1 for word in action_words if word in bio_lower)
        score += min(action_count * 4, 20)  # Max 20 points
        
        return min(score, 100.0)
    
    def _extract_used_keywords(self, bio: str, keyword_list: List[str]) -> List[str]:
        """Extract keywords that are used in the bio."""
        bio_lower = bio.lower()
        return [keyword for keyword in keyword_list if keyword.lower() in bio_lower]
    
    def _calculate_uniqueness_score(self, bio: str) -> float:
        """Calculate uniqueness score."""
        # Simple uniqueness calculation based on specific details
        specific_indicators = [
            "github", "open source", "stars", "repositories", "projects",
            "ai", "ml", "machine learning", "automation", "optimization"
        ]
        
        bio_lower = bio.lower()
        specific_count = sum(1 for indicator in specific_indicators if indicator in bio_lower)
        
        # Score from 0-100
        return min(specific_count * 15, 100.0)
    
    def _identify_authenticity_indicators(self, bio: str) -> List[str]:
        """Identify authenticity indicators."""
        indicators = []
        
        bio_lower = bio.lower()
        
        if any(word in bio_lower for word in ["github", "open source", "repositories"]):
            indicators.append("Technical authenticity")
        
        if any(word in bio_lower for word in ["passionate", "love", "excited", "driven"]):
            indicators.append("Personal passion")
        
        if any(word in bio_lower for word in ["built", "created", "developed", "led"]):
            indicators.append("Concrete achievements")
        
        if re.search(r'\d+', bio):
            indicators.append("Quantified results")
        
        return indicators


# Export classes
__all__ = [
    'AIBioConfig',
    'AIBioAnalysis', 
    'AIGeneratedBio',
    'AILinkedInBioGenerator'
]