#!/usr/bin/env python3
"""
GitHub Profile Builder

Builds comprehensive GitHub profiles by analyzing all user repositories,
extracting insights, and generating portfolio-ready data.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import defaultdict, Counter
import statistics

try:
    from .repository_discovery import RepositoryInfo, RepositoryDiscovery, DiscoveryConfig
    from .analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata
    from .utils.logger import get_logger
except ImportError:
    from repository_discovery import RepositoryInfo, RepositoryDiscovery, DiscoveryConfig
    from analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata
    from utils.logger import get_logger


@dataclass
class GitHubProfile:
    """Comprehensive GitHub profile data structure."""
    
    # Basic Profile Info
    username: str = ""
    name: str = ""
    bio: str = ""
    location: str = ""
    company: str = ""
    website: str = ""
    email: str = ""
    avatar_url: str = ""
    profile_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    # Repository Statistics
    total_repositories: int = 0
    public_repositories: int = 0
    private_repositories: int = 0
    forked_repositories: int = 0
    original_repositories: int = 0
    
    # Code Statistics
    total_stars_received: int = 0
    total_forks_received: int = 0
    total_commits: int = 0
    total_lines_of_code: int = 0
    total_files: int = 0
    
    # Language Analysis
    languages_used: Dict[str, int] = field(default_factory=dict)  # language -> line count
    languages_percentage: Dict[str, float] = field(default_factory=dict)
    primary_languages: List[str] = field(default_factory=list)  # Top 5 languages
    
    # Technology Stack
    frameworks_used: Counter = field(default_factory=Counter)
    databases_used: Counter = field(default_factory=Counter)
    tools_used: Counter = field(default_factory=Counter)
    
    # Project Types
    project_types: Counter = field(default_factory=Counter)
    has_web_projects: bool = False
    has_mobile_projects: bool = False
    has_cli_tools: bool = False
    has_libraries: bool = False
    has_apis: bool = False
    
    # Development Practices
    repositories_with_tests: int = 0
    repositories_with_docs: int = 0
    repositories_with_ci: int = 0
    repositories_with_docker: int = 0
    repositories_with_readme: int = 0
    test_coverage_percentage: float = 0.0
    
    # Activity Patterns
    most_active_months: List[str] = field(default_factory=list)
    commit_frequency: Dict[str, int] = field(default_factory=dict)  # day/month -> commit count
    average_commits_per_repo: float = 0.0
    
    # Notable Repositories
    most_starred_repos: List[Dict] = field(default_factory=list)
    most_forked_repos: List[Dict] = field(default_factory=list)
    largest_repos: List[Dict] = field(default_factory=list)
    recent_active_repos: List[Dict] = field(default_factory=list)
    
    # Skills and Expertise
    skill_levels: Dict[str, str] = field(default_factory=dict)  # language -> level (Beginner/Intermediate/Advanced/Expert)
    expertise_areas: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    
    # Profile Insights
    developer_type: str = ""  # Full-stack, Frontend, Backend, Mobile, DevOps, etc.
    experience_level: str = ""  # Junior, Mid, Senior, Lead
    collaboration_score: float = 0.0  # Based on forks, contributions, etc.
    innovation_score: float = 0.0  # Based on original projects, stars received
    consistency_score: float = 0.0  # Based on commit frequency
    
    # Portfolio Data
    featured_projects: List[Dict] = field(default_factory=list)
    project_categories: Dict[str, List[Dict]] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    
    # Metadata
    analysis_date: str = ""
    total_analyzed_repos: int = 0
    analysis_duration: float = 0.0


@dataclass
class ProfileBuilderConfig:
    """Configuration for profile building."""
    
    # Analysis settings
    include_forks: bool = False
    include_archived: bool = False
    min_repo_size_kb: int = 1  # Ignore tiny repos
    max_repos_to_analyze: Optional[int] = None
    
    # Portfolio settings  
    max_featured_projects: int = 6
    min_stars_for_featured: int = 1
    prioritize_recent_activity: bool = True
    
    # Skills assessment
    min_commits_for_skill: int = 10
    min_lines_for_expertise: int = 1000
    
    # Export settings
    generate_portfolio_html: bool = True
    generate_resume_data: bool = True
    export_raw_data: bool = True


class GitHubProfileBuilder:
    """Main class for building comprehensive GitHub profiles."""
    
    def __init__(self, config: ProfileBuilderConfig = None):
        """Initialize the profile builder."""
        self.config = config or ProfileBuilderConfig()
        self.logger = get_logger()
        self.analyzer = RepositoryAnalyzer()
        self.profile = GitHubProfile()
        
    async def build_profile(self, username: str, github_token: Optional[str] = None,
                          progress_callback: Optional[callable] = None) -> GitHubProfile:
        """Build a comprehensive GitHub profile."""
        start_time = datetime.now()
        self.profile.username = username
        self.profile.analysis_date = start_time.isoformat()
        
        try:
            # Step 1: Discover all repositories
            if progress_callback:
                progress_callback("Discovering repositories...", 0)
            
            repos = await self._discover_repositories(username, github_token)
            if not repos:
                raise ValueError(f"No repositories found for user: {username}")
            
            # Step 2: Get user profile information
            if progress_callback:
                progress_callback("Fetching profile information...", 10)
            
            await self._fetch_user_profile(username, github_token)
            
            # Step 3: Analyze repositories
            if progress_callback:
                progress_callback("Analyzing repositories...", 20)
            
            analyzed_repos = await self._analyze_repositories(repos, progress_callback)
            
            # Step 4: Generate profile insights
            if progress_callback:
                progress_callback("Generating insights...", 80)
            
            self._generate_profile_insights(analyzed_repos)
            
            # Step 5: Build portfolio data
            if progress_callback:
                progress_callback("Building portfolio data...", 90)
            
            self._build_portfolio_data(analyzed_repos)
            
            # Step 6: Calculate scores and classifications
            self._calculate_developer_scores()
            self._classify_developer_type()
            
            # Finalize
            end_time = datetime.now()
            self.profile.analysis_duration = (end_time - start_time).total_seconds()
            
            if progress_callback:
                progress_callback("Profile building completed!", 100)
                
            self.logger.info(f"Profile built for {username}: {len(analyzed_repos)} repos analyzed")
            return self.profile
            
        except Exception as e:
            self.logger.error(f"Failed to build profile for {username}: {e}")
            raise
    
    async def _discover_repositories(self, username: str, github_token: Optional[str]) -> List[RepositoryInfo]:
        """Discover all repositories for the user."""
        config = DiscoveryConfig(
            include_github=True,
            include_gitlab=False,
            github_token=github_token,
            include_private=True,
            include_forks=self.config.include_forks,
            include_archived=self.config.include_archived,
            max_repos_per_provider=self.config.max_repos_to_analyze or 1000
        )
        
        discovery = RepositoryDiscovery(config)
        repos = await discovery.discover_all_repositories()
        
        # Filter by size if specified
        if self.config.min_repo_size_kb > 0:
            repos = [r for r in repos if r.size_kb >= self.config.min_repo_size_kb]
        
        self.profile.total_repositories = len(repos)
        self.profile.public_repositories = sum(1 for r in repos if not r.is_private)
        self.profile.private_repositories = sum(1 for r in repos if r.is_private)
        self.profile.forked_repositories = sum(1 for r in repos if r.is_fork)
        self.profile.original_repositories = sum(1 for r in repos if not r.is_fork)
        
        return repos
    
    async def _fetch_user_profile(self, username: str, github_token: Optional[str]):
        """Fetch user profile information from GitHub."""
        try:
            from github import Github
            
            if github_token:
                github = Github(github_token)
            else:
                github = Github()
            
            user = github.get_user(username)
            
            self.profile.name = user.name or ""
            self.profile.bio = user.bio or ""
            self.profile.location = user.location or ""
            self.profile.company = user.company or ""
            self.profile.website = user.blog or ""
            self.profile.email = user.email or ""
            self.profile.avatar_url = user.avatar_url or ""
            self.profile.profile_url = user.html_url or ""
            self.profile.created_at = user.created_at.isoformat() if user.created_at else ""
            self.profile.updated_at = user.updated_at.isoformat() if user.updated_at else ""
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch user profile: {e}")
    
    async def _analyze_repositories(self, repos: List[RepositoryInfo], 
                                  progress_callback: Optional[callable] = None) -> List[Tuple[RepositoryInfo, ProjectMetadata]]:
        """Analyze all repositories and extract metadata."""
        analyzed_repos = []
        
        for i, repo in enumerate(repos):
            try:
                if progress_callback:
                    progress = 20 + int((i / len(repos)) * 60)  # 20% to 80%
                    progress_callback(f"Analyzing {repo.name}...", progress)
                
                # For now, create metadata from repository info
                # In a full implementation, you'd clone and analyze each repo
                metadata = self._create_metadata_from_repo_info(repo)
                analyzed_repos.append((repo, metadata))
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze repository {repo.name}: {e}")
                continue
        
        self.profile.total_analyzed_repos = len(analyzed_repos)
        return analyzed_repos
    
    def _create_metadata_from_repo_info(self, repo: RepositoryInfo) -> ProjectMetadata:
        """Create project metadata from repository information."""
        metadata = ProjectMetadata()
        metadata.name = repo.name
        metadata.description = repo.description
        metadata.repository_url = repo.url
        metadata.primary_language = repo.language
        metadata.languages = {repo.language: 100.0} if repo.language != "Unknown" else {}
        metadata.stars_count = repo.stars
        metadata.forks_count = repo.forks
        metadata.has_readme = repo.has_readme
        metadata.created_date = repo.created_at
        metadata.last_updated = repo.updated_at
        metadata.license = repo.license or ""
        metadata.topics = repo.topics
        
        # Infer project type from repo name, language, and topics
        metadata.project_type = self._infer_project_type(repo)
        
        return metadata
    
    def _infer_project_type(self, repo: RepositoryInfo) -> str:
        """Infer project type from repository information."""
        name_lower = repo.name.lower()
        desc_lower = repo.description.lower() if repo.description else ""
        topics_lower = [t.lower() for t in repo.topics]
        
        # Web applications
        web_indicators = ['website', 'web', 'app', 'frontend', 'backend', 'fullstack', 'react', 'vue', 'angular']
        if any(indicator in name_lower or indicator in desc_lower for indicator in web_indicators):
            return "web-app"
        
        # Mobile applications
        mobile_indicators = ['mobile', 'android', 'ios', 'flutter', 'react-native', 'swift', 'kotlin']
        if any(indicator in name_lower or indicator in desc_lower or indicator in topics_lower for indicator in mobile_indicators):
            return "mobile-app"
        
        # CLI tools
        cli_indicators = ['cli', 'command', 'tool', 'utility', 'script']
        if any(indicator in name_lower or indicator in desc_lower for indicator in cli_indicators):
            return "cli-tool"
        
        # Libraries
        lib_indicators = ['library', 'lib', 'package', 'sdk', 'framework']
        if any(indicator in name_lower or indicator in desc_lower or indicator in topics_lower for indicator in lib_indicators):
            return "library"
        
        # APIs
        api_indicators = ['api', 'server', 'backend', 'microservice', 'service']
        if any(indicator in name_lower or indicator in desc_lower for indicator in api_indicators):
            return "api"
        
        return "other"
    
    def _generate_profile_insights(self, analyzed_repos: List[Tuple[RepositoryInfo, ProjectMetadata]]):
        """Generate insights from analyzed repositories."""
        
        # Calculate totals
        for repo_info, metadata in analyzed_repos:
            self.profile.total_stars_received += repo_info.stars
            self.profile.total_forks_received += repo_info.forks
            
            # Language statistics
            if metadata.primary_language and metadata.primary_language != "Unknown":
                self.profile.languages_used[metadata.primary_language] = \
                    self.profile.languages_used.get(metadata.primary_language, 0) + repo_info.size_kb
            
            # Project types
            if metadata.project_type:
                self.profile.project_types[metadata.project_type] += 1
            
            # Development practices
            if metadata.has_readme:
                self.profile.repositories_with_readme += 1
        
        # Calculate language percentages
        total_size = sum(self.profile.languages_used.values()) or 1
        self.profile.languages_percentage = {
            lang: (size / total_size) * 100 
            for lang, size in self.profile.languages_used.items()
        }
        
        # Primary languages (top 5)
        sorted_languages = sorted(
            self.profile.languages_percentage.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        self.profile.primary_languages = [lang for lang, _ in sorted_languages[:5]]
        
        # Set project type flags
        self.profile.has_web_projects = self.profile.project_types.get('web-app', 0) > 0
        self.profile.has_mobile_projects = self.profile.project_types.get('mobile-app', 0) > 0
        self.profile.has_cli_tools = self.profile.project_types.get('cli-tool', 0) > 0
        self.profile.has_libraries = self.profile.project_types.get('library', 0) > 0
        self.profile.has_apis = self.profile.project_types.get('api', 0) > 0
    
    def _build_portfolio_data(self, analyzed_repos: List[Tuple[RepositoryInfo, ProjectMetadata]]):
        """Build portfolio-ready data."""
        
        # Sort repos by different criteria
        repos_by_stars = sorted(analyzed_repos, key=lambda x: x[0].stars, reverse=True)
        repos_by_forks = sorted(analyzed_repos, key=lambda x: x[0].forks, reverse=True)
        repos_by_size = sorted(analyzed_repos, key=lambda x: x[0].size_kb, reverse=True)
        repos_by_update = sorted(analyzed_repos, key=lambda x: x[0].updated_at, reverse=True)
        
        # Most starred repositories
        self.profile.most_starred_repos = [
            {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stars,
                "forks": repo.forks,
                "language": repo.language,
                "url": repo.url,
                "topics": repo.topics
            }
            for repo, _ in repos_by_stars[:10]
        ]
        
        # Most forked repositories
        self.profile.most_forked_repos = [
            {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stars,
                "forks": repo.forks,
                "language": repo.language,
                "url": repo.url
            }
            for repo, _ in repos_by_forks[:10]
        ]
        
        # Largest repositories
        self.profile.largest_repos = [
            {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "size_kb": repo.size_kb,
                "language": repo.language,
                "url": repo.url
            }
            for repo, _ in repos_by_size[:10]
        ]
        
        # Recent active repositories
        self.profile.recent_active_repos = [
            {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "updated_at": repo.updated_at,
                "language": repo.language,
                "url": repo.url
            }
            for repo, _ in repos_by_update[:10]
        ]
        
        # Featured projects (for portfolio)
        featured_candidates = [
            (repo, metadata) for repo, metadata in analyzed_repos 
            if repo.stars >= self.config.min_stars_for_featured and not repo.is_fork
        ]
        
        # Sort by stars and recency for featured projects
        featured_candidates.sort(
            key=lambda x: (x[0].stars, x[0].updated_at), 
            reverse=True
        )
        
        self.profile.featured_projects = [
            {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or metadata.description,
                "stars": repo.stars,
                "forks": repo.forks,
                "language": repo.language,
                "url": repo.url,
                "topics": repo.topics,
                "project_type": metadata.project_type,
                "has_readme": repo.has_readme,
                "updated_at": repo.updated_at
            }
            for repo, metadata in featured_candidates[:self.config.max_featured_projects]
        ]
        
        # Categorize projects
        categories = defaultdict(list)
        for repo, metadata in analyzed_repos:
            if not repo.is_fork:  # Only original projects
                category = metadata.project_type or "other"
                categories[category].append({
                    "name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stars,
                    "url": repo.url,
                    "topics": repo.topics
                })
        
        self.profile.project_categories = dict(categories)
    
    def _calculate_developer_scores(self):
        """Calculate various developer scores."""
        
        # Collaboration Score (0-100)
        # Based on forks received, non-fork repos, and public repos
        collaboration_factors = []
        if self.profile.total_repositories > 0:
            fork_ratio = self.profile.total_forks_received / max(self.profile.original_repositories, 1)
            collaboration_factors.append(min(fork_ratio * 10, 50))  # Max 50 points
            
            public_ratio = self.profile.public_repositories / self.profile.total_repositories
            collaboration_factors.append(public_ratio * 30)  # Max 30 points
            
            readme_ratio = self.profile.repositories_with_readme / self.profile.total_repositories
            collaboration_factors.append(readme_ratio * 20)  # Max 20 points
        
        self.profile.collaboration_score = sum(collaboration_factors) if collaboration_factors else 0
        
        # Innovation Score (0-100)
        # Based on stars received, original projects, and technology diversity
        innovation_factors = []
        if self.profile.total_repositories > 0:
            # Stars per original repo
            stars_per_repo = self.profile.total_stars_received / max(self.profile.original_repositories, 1)
            innovation_factors.append(min(stars_per_repo * 5, 40))  # Max 40 points
            
            # Language diversity
            num_languages = len(self.profile.languages_used)
            innovation_factors.append(min(num_languages * 5, 30))  # Max 30 points
            
            # Original project ratio
            original_ratio = self.profile.original_repositories / self.profile.total_repositories
            innovation_factors.append(original_ratio * 30)  # Max 30 points
        
        self.profile.innovation_score = sum(innovation_factors) if innovation_factors else 0
        
        # Consistency Score (placeholder - would need commit history)
        self.profile.consistency_score = 50.0  # Default middle score
    
    def _classify_developer_type(self):
        """Classify the developer type based on technologies and project types."""
        
        # Analyze languages and project types
        web_languages = {'JavaScript', 'TypeScript', 'HTML', 'CSS', 'PHP', 'Ruby', 'Python'}
        mobile_languages = {'Swift', 'Kotlin', 'Dart', 'Objective-C', 'Java'}
        backend_languages = {'Python', 'Java', 'Go', 'Rust', 'C++', 'C#', 'Ruby', 'PHP', 'Scala'}
        frontend_languages = {'JavaScript', 'TypeScript', 'HTML', 'CSS'}
        
        user_languages = set(self.profile.languages_used.keys())
        
        # Score different developer types
        scores = {
            'Full-stack': len(user_languages & web_languages) + (2 if self.profile.has_web_projects else 0),
            'Frontend': len(user_languages & frontend_languages) + (2 if self.profile.has_web_projects else 0),
            'Backend': len(user_languages & backend_languages) + (2 if self.profile.has_apis else 0),
            'Mobile': len(user_languages & mobile_languages) + (3 if self.profile.has_mobile_projects else 0),
            'DevOps': 1 if 'Shell' in user_languages or 'Dockerfile' in user_languages else 0,
            'Data Science': 2 if 'Python' in user_languages or 'R' in user_languages else 0,
            'Systems': len(user_languages & {'C', 'C++', 'Rust', 'Go', 'Assembly'})
        }
        
        # Add project type bonuses
        if self.profile.has_libraries:
            scores['Library Developer'] = 2
        if self.profile.has_cli_tools:
            scores['Tool Developer'] = 2
        
        # Determine primary type
        if scores:
            primary_type = max(scores, key=scores.get)
            self.profile.developer_type = primary_type if scores[primary_type] > 0 else "Generalist"
        else:
            self.profile.developer_type = "Generalist"
        
        # Determine experience level based on various factors
        experience_indicators = []
        if self.profile.total_repositories >= 50:
            experience_indicators.append(3)
        elif self.profile.total_repositories >= 20:
            experience_indicators.append(2)
        elif self.profile.total_repositories >= 10:
            experience_indicators.append(1)
        
        if self.profile.total_stars_received >= 100:
            experience_indicators.append(2)
        elif self.profile.total_stars_received >= 20:
            experience_indicators.append(1)
        
        if len(self.profile.languages_used) >= 5:
            experience_indicators.append(2)
        elif len(self.profile.languages_used) >= 3:
            experience_indicators.append(1)
        
        avg_experience = sum(experience_indicators) / len(experience_indicators) if experience_indicators else 0
        
        if avg_experience >= 2.5:
            self.profile.experience_level = "Senior"
        elif avg_experience >= 1.5:
            self.profile.experience_level = "Mid-level"  
        elif avg_experience >= 0.5:
            self.profile.experience_level = "Junior"
        else:
            self.profile.experience_level = "Entry-level"


class ProfileExporter:
    """Exports GitHub profiles to various formats."""
    
    def __init__(self, profile: GitHubProfile):
        self.profile = profile
        self.logger = get_logger()
    
    def export_to_json(self, file_path: str, pretty: bool = True):
        """Export profile to JSON format."""
        try:
            # Convert dataclass to dictionary, handling Counter objects
            profile_dict = self._profile_to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(profile_dict, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(profile_dict, f, ensure_ascii=False, default=str)
            
            self.logger.info(f"Profile exported to JSON: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export profile to JSON: {e}")
            raise
    
    def export_to_html_portfolio(self, file_path: str):
        """Export profile as HTML portfolio page."""
        try:
            html_content = self._generate_portfolio_html()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Portfolio HTML exported: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export HTML portfolio: {e}")
            raise
    
    def export_resume_data(self, file_path: str):
        """Export resume-ready data in JSON format."""
        try:
            resume_data = self._generate_resume_data()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Resume data exported: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export resume data: {e}")
            raise
    
    def export_to_pdf_portfolio(self, file_path: str):
        """Export HTML portfolio as PDF using headless browser."""
        try:
            import tempfile
            import subprocess
            import os
            import platform
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                html_content = self._generate_portfolio_html()
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            try:
                # Try different PDF generation methods
                success = False
                
                # Method 1: Try weasyprint (if available)
                if not success:
                    success = self._pdf_with_weasyprint(temp_html_path, file_path)
                
                # Method 2: Try playwright (if available)
                if not success:
                    success = self._pdf_with_playwright(temp_html_path, file_path)
                
                # Method 3: Try wkhtmltopdf (if available)
                if not success:
                    success = self._pdf_with_wkhtmltopdf(temp_html_path, file_path)
                
                # Method 4: Try Chrome/Chromium headless (if available)
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
                
                self.logger.info(f"PDF portfolio exported: {file_path}")
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_html_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to export PDF portfolio: {e}")
            raise
    
    def _pdf_with_weasyprint(self, html_path: str, pdf_path: str) -> bool:
        """Generate PDF using WeasyPrint."""
        try:
            import weasyprint
            from urllib.request import pathname2url
            
            # Convert file path to file:// URL
            file_url = f"file://{pathname2url(os.path.abspath(html_path))}"
            
            # Generate PDF
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
                
                # Wait for content to load
                page.wait_for_load_state("networkidle")
                
                # Generate PDF
                page.pdf(
                    path=pdf_path,
                    format='A4',
                    print_background=True,
                    margin={
                        'top': '0.5in',
                        'bottom': '0.5in',
                        'left': '0.5in',
                        'right': '0.5in'
                    }
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
            
            # Check if wkhtmltopdf is available
            if not shutil.which('wkhtmltopdf'):
                return False
            
            # Run wkhtmltopdf
            cmd = [
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '0.75in',
                '--margin-right', '0.75in',
                '--margin-bottom', '0.75in',
                '--margin-left', '0.75in',
                '--enable-local-file-access',
                '--print-media-type',
                html_path,
                pdf_path
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
                    r"C:\Users\%s\AppData\Local\Google\Chrome\Application\chrome.exe" % os.getenv('USERNAME', ''),
                ]
            elif platform.system() == "Darwin":  # macOS
                chrome_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium",
                ]
            else:  # Linux
                chrome_paths = [
                    "google-chrome",
                    "google-chrome-stable",
                    "chromium-browser",
                    "chromium",
                ]
            
            chrome_exe = None
            for path in chrome_paths:
                if os.path.exists(path) or shutil.which(path):
                    chrome_exe = path
                    break
            
            if not chrome_exe:
                return False
            
            # Run Chrome in headless mode
            cmd = [
                chrome_exe,
                '--headless',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--print-to-pdf=' + pdf_path,
                '--print-to-pdf-no-header',
                f'file://{os.path.abspath(html_path)}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0 and os.path.exists(pdf_path)
            
        except Exception as e:
            self.logger.warning(f"Chrome PDF generation failed: {e}")
            return False
    
    def _profile_to_dict(self) -> dict:
        """Convert profile to dictionary, handling special types."""
        profile_dict = asdict(self.profile)
        
        # Convert Counter objects to regular dictionaries
        if isinstance(profile_dict.get('frameworks_used'), Counter):
            profile_dict['frameworks_used'] = dict(self.profile.frameworks_used)
        if isinstance(profile_dict.get('databases_used'), Counter):
            profile_dict['databases_used'] = dict(self.profile.databases_used)
        if isinstance(profile_dict.get('tools_used'), Counter):
            profile_dict['tools_used'] = dict(self.profile.tools_used)
        if isinstance(profile_dict.get('project_types'), Counter):
            profile_dict['project_types'] = dict(self.profile.project_types)
        
        return profile_dict
    
    def _generate_portfolio_html(self) -> str:
        """Generate enhanced HTML portfolio page with timeline, skills chart, and contact form."""
        
        # Generate timeline data from recent projects
        timeline_projects = sorted(
            [p for p in self.profile.featured_projects if p.get('updated_at')],
            key=lambda x: x['updated_at'], 
            reverse=True
        )[:8]
        
        # Calculate skills proficiency levels
        skills_with_levels = []
        for lang, percentage in sorted(self.profile.languages_percentage.items(), key=lambda x: x[1], reverse=True):
            if percentage >= 30:
                level = "Expert"
                level_width = min(percentage, 100)
            elif percentage >= 15:
                level = "Advanced" 
                level_width = min(percentage, 100)
            elif percentage >= 5:
                level = "Intermediate"
                level_width = min(percentage, 100)
            else:
                level = "Beginner"
                level_width = min(percentage, 100)
            skills_with_levels.append((lang, level, level_width, percentage))
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.profile.name or self.profile.username} - Developer Portfolio</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            background-color: #f8f9fa;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        /* Header Section */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 0;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20"><defs><pattern id="a" patternUnits="userSpaceOnUse" width="20" height="20" patternTransform="scale(2)"><rect width="100%" height="100%" fill="none"/><path d="m0 18 8-4 8 4 8-4 8 4v2H0z" fill="%23ffffff" fill-opacity="0.05"/></pattern></defs><rect width="100%" height="100%" fill="url(%23a)"/></svg>') repeat;
            opacity: 0.3;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        
        .profile-avatar {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            margin: 0 auto 30px;
            border: 5px solid rgba(255,255,255,0.3);
            transition: transform 0.3s ease;
        }}
        
        .profile-avatar:hover {{
            transform: scale(1.05);
        }}
        
        .header h1 {{
            font-size: 3.5rem;
            margin-bottom: 15px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.4rem;
            opacity: 0.95;
            margin-bottom: 15px;
        }}
        
        .header .bio {{
            font-size: 1.1rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .header-buttons {{
            margin-top: 30px;
        }}
        
        .btn {{
            display: inline-block;
            padding: 12px 30px;
            margin: 0 10px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            border: 2px solid rgba(255,255,255,0.3);
            transition: all 0.3s ease;
            font-weight: 500;
        }}
        
        .btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
        
        /* Navigation */
        .nav {{
            background: white;
            padding: 20px 0;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .nav ul {{
            display: flex;
            justify-content: center;
            list-style: none;
            flex-wrap: wrap;
        }}
        
        .nav li {{
            margin: 0 20px;
        }}
        
        .nav a {{
            text-decoration: none;
            color: #666;
            font-weight: 500;
            padding: 10px 0;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .nav a:hover {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 50px 0;
        }}
        
        .stat-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            border-top: 4px solid #667eea;
        }}
        
        .stat-card:hover {{
            transform: translateY(-10px);
        }}
        
        .stat-card .icon {{
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #333;
            display: block;
            margin-bottom: 10px;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        /* Section Styling */
        .section {{
            background: white;
            margin: 50px 0;
            padding: 50px;
            border-radius: 15px;
            box-shadow: 0 5px 25px rgba(0,0,0,0.08);
        }}
        
        .section h2 {{
            font-size: 2.5rem;
            margin-bottom: 40px;
            color: #333;
            text-align: center;
            position: relative;
        }}
        
        .section h2::after {{
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 4px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 2px;
        }}
        
        /* Skills Section */
        .skills-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 50px;
            align-items: center;
        }}
        
        .skills-list {{
            display: flex;
            flex-direction: column;
            gap: 25px;
        }}
        
        .skill-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .skill-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .skill-name {{
            font-weight: 600;
            color: #333;
            font-size: 1.1rem;
        }}
        
        .skill-level {{
            font-size: 0.9rem;
            color: #667eea;
            font-weight: 500;
        }}
        
        .skill-bar {{
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .skill-progress {{
            height: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 4px;
            transition: width 2s ease-in-out;
        }}
        
        .chart-container {{
            max-width: 400px;
            margin: 0 auto;
        }}
        
        /* Timeline */
        .timeline {{
            position: relative;
            padding: 20px 0;
        }}
        
        .timeline::before {{
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(to bottom, #667eea, #764ba2);
            transform: translateX(-50%);
        }}
        
        .timeline-item {{
            position: relative;
            margin: 40px 0;
            display: flex;
            align-items: center;
        }}
        
        .timeline-item:nth-child(odd) {{
            flex-direction: row-reverse;
        }}
        
        .timeline-content {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            width: 45%;
            position: relative;
            box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        }}
        
        .timeline-item:nth-child(odd) .timeline-content {{
            margin-right: 55%;
        }}
        
        .timeline-item:nth-child(even) .timeline-content {{
            margin-left: 55%;
        }}
        
        .timeline-content::before {{
            content: '';
            position: absolute;
            top: 50%;
            width: 0;
            height: 0;
            border: 15px solid transparent;
        }}
        
        .timeline-item:nth-child(odd) .timeline-content::before {{
            right: -30px;
            border-left-color: #f8f9fa;
            transform: translateY(-50%);
        }}
        
        .timeline-item:nth-child(even) .timeline-content::before {{
            left: -30px;
            border-right-color: #f8f9fa;
            transform: translateY(-50%);
        }}
        
        .timeline-dot {{
            position: absolute;
            left: 50%;
            width: 20px;
            height: 20px;
            background: #667eea;
            border-radius: 50%;
            transform: translateX(-50%);
            border: 4px solid white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        .timeline-date {{
            font-size: 0.9rem;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .timeline-title {{
            font-size: 1.2rem;
            font-weight: 700;
            color: #333;
            margin-bottom: 8px;
        }}
        
        .timeline-desc {{
            color: #666;
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        
        /* Projects Grid */
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        
        .project-card {{
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 25px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border: 1px solid #f0f0f0;
        }}
        
        .project-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .project-header {{
            padding: 25px 25px 0;
        }}
        
        .project-title {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .project-title a {{
            color: inherit;
            text-decoration: none;
        }}
        
        .project-title a:hover {{
            color: #667eea;
        }}
        
        .project-description {{
            color: #666;
            margin-bottom: 20px;
            font-size: 0.95rem;
            line-height: 1.6;
        }}
        
        .project-footer {{
            padding: 0 25px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .language-tag {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .project-stats {{
            display: flex;
            gap: 15px;
            color: #888;
            font-size: 0.9rem;
        }}
        
        .project-stats i {{
            margin-right: 5px;
        }}
        
        /* Contact Form */
        .contact-form {{
            background: #f8f9fa;
            padding: 40px;
            border-radius: 15px;
            margin: 40px 0;
        }}
        
        .form-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .form-group {{
            display: flex;
            flex-direction: column;
        }}
        
        .form-group.full-width {{
            grid-column: 1 / -1;
        }}
        
        .form-group label {{
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }}
        
        .form-group input,
        .form-group textarea {{
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }}
        
        .form-group input:focus,
        .form-group textarea:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .form-group textarea {{
            resize: vertical;
            min-height: 120px;
        }}
        
        .contact-button {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .contact-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }}
        
        /* Footer */
        .footer {{
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            text-align: center;
            padding: 60px 0 40px;
            margin-top: 80px;
        }}
        
        .footer-content {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 40px;
            margin-bottom: 40px;
            text-align: left;
        }}
        
        .footer-section h3 {{
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #ecf0f1;
        }}
        
        .footer-section p,
        .footer-section a {{
            color: #bdc3c7;
            text-decoration: none;
            line-height: 1.8;
        }}
        
        .footer-section a:hover {{
            color: #667eea;
        }}
        
        .social-links {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin: 20px 0;
        }}
        
        .social-links a {{
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.1);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }}
        
        .social-links a:hover {{
            background: #667eea;
            transform: translateY(-3px);
        }}
        
        .footer-bottom {{
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 30px;
            text-align: center;
            color: #bdc3c7;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .container {{ padding: 0 15px; }}
            .header h1 {{ font-size: 2.5rem; }}
            .skills-container {{ grid-template-columns: 1fr; gap: 30px; }}
            .timeline::before {{ left: 20px; }}
            .timeline-item {{ flex-direction: column !important; }}
            .timeline-content {{ width: 100%; margin: 0 0 0 40px !important; }}
            .timeline-content::before {{ display: none; }}
            .form-grid {{ grid-template-columns: 1fr; }}
            .projects-grid {{ grid-template-columns: 1fr; }}
            .nav ul {{ flex-direction: column; align-items: center; }}
            .nav li {{ margin: 5px 0; }}
        }}
        
        /* Animation */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .animate-on-scroll {{
            animation: fadeInUp 0.8s ease-out;
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <img src="{self.profile.avatar_url or 'https://via.placeholder.com/150'}" alt="Profile Avatar" class="profile-avatar">
                <h1>{self.profile.name or self.profile.username}</h1>
                <p class="subtitle">{self.profile.developer_type} Developer • {self.profile.experience_level}</p>
                <p class="bio">{self.profile.bio or f'Passionate developer with {self.profile.total_repositories} repositories and {self.profile.total_stars_received} stars'}</p>
                <div class="header-buttons">
                    <a href="#contact" class="btn"><i class="fas fa-envelope"></i> Get In Touch</a>
                    <a href="{self.profile.profile_url}" target="_blank" class="btn"><i class="fab fa-github"></i> View GitHub</a>
                </div>
            </div>
        </div>
    </header>
    
    <nav class="nav">
        <div class="container">
            <ul>
                <li><a href="#about">About</a></li>
                <li><a href="#skills">Skills</a></li>
                <li><a href="#timeline">Timeline</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon"><i class="fas fa-code-branch"></i></div>
                <span class="number">{self.profile.total_repositories}</span>
                <div class="label">Total Repositories</div>
            </div>
            <div class="stat-card">
                <div class="icon"><i class="fas fa-star"></i></div>
                <span class="number">{self.profile.total_stars_received}</span>
                <div class="label">Stars Received</div>
            </div>
            <div class="stat-card">
                <div class="icon"><i class="fas fa-code"></i></div>
                <span class="number">{len(self.profile.languages_used)}</span>
                <div class="label">Languages Used</div>
            </div>
            <div class="stat-card">
                <div class="icon"><i class="fas fa-users"></i></div>
                <span class="number">{self.profile.collaboration_score:.0f}</span>
                <div class="label">Collaboration Score</div>
            </div>
        </div>
        
        <section id="skills" class="section">
            <h2><i class="fas fa-cogs"></i> Technical Skills</h2>
            <div class="skills-container">
                <div class="skills-list">"""
        
        # Add skills with progress bars
        for lang, level, width, percentage in skills_with_levels[:8]:
            html += f"""
                    <div class="skill-item">
                        <div class="skill-header">
                            <span class="skill-name">{lang}</span>
                            <span class="skill-level">{level}</span>
                        </div>
                        <div class="skill-bar">
                            <div class="skill-progress" style="width: {width}%"></div>
                        </div>
                    </div>"""
        
        html += f"""
                </div>
                <div class="chart-container">
                    <canvas id="languageChart"></canvas>
                </div>
            </div>
        </section>
        
        <section id="timeline" class="section">
            <h2><i class="fas fa-clock"></i> Development Timeline</h2>
            <div class="timeline">"""
        
        # Add timeline items
        for i, project in enumerate(timeline_projects):
            try:
                from datetime import datetime as dt
                updated_date = dt.fromisoformat(project['updated_at'].replace('Z', '+00:00'))
                date_str = updated_date.strftime('%B %Y')
            except:
                date_str = "Recent"
            
            html += f"""
                <div class="timeline-item">
                    <div class="timeline-content">
                        <div class="timeline-date">{date_str}</div>
                        <div class="timeline-title">{project['name']}</div>
                        <div class="timeline-desc">{project['description'][:100] if project.get('description') else 'Active development on this project'}{'...' if len(project.get('description', '')) > 100 else ''}</div>
                    </div>
                    <div class="timeline-dot"></div>
                </div>"""
        
        html += f"""
            </div>
        </section>
        
        <section id="projects" class="section">
            <h2><i class="fas fa-folder-open"></i> Featured Projects</h2>
            <div class="projects-grid">"""
        
        # Add featured projects
        for project in self.profile.featured_projects[:6]:
            html += f"""
                <div class="project-card">
                    <div class="project-header">
                        <h3 class="project-title">
                            <a href="{project['url']}" target="_blank">{project['name']}</a>
                        </h3>
                        <p class="project-description">{project['description'][:200] if project.get('description') else 'No description available'}{'...' if len(project.get('description', '')) > 200 else ''}</p>
                    </div>
                    <div class="project-footer">
                        <span class="language-tag">{project['language']}</span>
                        <div class="project-stats">
                            <span><i class="fas fa-star"></i> {project['stars']}</span>
                            <span><i class="fas fa-code-branch"></i> {project['forks']}</span>
                        </div>
                    </div>
                </div>"""
        
        html += f"""
            </div>
        </section>
        
        <section id="contact" class="section">
            <h2><i class="fas fa-envelope"></i> Get In Touch</h2>
            <p style="text-align: center; margin-bottom: 30px; font-size: 1.1rem; color: #666;">
                Interested in collaborating or have a project in mind? Let's connect!
            </p>
            
            <form class="contact-form" onsubmit="handleContactForm(event)">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="name">Name *</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email *</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group full-width">
                        <label for="subject">Subject</label>
                        <input type="text" id="subject" name="subject" placeholder="Project collaboration, job opportunity, etc.">
                    </div>
                    <div class="form-group full-width">
                        <label for="message">Message *</label>
                        <textarea id="message" name="message" required placeholder="Tell me about your project or opportunity..."></textarea>
                    </div>
                </div>
                <div style="text-align: center;">
                    <button type="submit" class="contact-button">
                        <i class="fas fa-paper-plane"></i> Send Message
                    </button>
                </div>
            </form>
            
            <div style="text-align: center; margin-top: 40px;">
                <p><strong>Preferred Contact:</strong> {self.profile.email or 'Via GitHub'}</p>
                {f'<p><strong>Location:</strong> {self.profile.location}</p>' if self.profile.location else ''}
                {f'<p><strong>Website:</strong> <a href="{self.profile.website}" target="_blank">{self.profile.website}</a></p>' if self.profile.website else ''}
            </div>
        </section>
    </div>
    
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>About</h3>
                    <p>{self.profile.bio or f'{self.profile.developer_type} developer passionate about creating innovative solutions.'}</p>
                </div>
                <div class="footer-section">
                    <h3>Quick Stats</h3>
                    <p>{self.profile.total_repositories} Repositories</p>
                    <p>{self.profile.total_stars_received} Stars Earned</p>
                    <p>{len(self.profile.primary_languages)} Main Languages</p>
                </div>
                <div class="footer-section">
                    <h3>Connect</h3>
                    <p><a href="{self.profile.profile_url}" target="_blank">GitHub Profile</a></p>
                    {f'<p><a href="{self.profile.website}" target="_blank">Personal Website</a></p>' if self.profile.website else ''}
                    <p><a href="#contact">Send Message</a></p>
                </div>
            </div>
            
            <div class="social-links">
                <a href="{self.profile.profile_url}" target="_blank" title="GitHub">
                    <i class="fab fa-github"></i>
                </a>"""
        
        if self.profile.website:
            html += f"""
                <a href="{self.profile.website}" target="_blank" title="Website">
                    <i class="fas fa-globe"></i>
                </a>"""
        
        if self.profile.email:
            html += f"""
                <a href="mailto:{self.profile.email}" title="Email">
                    <i class="fas fa-envelope"></i>
                </a>"""
        
        html += f"""
            </div>
            
            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} {self.profile.name or self.profile.username}. Portfolio generated by RepoReadme Profile Builder.</p>
                <p>Last updated: {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
        </div>
    </footer>
    
    <script>
        // Language Chart
        const ctx = document.getElementById('languageChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: [{', '.join(f"'{lang}'" for lang, _, _, _ in skills_with_levels[:6])}],
                datasets: [{{
                    data: [{', '.join(f'{pct:.1f}' for _, _, _, pct in skills_with_levels[:6])}],
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b'
                    ],
                    borderWidth: 3,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 20,
                            font: {{
                                size: 12
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Contact Form Handler
        function handleContactForm(event) {{
            event.preventDefault();
            const formData = new FormData(event.target);
            const name = formData.get('name');
            const email = formData.get('email');
            const subject = formData.get('subject') || 'Portfolio Contact';
            const message = formData.get('message');
            
            // Create mailto link
            const mailtoLink = `mailto:{self.profile.email or 'contact@example.com'}?subject=${{encodeURIComponent(subject)}}&body=${{encodeURIComponent(
                `Name: ${{name}}\\nEmail: ${{email}}\\n\\nMessage:\\n${{message}}`
            )}}`;
            
            window.location.href = mailtoLink;
            
            // Show success message
            alert('Thank you for your message! Your email client should open with the pre-filled message.');
        }}
        
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
        
        // Animate skill bars on scroll
        const observerOptions = {{
            threshold: 0.3,
            rootMargin: '0px 0px -50px 0px'
        }};
        
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const skillBars = entry.target.querySelectorAll('.skill-progress');
                    skillBars.forEach(bar => {{
                        const width = bar.style.width;
                        bar.style.width = '0%';
                        setTimeout(() => {{
                            bar.style.width = width;
                        }}, 100);
                    }});
                }}
            }});
        }}, observerOptions);
        
        const skillsSection = document.getElementById('skills');
        if (skillsSection) {{
            observer.observe(skillsSection);
        }}
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_resume_data(self) -> dict:
        """Generate resume-ready data structure."""
        return {
            "personal_info": {
                "name": self.profile.name,
                "username": self.profile.username,
                "bio": self.profile.bio,
                "location": self.profile.location,
                "email": self.profile.email,
                "website": self.profile.website,
                "github": self.profile.profile_url
            },
            "professional_summary": {
                "developer_type": self.profile.developer_type,
                "experience_level": self.profile.experience_level,
                "specializations": self.profile.specializations,
                "total_repositories": self.profile.total_repositories,
                "stars_received": self.profile.total_stars_received
            },
            "technical_skills": {
                "primary_languages": self.profile.primary_languages,
                "languages_proficiency": self.profile.languages_percentage,
                "frameworks": list(self.profile.frameworks_used.keys()),
                "databases": list(self.profile.databases_used.keys()),
                "tools": list(self.profile.tools_used.keys())
            },
            "projects": {
                "featured_projects": self.profile.featured_projects,
                "project_categories": self.profile.project_categories,
                "most_starred": self.profile.most_starred_repos[:5],
                "recent_work": self.profile.recent_active_repos[:5]
            },
            "achievements": {
                "total_stars": self.profile.total_stars_received,
                "total_forks": self.profile.total_forks_received,
                "collaboration_score": self.profile.collaboration_score,
                "innovation_score": self.profile.innovation_score,
                "achievements": self.profile.achievements
            },
            "development_practices": {
                "repositories_with_readme": self.profile.repositories_with_readme,
                "repositories_with_tests": self.profile.repositories_with_tests,
                "repositories_with_docs": self.profile.repositories_with_docs,
                "repositories_with_ci": self.profile.repositories_with_ci
            },
            "metadata": {
                "generated_date": self.profile.analysis_date,
                "total_analyzed_repos": self.profile.total_analyzed_repos,
                "analysis_duration": self.profile.analysis_duration
            }
        }