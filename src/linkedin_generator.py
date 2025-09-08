#!/usr/bin/env python3
"""
LinkedIn Profile Generator/Improver

Analyzes GitHub profile data and generates optimized LinkedIn profile content
including headlines, summaries, experience descriptions, and skill recommendations.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter

try:
    from .profile_builder import GitHubProfile
    from .utils.logger import get_logger
except ImportError:
    from profile_builder import GitHubProfile
    from utils.logger import get_logger


@dataclass
class LinkedInConfig:
    """Configuration for LinkedIn profile generation."""
    
    # Content Style
    tone: str = "professional"  # professional, approachable, authoritative, creative
    length: str = "medium"      # short, medium, long
    include_emojis: bool = False
    use_first_person: bool = True
    
    # Content Focus
    focus_on_results: bool = True
    highlight_leadership: bool = False
    emphasize_innovation: bool = True
    include_personal_touches: bool = False
    
    # Target Positioning
    target_role: Optional[str] = None
    target_industry: Optional[str] = None
    career_level: Optional[str] = None  # entry, mid, senior, executive
    
    # LinkedIn-specific
    optimize_for_keywords: bool = True
    include_call_to_action: bool = True
    mention_open_to_opportunities: bool = False
    
    # Customization
    personal_brand_keywords: List[str] = field(default_factory=list)
    company_preferences: List[str] = field(default_factory=list)
    location_preferences: List[str] = field(default_factory=list)


@dataclass
class LinkedInProfile:
    """Generated LinkedIn profile content."""
    
    # Header Section
    headline: str = ""
    current_position: str = ""
    location: str = ""
    
    # About/Summary Section
    summary: str = ""
    summary_short: str = ""  # 2-sentence version
    summary_long: str = ""   # Extended version
    
    # Experience Descriptions
    experience_descriptions: List[Dict[str, Any]] = field(default_factory=list)
    project_descriptions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Skills & Endorsements
    top_skills: List[str] = field(default_factory=list)
    skill_categories: Dict[str, List[str]] = field(default_factory=dict)
    
    # Content Suggestions
    post_ideas: List[str] = field(default_factory=list)
    article_topics: List[str] = field(default_factory=list)
    
    # Networking
    connection_targets: List[str] = field(default_factory=list)
    industry_keywords: List[str] = field(default_factory=list)
    
    # Optimization Tips
    profile_improvement_tips: List[str] = field(default_factory=list)
    keyword_optimization: List[str] = field(default_factory=list)
    
    # Metadata
    generated_date: str = ""
    config_used: Optional[LinkedInConfig] = None


class LinkedInGenerator:
    """Generates optimized LinkedIn profile content from GitHub data."""
    
    def __init__(self, config: LinkedInConfig = None):
        """Initialize the LinkedIn generator."""
        self.config = config or LinkedInConfig()
        self.logger = get_logger()
        
        # Industry keywords mapping
        self.industry_keywords = {
            'fintech': ['financial technology', 'payments', 'blockchain', 'cryptocurrency', 'trading', 'banking'],
            'healthtech': ['healthcare technology', 'medical software', 'telemedicine', 'health informatics', 'HIPAA'],
            'edtech': ['educational technology', 'e-learning', 'online education', 'learning management', 'MOOC'],
            'ecommerce': ['e-commerce', 'online retail', 'marketplace', 'payment processing', 'inventory management'],
            'saas': ['software as a service', 'cloud computing', 'subscription model', 'B2B software', 'enterprise'],
            'gaming': ['game development', 'interactive entertainment', 'mobile games', 'game engine', 'VR/AR'],
            'iot': ['internet of things', 'connected devices', 'embedded systems', 'sensor networks', 'smart devices'],
            'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'natural language processing', 'computer vision'],
            'cybersecurity': ['information security', 'cybersecurity', 'threat detection', 'security architecture', 'penetration testing']
        }
        
        # Role-specific keywords
        self.role_keywords = {
            'frontend developer': ['React', 'Vue', 'Angular', 'JavaScript', 'TypeScript', 'CSS', 'HTML', 'responsive design', 'user experience'],
            'backend developer': ['API development', 'microservices', 'database design', 'server architecture', 'RESTful services'],
            'full stack developer': ['full-stack development', 'end-to-end solutions', 'frontend and backend', 'complete software solutions'],
            'mobile developer': ['iOS development', 'Android development', 'mobile applications', 'app store', 'mobile UX'],
            'devops engineer': ['continuous integration', 'continuous deployment', 'infrastructure as code', 'containerization', 'cloud platforms'],
            'data scientist': ['data analysis', 'machine learning', 'statistical modeling', 'data visualization', 'big data'],
            'software architect': ['system architecture', 'technical leadership', 'scalable solutions', 'design patterns', 'technology strategy'],
            'product manager': ['product strategy', 'roadmap planning', 'stakeholder management', 'user research', 'agile development'],
            'tech lead': ['technical leadership', 'team management', 'code review', 'mentoring', 'technical decision making']
        }
    
    def generate_linkedin_profile(self, github_profile: GitHubProfile, 
                                 additional_info: Dict[str, Any] = None) -> LinkedInProfile:
        """Generate complete LinkedIn profile from GitHub data."""
        self.logger.info(f"Generating LinkedIn profile for {github_profile.username}")
        
        linkedin_profile = LinkedInProfile()
        linkedin_profile.generated_date = datetime.now().isoformat()
        linkedin_profile.config_used = self.config
        
        additional_info = additional_info or {}
        
        # Generate each section
        linkedin_profile.headline = self._generate_headline(github_profile, additional_info)
        linkedin_profile.current_position = self._generate_current_position(github_profile)
        linkedin_profile.location = github_profile.location or additional_info.get('location', '')
        
        # Generate summaries of different lengths
        linkedin_profile.summary = self._generate_summary(github_profile, additional_info)
        linkedin_profile.summary_short = self._generate_summary_short(github_profile)
        linkedin_profile.summary_long = self._generate_summary_long(github_profile, additional_info)
        
        # Generate experience and project descriptions
        linkedin_profile.experience_descriptions = self._generate_experience_descriptions(github_profile, additional_info)
        linkedin_profile.project_descriptions = self._generate_project_descriptions(github_profile)
        
        # Skills and categories
        linkedin_profile.top_skills = self._generate_top_skills(github_profile)
        linkedin_profile.skill_categories = self._generate_skill_categories(github_profile)
        
        # Content suggestions
        linkedin_profile.post_ideas = self._generate_post_ideas(github_profile)
        linkedin_profile.article_topics = self._generate_article_topics(github_profile)
        
        # Networking and optimization
        linkedin_profile.connection_targets = self._generate_connection_targets(github_profile)
        linkedin_profile.industry_keywords = self._generate_industry_keywords(github_profile)
        linkedin_profile.profile_improvement_tips = self._generate_improvement_tips(github_profile)
        linkedin_profile.keyword_optimization = self._generate_keyword_optimization(github_profile)
        
        self.logger.info("LinkedIn profile generated successfully")
        return linkedin_profile
    
    def _generate_headline(self, profile: GitHubProfile, additional_info: Dict[str, Any]) -> str:
        """Generate LinkedIn headline (220 character limit)."""
        target_role = self.config.target_role or profile.developer_type
        experience_level = profile.experience_level
        
        # Primary role description
        if experience_level.lower() in ['senior', 'lead']:
            role_prefix = experience_level
        else:
            role_prefix = ""
        
        role_desc = f"{role_prefix} {target_role}".strip()
        
        # Key technologies
        top_langs = profile.primary_languages[:3]
        tech_stack = " | ".join(top_langs) if top_langs else ""
        
        # Specializations
        specializations = []
        if profile.has_web_projects and profile.has_mobile_projects:
            specializations.append("Full-Stack")
        elif profile.has_web_projects:
            specializations.append("Web Development")
        elif profile.has_mobile_projects:
            specializations.append("Mobile Development")
        
        if profile.has_apis:
            specializations.append("API Development")
        if profile.has_cli_tools:
            specializations.append("Developer Tools")
        
        # Results/metrics
        results = []
        if profile.total_stars_received > 100:
            results.append(f"{profile.total_stars_received}+ GitHub Stars")
        if profile.original_repositories > 20:
            results.append(f"{profile.original_repositories} Projects")
        
        # Industry focus
        industry_focus = ""
        if self.config.target_industry:
            industry_focus = f" in {self.config.target_industry}"
        
        # Company/open to opportunities
        opportunity_text = ""
        if self.config.mention_open_to_opportunities:
            opportunity_text = " | Open to New Opportunities"
        
        # Build headline variations and choose the best fit
        variations = []
        
        # Variation 1: Role + Tech + Results
        if tech_stack and results:
            v1 = f"{role_desc} | {tech_stack} | {results[0]}{opportunity_text}"
            if len(v1) <= 220:
                variations.append(v1)
        
        # Variation 2: Role + Specializations + Industry
        if specializations:
            spec_text = " & ".join(specializations[:2])
            v2 = f"{role_desc} specializing in {spec_text}{industry_focus}{opportunity_text}"
            if len(v2) <= 220:
                variations.append(v2)
        
        # Variation 3: Simple role + top tech + value prop
        if top_langs:
            v3 = f"{role_desc} | {top_langs[0]} & {top_langs[1] if len(top_langs) > 1 else 'Full-Stack'} | Building scalable solutions{opportunity_text}"
            if len(v3) <= 220:
                variations.append(v3)
        
        # Variation 4: Experienced + role + focus
        v4 = f"Experienced {target_role} | {tech_stack or 'Multi-stack'} | Passionate about open source{opportunity_text}"
        if len(v4) <= 220:
            variations.append(v4)
        
        # Default fallback
        if not variations:
            fallback = f"{role_desc} | {tech_stack[:50] if tech_stack else 'Software Development'}{opportunity_text}"
            variations.append(fallback[:220])
        
        return variations[0]
    
    def _generate_current_position(self, profile: GitHubProfile) -> str:
        """Generate current position title."""
        if self.config.target_role:
            return self.config.target_role
        
        # Infer position from profile data
        if profile.experience_level.lower() == 'senior':
            return f"Senior {profile.developer_type}"
        elif profile.experience_level.lower() == 'lead':
            return f"Lead {profile.developer_type}"
        else:
            return profile.developer_type
    
    def _generate_summary(self, profile: GitHubProfile, additional_info: Dict[str, Any]) -> str:
        """Generate main LinkedIn summary (2000 character limit)."""
        if self.config.length == "short":
            return self._generate_summary_short(profile)
        elif self.config.length == "long":
            return self._generate_summary_long(profile, additional_info)
        else:
            return self._generate_summary_medium(profile, additional_info)
    
    def _generate_summary_short(self, profile: GitHubProfile) -> str:
        """Generate short summary (2 sentences)."""
        experience_level = profile.experience_level.lower()
        developer_type = profile.developer_type
        
        # Opening sentence
        if experience_level in ['senior', 'lead']:
            opening = f"I'm a {experience_level} {developer_type.lower()} with a passion for building innovative software solutions."
        else:
            opening = f"I'm a {developer_type.lower()} passionate about creating impactful software solutions."
        
        # Second sentence with metrics
        if profile.total_repositories > 10 and profile.total_stars_received > 20:
            closing = f"With {profile.original_repositories} open-source projects and {profile.total_stars_received} GitHub stars, I love sharing knowledge and collaborating with the developer community."
        elif profile.total_repositories > 5:
            closing = f"I've built {profile.original_repositories} open-source projects and enjoy collaborating with fellow developers."
        else:
            closing = f"I specialize in {', '.join(profile.primary_languages[:2])} and enjoy tackling complex technical challenges."
        
        return f"{opening} {closing}"
    
    def _generate_summary_medium(self, profile: GitHubProfile, additional_info: Dict[str, Any]) -> str:
        """Generate medium-length summary (3-4 paragraphs)."""
        paragraphs = []
        
        # Paragraph 1: Introduction and main value proposition
        intro = self._generate_intro_paragraph(profile, additional_info)
        paragraphs.append(intro)
        
        # Paragraph 2: Technical expertise and experience
        tech_para = self._generate_technical_paragraph(profile)
        paragraphs.append(tech_para)
        
        # Paragraph 3: Achievements and results
        achievements_para = self._generate_achievements_paragraph(profile)
        paragraphs.append(achievements_para)
        
        # Paragraph 4: Call to action or future focus
        if self.config.include_call_to_action:
            cta_para = self._generate_cta_paragraph(profile)
            paragraphs.append(cta_para)
        
        return "\n\n".join(paragraphs)
    
    def _generate_summary_long(self, profile: GitHubProfile, additional_info: Dict[str, Any]) -> str:
        """Generate extended summary."""
        # Start with medium summary
        base_summary = self._generate_summary_medium(profile, additional_info)
        
        # Add additional paragraphs
        additional_paras = []
        
        # Personal philosophy or approach paragraph
        philosophy_para = self._generate_philosophy_paragraph(profile)
        if philosophy_para:
            additional_paras.append(philosophy_para)
        
        # Industry insights or trends paragraph
        if self.config.target_industry:
            industry_para = self._generate_industry_paragraph(profile)
            if industry_para:
                additional_paras.append(industry_para)
        
        # Personal interests or community involvement
        if self.config.include_personal_touches:
            personal_para = self._generate_personal_paragraph(profile, additional_info)
            if personal_para:
                additional_paras.append(personal_para)
        
        if additional_paras:
            return base_summary + "\n\n" + "\n\n".join(additional_paras)
        else:
            return base_summary
    
    def _generate_intro_paragraph(self, profile: GitHubProfile, additional_info: Dict[str, Any]) -> str:
        """Generate introduction paragraph."""
        name = profile.name.split()[0] if profile.name else "I"
        pronoun = "I'm" if self.config.use_first_person else f"{name} is"
        pronoun_possess = "my" if self.config.use_first_person else f"{name}'s"
        
        experience_level = profile.experience_level.lower()
        developer_type = profile.developer_type.lower()
        
        # Opening statement
        if experience_level in ['senior', 'lead']:
            opening = f"{pronoun} a {experience_level} {developer_type} with a proven track record of delivering high-impact software solutions."
        else:
            opening = f"{pronoun} a passionate {developer_type} dedicated to crafting innovative software that solves real-world problems."
        
        # Value proposition
        value_props = []
        if profile.collaboration_score > 70:
            value_props.append("collaborative approach to development")
        if profile.innovation_score > 70:
            value_props.append("focus on cutting-edge technologies")
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.8:
            value_props.append("commitment to clean, well-documented code")
        
        if value_props:
            value_text = f"Known for {pronoun_possess} {' and '.join(value_props[:2])}"
        else:
            value_text = f"Committed to writing clean, maintainable code and delivering exceptional user experiences"
        
        # Industry/domain focus
        domain_focus = ""
        if self.config.target_industry:
            domain_focus = f" in the {self.config.target_industry} space"
        
        return f"{opening} {value_text}{domain_focus}."
    
    def _generate_technical_paragraph(self, profile: GitHubProfile) -> str:
        """Generate technical expertise paragraph."""
        pronoun_possess = "My" if self.config.use_first_person else "Their"
        
        # Core technologies
        top_languages = profile.primary_languages[:4]
        if len(top_languages) > 2:
            tech_list = ", ".join(top_languages[:-1]) + f", and {top_languages[-1]}"
        elif len(top_languages) == 2:
            tech_list = f"{top_languages[0]} and {top_languages[1]}"
        else:
            tech_list = top_languages[0] if top_languages else "multiple programming languages"
        
        tech_intro = f"{pronoun_possess} technical expertise spans {tech_list}"
        
        # Specializations
        specializations = []
        if profile.has_web_projects:
            specializations.append("web application development")
        if profile.has_mobile_projects:
            specializations.append("mobile app development")
        if profile.has_apis:
            specializations.append("API design and development")
        if profile.has_libraries:
            specializations.append("open-source library development")
        if profile.has_cli_tools:
            specializations.append("developer tooling")
        
        if specializations:
            if len(specializations) > 2:
                spec_text = ", ".join(specializations[:-1]) + f", and {specializations[-1]}"
            elif len(specializations) == 2:
                spec_text = f"{specializations[0]} and {specializations[1]}"
            else:
                spec_text = specializations[0]
            
            tech_intro += f", with particular strengths in {spec_text}"
        
        # Development practices
        practices = []
        if profile.repositories_with_tests > 0:
            practices.append("test-driven development")
        if profile.repositories_with_ci > 0:
            practices.append("continuous integration")
        if profile.repositories_with_docker > 0:
            practices.append("containerization")
        if profile.collaboration_score > 60:
            practices.append("collaborative development")
        
        if practices:
            practices_text = f" Following best practices in {' and '.join(practices[:2])}"
            tech_intro += f".{practices_text}"
        
        return tech_intro + "."
    
    def _generate_achievements_paragraph(self, profile: GitHubProfile) -> str:
        """Generate achievements paragraph."""
        pronoun = "I've" if self.config.use_first_person else "They've"
        pronoun_possess = "my" if self.config.use_first_person else "their"
        
        achievements = []
        
        # Repository achievements
        if profile.original_repositories > 20:
            achievements.append(f"built and maintained {profile.original_repositories} open-source projects")
        elif profile.original_repositories > 5:
            achievements.append(f"created {profile.original_repositories} software projects")
        
        # Community recognition
        if profile.total_stars_received > 500:
            achievements.append(f"earned over {profile.total_stars_received} GitHub stars")
        elif profile.total_stars_received > 100:
            achievements.append(f"received {profile.total_stars_received} GitHub stars from the community")
        elif profile.total_stars_received > 20:
            achievements.append(f"gained recognition with {profile.total_stars_received} GitHub stars")
        
        # Collaboration metrics
        if profile.total_forks_received > 100:
            achievements.append(f"had {pronoun_possess} work forked over {profile.total_forks_received} times")
        elif profile.total_forks_received > 20:
            achievements.append(f"contributed to the community with {profile.total_forks_received} project forks")
        
        # Technical diversity
        if len(profile.languages_used) > 8:
            achievements.append(f"demonstrated proficiency across {len(profile.languages_used)} programming languages")
        
        if not achievements:
            # Fallback achievements
            achievements.append("contributed to multiple open-source projects")
            achievements.append("maintained high code quality standards")
        
        # Construct paragraph
        if len(achievements) >= 2:
            main_achievements = achievements[:2]
            achievement_text = f"{main_achievements[0]} and {main_achievements[1]}"
        else:
            achievement_text = achievements[0]
        
        intro = f"{pronoun} {achievement_text}"
        
        # Add impact statement
        impact_statements = [
            f"demonstrating {pronoun_possess} commitment to quality software development",
            f"reflecting {pronoun_possess} passion for sharing knowledge with the developer community",
            f"showcasing {pronoun_possess} ability to build solutions that resonate with other developers"
        ]
        
        impact = impact_statements[0]  # Choose first for consistency
        
        return f"{intro}, {impact}."
    
    def _generate_cta_paragraph(self, profile: GitHubProfile) -> str:
        """Generate call-to-action paragraph."""
        pronoun = "I'm" if self.config.use_first_person else "They're"
        contact_verb = "connect" if self.config.use_first_person else "connect with them"
        
        cta_options = []
        
        # Collaboration focus
        if self.config.mention_open_to_opportunities:
            cta_options.append(f"{pronoun} always open to discussing new opportunities and interesting projects.")
        
        # Industry networking
        if self.config.target_industry:
            cta_options.append(f"{pronoun} particularly interested in connecting with professionals in the {self.config.target_industry} industry.")
        
        # General networking
        cta_options.append(f"Feel free to {contact_verb} if you'd like to discuss technology, collaborate on projects, or share insights about software development.")
        
        # Knowledge sharing
        if profile.total_stars_received > 50:
            cta_options.append(f"{pronoun} always eager to share knowledge and learn from fellow developers.")
        
        # Choose the most appropriate CTA
        return cta_options[0]
    
    def _generate_philosophy_paragraph(self, profile: GitHubProfile) -> str:
        """Generate development philosophy paragraph."""
        if profile.total_repositories < 10:
            return ""  # Skip if not enough data
        
        pronoun = "I believe" if self.config.use_first_person else "They believe"
        
        philosophy_elements = []
        
        # Code quality philosophy
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.7:
            philosophy_elements.append("that great code tells a story through clear documentation")
        
        # Collaboration philosophy
        if profile.collaboration_score > 60:
            philosophy_elements.append("in the power of collaborative development and code review")
        
        # Innovation philosophy
        if profile.innovation_score > 60:
            philosophy_elements.append("that technology should solve real problems and create meaningful impact")
        
        # Open source philosophy
        if profile.original_repositories > 10:
            philosophy_elements.append("in giving back to the open-source community that has given so much")
        
        if not philosophy_elements:
            return ""
        
        main_philosophy = philosophy_elements[0]
        return f"{pronoun} {main_philosophy}."
    
    def _generate_industry_paragraph(self, profile: GitHubProfile) -> str:
        """Generate industry insights paragraph."""
        industry = self.config.target_industry.lower()
        pronoun = "I'm" if self.config.use_first_person else "They're"
        
        industry_insights = {
            'fintech': f"{pronoun} passionate about the intersection of finance and technology, particularly in areas like digital payments, blockchain applications, and financial data security.",
            'healthtech': f"{pronoun} excited about leveraging technology to improve healthcare outcomes, with focus on patient data privacy, telemedicine solutions, and healthcare interoperability.",
            'edtech': f"{pronoun} committed to democratizing education through technology, creating engaging learning experiences and accessible educational tools.",
            'ecommerce': f"{pronoun} fascinated by the evolving e-commerce landscape, from personalized shopping experiences to supply chain optimization.",
            'ai': f"{pronoun} at the forefront of the AI revolution, exploring how machine learning and artificial intelligence can augment human capabilities."
        }
        
        return industry_insights.get(industry, "")
    
    def _generate_personal_paragraph(self, profile: GitHubProfile, additional_info: Dict[str, Any]) -> str:
        """Generate personal interests paragraph."""
        personal_interests = additional_info.get('interests', [])
        hobbies = additional_info.get('hobbies', [])
        
        if not personal_interests and not hobbies:
            return ""
        
        pronoun = "When I'm" if self.config.use_first_person else "When they're"
        verb_enjoy = "enjoy" if self.config.use_first_person else "enjoys"
        
        interests_text = ""
        if personal_interests:
            interests_text = f"{pronoun} not coding, {verb_enjoy} {', '.join(personal_interests[:2])}"
        elif hobbies:
            interests_text = f"{pronoun} not coding, {verb_enjoy} {', '.join(hobbies[:2])}"
        
        if interests_text:
            return f"{interests_text}. These interests often inspire creative approaches to problem-solving in my development work."
        
        return ""
    
    def _generate_experience_descriptions(self, profile: GitHubProfile, 
                                        additional_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate LinkedIn-optimized experience descriptions."""
        experiences = []
        
        # Get existing work experience
        work_experience = additional_info.get('work_experience', [])
        
        if work_experience:
            # Enhance existing work experience
            for exp in work_experience:
                enhanced_exp = self._enhance_experience_description(exp, profile)
                experiences.append(enhanced_exp)
        else:
            # Create synthesized experience from GitHub activity
            synthesized_exp = self._create_synthesized_experience(profile)
            if synthesized_exp:
                experiences.append(synthesized_exp)
        
        return experiences
    
    def _enhance_experience_description(self, experience: Dict[str, Any], 
                                      profile: GitHubProfile) -> Dict[str, Any]:
        """Enhance existing experience description with GitHub insights."""
        enhanced = experience.copy()
        
        # Enhance description with action verbs and results
        original_desc = enhanced.get('description', '')
        enhanced_desc = self._rewrite_with_action_verbs(original_desc)
        enhanced['linkedin_description'] = enhanced_desc
        
        # Add GitHub-backed achievements
        github_achievements = []
        if profile.total_stars_received > 20:
            github_achievements.append(f"• Built open-source projects that earned {profile.total_stars_received} GitHub stars")
        if profile.collaboration_score > 60:
            github_achievements.append("• Demonstrated strong collaborative development practices through code reviews and contributions")
        
        enhanced['github_achievements'] = github_achievements
        
        # Suggest relevant skills to highlight
        relevant_skills = self._extract_relevant_skills(enhanced.get('technologies', []), profile)
        enhanced['suggested_skills'] = relevant_skills
        
        return enhanced
    
    def _create_synthesized_experience(self, profile: GitHubProfile) -> Optional[Dict[str, Any]]:
        """Create synthesized experience entry from GitHub activity."""
        if profile.total_repositories < 5:
            return None
        
        # Estimate career timeline
        current_year = datetime.now().year
        estimated_start = current_year - min(6, max(2, profile.total_repositories // 8))
        
        # Determine role and company
        if profile.total_stars_received > 100:
            title = "Senior Open Source Developer"
        elif profile.total_stars_received > 20:
            title = "Software Developer"
        else:
            title = "Software Developer"
        
        company = "Freelance / Open Source Community"
        
        # Generate achievements-focused description
        description = self._generate_github_based_description(profile)
        
        # Key accomplishments
        accomplishments = []
        accomplishments.append(f"Architected and developed {profile.original_repositories} open-source software projects")
        
        if profile.total_stars_received > 50:
            accomplishments.append(f"Earned {profile.total_stars_received} GitHub stars, demonstrating code quality and community value")
        
        if profile.total_forks_received > 20:
            accomplishments.append(f"Achieved {profile.total_forks_received} project forks, indicating high reusability and adoption")
        
        if len(profile.languages_used) > 5:
            accomplishments.append(f"Demonstrated proficiency across {len(profile.languages_used)} programming languages and frameworks")
        
        technologies = profile.primary_languages[:6]
        
        return {
            'title': title,
            'company': company,
            'start_date': str(estimated_start),
            'end_date': 'Present',
            'description': description,
            'linkedin_description': description,
            'accomplishments': accomplishments,
            'technologies': technologies,
            'github_backed': True
        }
    
    def _generate_github_based_description(self, profile: GitHubProfile) -> str:
        """Generate experience description based on GitHub activity."""
        description_parts = []
        
        # Main responsibilities
        if profile.has_web_projects and profile.has_mobile_projects:
            description_parts.append("Developed full-stack applications spanning web and mobile platforms")
        elif profile.has_web_projects:
            description_parts.append("Specialized in web application development using modern frameworks and technologies")
        elif profile.has_mobile_projects:
            description_parts.append("Focused on mobile application development for iOS and Android platforms")
        
        if profile.has_apis:
            description_parts.append("Designed and implemented RESTful APIs and backend services")
        
        if profile.has_libraries:
            description_parts.append("Created reusable software libraries and developer tools for the open-source community")
        
        # Technical practices
        practices = []
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.7:
            practices.append("comprehensive documentation")
        if profile.repositories_with_tests > 0:
            practices.append("test-driven development")
        if profile.collaboration_score > 60:
            practices.append("collaborative development workflows")
        
        if practices:
            practices_text = f"Maintained high standards in {' and '.join(practices[:2])}"
            description_parts.append(practices_text)
        
        return ". ".join(description_parts) + "."
    
    def _rewrite_with_action_verbs(self, description: str) -> str:
        """Rewrite description with strong action verbs."""
        if not description:
            return ""
        
        # Simple enhancement - this could be made more sophisticated
        action_verb_map = {
            'worked on': 'developed',
            'helped': 'collaborated to',
            'made': 'built',
            'did': 'executed',
            'was responsible for': 'led',
            'handled': 'managed',
            'used': 'leveraged',
            'wrote': 'authored'
        }
        
        enhanced = description
        for weak_verb, strong_verb in action_verb_map.items():
            enhanced = enhanced.replace(weak_verb, strong_verb)
        
        return enhanced
    
    def _extract_relevant_skills(self, existing_skills: List[str], profile: GitHubProfile) -> List[str]:
        """Extract relevant skills to highlight."""
        all_skills = set(existing_skills)
        all_skills.update(profile.primary_languages)
        
        # Add inferred skills
        if profile.has_web_projects:
            all_skills.update(['HTML/CSS', 'JavaScript', 'Web Development'])
        if profile.has_mobile_projects:
            all_skills.update(['Mobile Development', 'iOS', 'Android'])
        if profile.has_apis:
            all_skills.update(['REST APIs', 'API Development'])
        
        return list(all_skills)[:15]  # LinkedIn recommends max 50, but top 15 for focus
    
    def _generate_project_descriptions(self, profile: GitHubProfile) -> List[Dict[str, Any]]:
        """Generate LinkedIn-optimized project descriptions."""
        projects = []
        
        for project in profile.featured_projects[:6]:  # Top 6 projects for LinkedIn
            linkedin_project = {
                'name': project['name'],
                'description': self._enhance_project_description(project, profile),
                'technologies': [project.get('language', '')] + project.get('topics', [])[:3],
                'url': project['url'],
                'achievements': self._generate_project_achievements(project),
                'year': self._extract_year_from_date(project.get('updated_at', '')),
                'linkedin_optimized': True
            }
            projects.append(linkedin_project)
        
        return projects
    
    def _enhance_project_description(self, project: Dict[str, Any], profile: GitHubProfile) -> str:
        """Enhance project description for LinkedIn."""
        original_desc = project.get('description', '')
        
        if not original_desc:
            # Generate description from project data
            project_name = project['name'].replace('-', ' ').replace('_', ' ').title()
            project_type = project.get('project_type', 'application')
            
            type_descriptions = {
                'web-app': f"A comprehensive web application that demonstrates modern full-stack development practices",
                'mobile-app': f"A cross-platform mobile application built with focus on user experience and performance",
                'api': f"A robust API service designed for scalability and reliability",
                'library': f"An open-source library that provides reusable components for developers",
                'cli-tool': f"A command-line tool that streamlines developer workflows and productivity",
                'other': f"A software solution addressing specific technical challenges"
            }
            
            base_desc = type_descriptions.get(project_type, type_descriptions['other'])
            return f"{project_name}: {base_desc}."
        
        # Enhance existing description
        enhanced = original_desc
        
        # Add impact metrics if available
        stars = project.get('stars', 0)
        forks = project.get('forks', 0)
        
        impact_additions = []
        if stars > 50:
            impact_additions.append(f"Recognized by the community with {stars} GitHub stars")
        if forks > 20:
            impact_additions.append(f"adopted and extended by {forks} developers")
        
        if impact_additions:
            enhanced += f" {'. '.join(impact_additions)}."
        
        return enhanced
    
    def _generate_project_achievements(self, project: Dict[str, Any]) -> List[str]:
        """Generate project achievements for LinkedIn."""
        achievements = []
        
        stars = project.get('stars', 0)
        forks = project.get('forks', 0)
        
        if stars > 100:
            achievements.append(f"Achieved {stars} GitHub stars, indicating high community value")
        elif stars > 20:
            achievements.append(f"Earned {stars} GitHub stars from the developer community")
        
        if forks > 50:
            achievements.append(f"Forked {forks} times, demonstrating practical utility and adoption")
        elif forks > 10:
            achievements.append(f"Successfully adopted by {forks} other developers")
        
        if project.get('has_readme'):
            achievements.append("Maintained comprehensive documentation and user guides")
        
        # Add technical achievements based on project type
        project_type = project.get('project_type', '')
        if project_type == 'web-app':
            achievements.append("Implemented responsive design and modern web standards")
        elif project_type == 'mobile-app':
            achievements.append("Delivered cross-platform compatibility and optimized performance")
        elif project_type == 'api':
            achievements.append("Designed scalable architecture with comprehensive API documentation")
        
        return achievements
    
    def _extract_year_from_date(self, date_str: str) -> str:
        """Extract year from ISO date string."""
        try:
            if date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y')
        except:
            pass
        return datetime.now().strftime('%Y')
    
    def _generate_top_skills(self, profile: GitHubProfile) -> List[str]:
        """Generate top skills for LinkedIn profile."""
        skills = []
        
        # Programming languages (top performers)
        top_languages = [lang for lang, pct in profile.languages_percentage.items() if pct > 5][:8]
        skills.extend(top_languages)
        
        # Core development skills
        core_skills = []
        if profile.has_web_projects:
            core_skills.extend(['Web Development', 'Frontend Development', 'Backend Development'])
        if profile.has_mobile_projects:
            core_skills.extend(['Mobile Application Development', 'iOS Development', 'Android Development'])
        if profile.has_apis:
            core_skills.extend(['API Development', 'RESTful Services', 'Microservices'])
        if profile.has_libraries:
            core_skills.extend(['Software Architecture', 'Library Development'])
        if profile.has_cli_tools:
            core_skills.extend(['Developer Tools', 'Command Line Interface'])
        
        # Development practices
        if profile.repositories_with_tests > 0:
            core_skills.append('Test-Driven Development')
        if profile.repositories_with_ci > 0:
            core_skills.extend(['Continuous Integration', 'DevOps'])
        if profile.repositories_with_docker > 0:
            core_skills.append('Docker')
        
        skills.extend(core_skills[:10])
        
        # Soft skills based on profile analysis
        soft_skills = []
        if profile.collaboration_score > 60:
            soft_skills.extend(['Team Collaboration', 'Code Review', 'Technical Leadership'])
        if profile.innovation_score > 60:
            soft_skills.extend(['Problem Solving', 'Innovation', 'Technical Strategy'])
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.7:
            soft_skills.extend(['Technical Writing', 'Documentation'])
        
        skills.extend(soft_skills[:8])
        
        # Industry-specific skills
        if self.config.target_industry:
            industry_skills = self.industry_keywords.get(self.config.target_industry.lower(), [])
            skills.extend(industry_skills[:5])
        
        # Role-specific skills
        if self.config.target_role:
            role_skills = self.role_keywords.get(self.config.target_role.lower(), [])
            skills.extend(role_skills[:5])
        
        # Remove duplicates and return top skills
        unique_skills = list(dict.fromkeys(skills))  # Preserve order while removing duplicates
        return unique_skills[:50]  # LinkedIn allows up to 50 skills
    
    def _generate_skill_categories(self, profile: GitHubProfile) -> Dict[str, List[str]]:
        """Generate categorized skills."""
        categories = {}
        
        # Programming Languages
        languages = [lang for lang, pct in profile.languages_percentage.items() if pct > 2]
        if languages:
            categories['Programming Languages'] = languages[:12]
        
        # Frameworks & Technologies
        frameworks = []
        if 'JavaScript' in profile.languages_used or 'TypeScript' in profile.languages_used:
            frameworks.extend(['React', 'Node.js', 'Express.js'])
        if 'Python' in profile.languages_used:
            frameworks.extend(['Django', 'Flask', 'FastAPI'])
        if 'Java' in profile.languages_used:
            frameworks.extend(['Spring Boot', 'Spring Framework'])
        
        if frameworks:
            categories['Frameworks & Technologies'] = frameworks[:10]
        
        # Development Tools
        tools = ['Git', 'GitHub']
        if profile.repositories_with_ci > 0:
            tools.extend(['CI/CD', 'GitHub Actions'])
        if profile.repositories_with_docker > 0:
            tools.append('Docker')
        
        categories['Development Tools'] = tools[:10]
        
        # Specializations
        specializations = []
        if profile.has_web_projects:
            specializations.append('Web Development')
        if profile.has_mobile_projects:
            specializations.append('Mobile Development')
        if profile.has_apis:
            specializations.append('API Development')
        if profile.has_libraries:
            specializations.append('Library Development')
        
        if specializations:
            categories['Specializations'] = specializations
        
        return categories
    
    def _generate_post_ideas(self, profile: GitHubProfile) -> List[str]:
        """Generate LinkedIn post ideas based on profile."""
        ideas = []
        
        # Technical insights posts
        for lang in profile.primary_languages[:3]:
            ideas.append(f"Share insights about {lang} best practices and lessons learned from your projects")
            ideas.append(f"Write about a challenging {lang} problem you solved and your approach")
        
        # Project showcase posts
        for project in profile.featured_projects[:3]:
            ideas.append(f"Create a case study post about {project['name']} - the problem, solution, and results")
            ideas.append(f"Share the technical architecture and decision-making process behind {project['name']}")
        
        # Industry and trend posts
        if profile.has_web_projects:
            ideas.append("Share thoughts on the latest web development trends and how they impact your work")
        if profile.has_mobile_projects:
            ideas.append("Discuss mobile development best practices and user experience insights")
        if profile.has_apis:
            ideas.append("Write about API design principles and common pitfalls to avoid")
        
        # Community and learning posts
        if profile.total_stars_received > 50:
            ideas.append("Reflect on what you've learned from building popular open-source projects")
        if profile.collaboration_score > 60:
            ideas.append("Share tips for effective collaboration in distributed development teams")
        
        # Career and growth posts
        ideas.append(f"Write about your journey as a {profile.developer_type.lower()} and key milestones")
        ideas.append("Share resources and learning paths for developers wanting to improve their skills")
        
        # Problem-solving posts
        ideas.append("Document a technical debugging session and the systematic approach you used")
        ideas.append("Share automation tools or scripts that have improved your development workflow")
        
        return ideas[:15]
    
    def _generate_article_topics(self, profile: GitHubProfile) -> List[str]:
        """Generate LinkedIn article topics."""
        topics = []
        
        # Technical deep-dives
        for lang in profile.primary_languages[:2]:
            topics.append(f"Advanced {lang} Patterns: Lessons from Building {profile.original_repositories} Projects")
            topics.append(f"The Evolution of {lang}: How It's Shaped My Development Journey")
        
        # Architecture and design
        if profile.has_web_projects:
            topics.append("Building Scalable Web Applications: Architecture Decisions That Matter")
        if profile.has_mobile_projects:
            topics.append("Mobile-First Development: Creating Apps That Users Love")
        if profile.has_apis:
            topics.append("API Design Philosophy: Creating Interfaces That Stand the Test of Time")
        
        # Open source and community
        if profile.total_stars_received > 100:
            topics.append(f"From Zero to {profile.total_stars_received} GitHub Stars: Building Software That Resonates")
        if profile.original_repositories > 20:
            topics.append("The Art of Open Source: What I've Learned from Publishing 20+ Projects")
        
        # Industry insights
        if self.config.target_industry:
            industry = self.config.target_industry
            topics.append(f"Technology Trends Shaping the {industry} Industry in 2024")
            topics.append(f"Building Software for {industry}: Challenges and Opportunities")
        
        # Career and learning
        topics.append(f"The {profile.developer_type} Mindset: How to Think Like a Solution Architect")
        topics.append("Continuous Learning in Tech: Staying Current in a Fast-Changing Field")
        
        # Process and methodology
        if profile.collaboration_score > 60:
            topics.append("Code Review Culture: Building Better Software Through Collaboration")
        if profile.repositories_with_readme / max(profile.total_repositories, 1) > 0.7:
            topics.append("Documentation as Code: Making Your Projects Accessible and Maintainable")
        
        return topics[:12]
    
    def _generate_connection_targets(self, profile: GitHubProfile) -> List[str]:
        """Generate connection targeting suggestions."""
        targets = []
        
        # Role-based connections
        if self.config.target_role:
            role = self.config.target_role.lower()
            targets.append(f"Senior {role}s and tech leads in similar roles")
            targets.append(f"Hiring managers looking for {role} talent")
        
        # Industry connections
        if self.config.target_industry:
            industry = self.config.target_industry
            targets.append(f"Technology leaders in the {industry} industry")
            targets.append(f"Product managers and CTOs in {industry} companies")
        
        # Technology-based connections
        for lang in profile.primary_languages[:2]:
            targets.append(f"{lang} developers and community leaders")
        
        # Company-based connections
        if self.config.company_preferences:
            for company in self.config.company_preferences[:3]:
                targets.append(f"Engineers and technical leaders at {company}")
        
        # Geographic connections
        if profile.location or self.config.location_preferences:
            locations = [profile.location] + self.config.location_preferences
            for location in locations[:2]:
                if location:
                    targets.append(f"Tech professionals in {location}")
        
        # Community connections
        if profile.total_stars_received > 50:
            targets.append("Open source maintainers and contributors")
        if profile.has_libraries:
            targets.append("Developer tool creators and library maintainers")
        
        # Event and community connections
        targets.append("Tech conference speakers and organizers")
        targets.append("Startup founders and early-stage company builders")
        
        return targets[:10]
    
    def _generate_industry_keywords(self, profile: GitHubProfile) -> List[str]:
        """Generate industry keywords for optimization."""
        keywords = []
        
        # Core technology keywords
        keywords.extend(profile.primary_languages[:5])
        
        # Role-based keywords
        if self.config.target_role:
            role_kw = self.role_keywords.get(self.config.target_role.lower(), [])
            keywords.extend(role_kw[:8])
        
        # Industry keywords
        if self.config.target_industry:
            industry_kw = self.industry_keywords.get(self.config.target_industry.lower(), [])
            keywords.extend(industry_kw[:8])
        
        # Development methodology keywords
        methodologies = []
        if profile.repositories_with_tests > 0:
            methodologies.extend(['test-driven development', 'unit testing', 'quality assurance'])
        if profile.repositories_with_ci > 0:
            methodologies.extend(['continuous integration', 'continuous deployment', 'DevOps'])
        if profile.collaboration_score > 60:
            methodologies.extend(['agile development', 'collaborative programming', 'code review'])
        
        keywords.extend(methodologies[:6])
        
        # Project type keywords
        if profile.has_web_projects:
            keywords.extend(['web applications', 'full-stack development', 'responsive design'])
        if profile.has_mobile_projects:
            keywords.extend(['mobile applications', 'app development', 'user experience'])
        if profile.has_apis:
            keywords.extend(['REST APIs', 'microservices', 'API design'])
        
        # Personal brand keywords
        keywords.extend(self.config.personal_brand_keywords)
        
        # Remove duplicates and return
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:30]
    
    def _generate_improvement_tips(self, profile: GitHubProfile) -> List[str]:
        """Generate profile improvement tips."""
        tips = []
        
        # Content completeness tips
        if not profile.bio:
            tips.append("Add a compelling bio/summary that tells your professional story")
        
        if not profile.location:
            tips.append("Include your location to improve local networking opportunities")
        
        if not profile.website:
            tips.append("Add a personal website or portfolio link to showcase your work")
        
        # Content optimization tips
        tips.append("Use industry-specific keywords in your headline and summary")
        tips.append("Include quantifiable achievements (GitHub stars, project impacts)")
        tips.append("Add skill endorsements by connecting with colleagues and peers")
        
        # Activity tips
        tips.append("Post regularly about your technical work and industry insights")
        tips.append("Share updates about your projects and development milestones")
        tips.append("Engage with other developers' content through thoughtful comments")
        
        # Network building tips
        tips.append("Connect with developers working in similar technologies")
        tips.append("Join LinkedIn groups related to your programming languages and industry")
        tips.append("Follow and engage with thought leaders in your field")
        
        # Professional development tips
        if profile.experience_level.lower() in ['entry', 'junior']:
            tips.append("Highlight your learning journey and growth trajectory")
            tips.append("Showcase personal projects that demonstrate your skills")
        elif profile.experience_level.lower() in ['senior', 'lead']:
            tips.append("Emphasize leadership experience and mentoring activities")
            tips.append("Share insights about technical decision-making and architecture")
        
        # Content strategy tips
        tips.append("Create case studies of your most successful projects")
        tips.append("Write about technical challenges you've solved")
        tips.append("Share resources and tools that have helped your development")
        
        return tips[:15]
    
    def _generate_keyword_optimization(self, profile: GitHubProfile) -> List[str]:
        """Generate keyword optimization suggestions."""
        optimizations = []
        
        # Headline optimization
        optimizations.append("Include your target role and top 2-3 technologies in your headline")
        optimizations.append("Add industry-specific terms that recruiters search for")
        
        # Summary optimization
        optimizations.append("Use your top programming languages naturally throughout your summary")
        optimizations.append("Include methodology keywords like 'agile', 'scrum', or 'DevOps' if applicable")
        optimizations.append("Mention specific frameworks and tools you're proficient in")
        
        # Experience optimization
        optimizations.append("Use action verbs and quantify achievements in experience descriptions")
        optimizations.append("Include relevant technologies in each experience entry")
        
        # Skills optimization
        optimizations.append("List both technical skills and soft skills relevant to your target role")
        optimizations.append("Include variations of skill names (e.g., 'JavaScript', 'JS', 'Node.js')")
        
        # Content optimization
        optimizations.append("Write posts and articles using keywords from your target job descriptions")
        optimizations.append("Use hashtags strategically in your posts to increase visibility")
        
        # Profile completeness
        optimizations.append("Ensure all sections are completed to improve LinkedIn search ranking")
        optimizations.append("Add media samples (code repositories, project screenshots) to showcase work")
        
        return optimizations[:12]


class LinkedInExporter:
    """Exports LinkedIn profile data to various formats."""
    
    def __init__(self, linkedin_profile: LinkedInProfile):
        self.linkedin_profile = linkedin_profile
        self.logger = get_logger()
    
    def export_to_json(self, file_path: str):
        """Export LinkedIn profile to JSON format."""
        try:
            profile_dict = asdict(self.linkedin_profile)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"LinkedIn profile exported to JSON: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export LinkedIn profile to JSON: {e}")
            raise
    
    def export_to_text(self, file_path: str):
        """Export LinkedIn profile to readable text format."""
        try:
            content = self._generate_text_export()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"LinkedIn profile exported to text: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export LinkedIn profile to text: {e}")
            raise
    
    def _generate_text_export(self) -> str:
        """Generate human-readable text export."""
        sections = []
        
        # Header
        sections.append("LINKEDIN PROFILE OPTIMIZATION GUIDE")
        sections.append("=" * 50)
        sections.append(f"Generated: {self.linkedin_profile.generated_date}")
        sections.append("")
        
        # Headline
        if self.linkedin_profile.headline:
            sections.append("HEADLINE:")
            sections.append(self.linkedin_profile.headline)
            sections.append("")
        
        # Summary
        if self.linkedin_profile.summary:
            sections.append("SUMMARY:")
            sections.append(self.linkedin_profile.summary)
            sections.append("")
        
        # Alternative summaries
        if self.linkedin_profile.summary_short:
            sections.append("SHORT SUMMARY (2 sentences):")
            sections.append(self.linkedin_profile.summary_short)
            sections.append("")
        
        # Top Skills
        if self.linkedin_profile.top_skills:
            sections.append("TOP SKILLS TO ADD:")
            for i, skill in enumerate(self.linkedin_profile.top_skills[:15], 1):
                sections.append(f"{i:2d}. {skill}")
            sections.append("")
        
        # Experience Descriptions
        if self.linkedin_profile.experience_descriptions:
            sections.append("EXPERIENCE DESCRIPTIONS:")
            for i, exp in enumerate(self.linkedin_profile.experience_descriptions, 1):
                sections.append(f"\n{i}. {exp.get('title', 'Position')} at {exp.get('company', 'Company')}")
                if exp.get('linkedin_description'):
                    sections.append(exp['linkedin_description'])
                if exp.get('accomplishments'):
                    sections.append("Key Accomplishments:")
                    for acc in exp['accomplishments']:
                        sections.append(f"  • {acc}")
            sections.append("")
        
        # Project Descriptions
        if self.linkedin_profile.project_descriptions:
            sections.append("PROJECT DESCRIPTIONS:")
            for i, project in enumerate(self.linkedin_profile.project_descriptions[:5], 1):
                sections.append(f"\n{i}. {project['name']}")
                sections.append(project['description'])
                if project.get('achievements'):
                    for achievement in project['achievements']:
                        sections.append(f"  • {achievement}")
            sections.append("")
        
        # Content Ideas
        if self.linkedin_profile.post_ideas:
            sections.append("LINKEDIN POST IDEAS:")
            for i, idea in enumerate(self.linkedin_profile.post_ideas[:10], 1):
                sections.append(f"{i:2d}. {idea}")
            sections.append("")
        
        # Article Topics
        if self.linkedin_profile.article_topics:
            sections.append("LINKEDIN ARTICLE TOPICS:")
            for i, topic in enumerate(self.linkedin_profile.article_topics[:8], 1):
                sections.append(f"{i:2d}. {topic}")
            sections.append("")
        
        # Optimization Tips
        if self.linkedin_profile.profile_improvement_tips:
            sections.append("PROFILE IMPROVEMENT TIPS:")
            for i, tip in enumerate(self.linkedin_profile.profile_improvement_tips, 1):
                sections.append(f"{i:2d}. {tip}")
            sections.append("")
        
        # Keyword Optimization
        if self.linkedin_profile.keyword_optimization:
            sections.append("KEYWORD OPTIMIZATION:")
            for i, opt in enumerate(self.linkedin_profile.keyword_optimization, 1):
                sections.append(f"{i:2d}. {opt}")
            sections.append("")
        
        # Connection Targets
        if self.linkedin_profile.connection_targets:
            sections.append("CONNECTION TARGETS:")
            for i, target in enumerate(self.linkedin_profile.connection_targets, 1):
                sections.append(f"{i:2d}. {target}")
            sections.append("")
        
        return "\n".join(sections)