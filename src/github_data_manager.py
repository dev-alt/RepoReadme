#!/usr/bin/env python3
"""
GitHub Data Manager

Centralized management of GitHub data with local storage capabilities.
Handles single repos, all public repos, all repos, and local file downloads.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import tempfile
import shutil
import zipfile
import requests
from dataclasses import dataclass, asdict

try:
    from github import Github, GithubException
    from github.Repository import Repository
    from github.ContentFile import ContentFile
    GITHUB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PyGithub not available: {e}")
    Github = None
    Repository = None
    GithubException = Exception
    ContentFile = None
    GITHUB_AVAILABLE = False

try:
    from .utils.logger import get_logger
    from .profile_builder import GitHubProfile
except ImportError:
    from utils.logger import get_logger
    from profile_builder import GitHubProfile


@dataclass
class RepoData:
    """Container for repository data."""
    name: str
    full_name: str
    description: str
    url: str
    clone_url: str
    ssh_url: str
    language: str
    languages: Dict[str, int]
    topics: List[str]
    stars: int
    forks: int
    watchers: int
    size: int
    created_at: str
    updated_at: str
    pushed_at: str
    default_branch: str
    is_private: bool
    is_fork: bool
    is_archived: bool
    license_name: Optional[str] = None
    has_readme: bool = False
    has_license: bool = False
    has_dockerfile: bool = False
    has_ci: bool = False
    has_tests: bool = False
    local_path: Optional[str] = None
    files_downloaded: bool = False


@dataclass
class GitHubUserData:
    """Container for GitHub user data."""
    username: str
    name: Optional[str]
    email: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    website: Optional[str]
    avatar_url: str
    public_repos: int
    private_repos: int
    followers: int
    following: int
    created_at: str
    updated_at: str
    repositories: List[RepoData]
    total_stars: int = 0
    total_forks: int = 0
    languages_used: Dict[str, int] = None
    profile_data: Optional[GitHubProfile] = None


class GitHubDataManager:
    """Centralized GitHub data management with local storage capabilities."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the GitHub data manager."""
        self.logger = get_logger()
        self.github_client: Optional[Github] = None
        self.current_token: Optional[str] = None
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / '.reporeadme' / 'github_cache'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up local repos directory
        self.local_repos_dir = Path.home() / '.reporeadme' / 'local_repos'
        self.local_repos_dir.mkdir(parents=True, exist_ok=True)
        
        # Current data state
        self.current_user_data: Optional[GitHubUserData] = None
        self.progress_callback: Optional[Callable[[str, int], None]] = None
        
    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
        
    def _update_progress(self, message: str, progress: int = 0):
        """Update progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(message, progress)
        self.logger.info(message)
    
    def set_github_token(self, token: str):
        """Set GitHub authentication token."""
        try:
            if not GITHUB_AVAILABLE or Github is None:
                raise RuntimeError("PyGithub not available")
            
            # Strip whitespace from token to prevent header issues
            clean_token = token.strip() if token else ""
            self.github_client = Github(clean_token) if clean_token else Github()
            self.current_token = clean_token
            
            # Test the connection
            user = self.github_client.get_user()
            self._update_progress(f"✅ Connected to GitHub as {user.login}")
            
        except Exception as e:
            self.logger.error(f"Failed to set GitHub token: {e}")
            raise
    
    def set_username_only(self, username: str):
        """Set up for public-only access with username."""
        try:
            if not GITHUB_AVAILABLE or Github is None:
                raise RuntimeError("PyGithub not available")
                
            self.github_client = Github()
            self.current_token = None
            
            # Test by getting user info
            user = self.github_client.get_user(username)
            self._update_progress(f"✅ Connected to GitHub for user {username} (public access)")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to GitHub: {e}")
            raise
    
    async def fetch_user_data(self, username: str, scope: str = "public", 
                            include_files: bool = False) -> GitHubUserData:
        """
        Fetch comprehensive user data from GitHub.
        
        Args:
            username: GitHub username
            scope: "single" (just README), "public", "all", or "private"
            include_files: Whether to download repository files locally
        """
        if not self.github_client:
            raise RuntimeError("GitHub client not initialized")
        
        self._update_progress("🔍 Fetching user information...", 5)
        
        try:
            # Validate username before making API call
            if not username or not username.strip():
                raise ValueError("Username cannot be empty")
            
            username = username.strip()
            self.logger.info(f"Fetching GitHub user: '{username}'")
            
            user = self.github_client.get_user(username)
            
            # Get basic user info (with safe attribute access)
            try:
                private_repos = user.total_private_repos if hasattr(user, 'total_private_repos') else 0
            except Exception:
                # If we can't access private repo count (common with public tokens), default to 0
                private_repos = 0
            
            user_data = GitHubUserData(
                username=user.login,
                name=user.name,
                email=user.email,
                bio=user.bio,
                location=user.location,
                website=user.blog,
                avatar_url=user.avatar_url,
                public_repos=user.public_repos,
                private_repos=private_repos,
                followers=user.followers,
                following=user.following,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat(),
                repositories=[],
                languages_used={}
            )
            
            # Fetch repositories based on scope
            repositories = await self._fetch_repositories(user, scope)
            
            # Process each repository
            total_repos = len(repositories)
            for i, repo in enumerate(repositories):
                progress = int(20 + (i / total_repos) * 60)  # 20-80% for repo processing
                
                self._update_progress(f"📊 Analyzing repository {i+1}/{total_repos}: {repo.name}", progress)
                
                repo_data = await self._process_repository(repo, include_files)
                user_data.repositories.append(repo_data)
                
                # Update aggregated stats
                user_data.total_stars += repo_data.stars
                user_data.total_forks += repo_data.forks
                
                # Aggregate language usage
                for lang, bytes_count in repo_data.languages.items():
                    if lang in user_data.languages_used:
                        user_data.languages_used[lang] += bytes_count
                    else:
                        user_data.languages_used[lang] = bytes_count
            
            # Cache the data
            self._update_progress("💾 Caching data...", 85)
            await self._cache_user_data(user_data)
            
            # Generate GitHub profile
            self._update_progress("🚀 Building GitHub profile...", 90)
            user_data.profile_data = await self._build_github_profile(user_data)
            
            self.current_user_data = user_data
            self._update_progress("✅ GitHub data fetch completed!", 100)
            
            return user_data
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to fetch user data: {e}")
            
            # Provide more helpful error messages for common issues
            if "404" in error_msg:
                if "Not Found" in error_msg:
                    helpful_msg = f"GitHub user '{username}' not found. Please check the username is correct."
                else:
                    helpful_msg = f"GitHub API returned 404. User '{username}' may not exist or be private."
                self._update_progress(f"❌ Error: {helpful_msg}", 0)
            else:
                self._update_progress(f"❌ Error: {error_msg}", 0)
            raise
    
    async def _fetch_repositories(self, user, scope: str) -> List[Repository]:
        """Fetch repositories based on scope."""
        repositories = []
        
        if scope == "single":
            # Just get repositories for README analysis
            self._update_progress("📂 Fetching repository list for README analysis...")
            for repo in user.get_repos(type='owner', sort='updated'):
                if not repo.fork:  # Skip forks for single mode
                    repositories.append(repo)
                    if len(repositories) >= 10:  # Limit for single mode
                        break
                        
        elif scope == "public":
            self._update_progress("📂 Fetching public repositories...")
            for repo in user.get_repos(type='public', sort='updated'):
                repositories.append(repo)
                
        elif scope == "all":
            self._update_progress("📂 Fetching all repositories (public + private)...")
            # First get public repos
            for repo in user.get_repos(type='public', sort='updated'):
                repositories.append(repo)
            
            # Then get private repos (if accessible)
            try:
                for repo in user.get_repos(type='private', sort='updated'):
                    repositories.append(repo)
                self.logger.info(f"Successfully fetched {len([r for r in repositories if r.private])} private repositories")
            except Exception as e:
                self.logger.warning(f"Could not access private repositories: {e}")
                self.logger.info("This may be due to insufficient token permissions or no private repos exist")
                
        elif scope == "private":
            self._update_progress("📂 Fetching private repositories...")
            for repo in user.get_repos(type='private', sort='updated'):
                repositories.append(repo)
        
        self.logger.info(f"Found {len(repositories)} repositories for scope: {scope}")
        return repositories
    
    async def _process_repository(self, repo: Repository, include_files: bool = False) -> RepoData:
        """Process a single repository and optionally download files."""
        
        # Get languages (this can fail, so handle gracefully)
        try:
            languages = repo.get_languages()
        except:
            languages = {}
        
        # Check for special files
        has_readme = self._repo_has_file(repo, ['README.md', 'README.rst', 'README.txt', 'README'])
        has_license = self._repo_has_file(repo, ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'LICENCE'])
        has_dockerfile = self._repo_has_file(repo, ['Dockerfile', 'dockerfile'])
        has_ci = self._repo_has_file(repo, ['.github/workflows', '.gitlab-ci.yml', '.travis.yml', 'Jenkinsfile'])
        has_tests = self._repo_has_file(repo, ['test', 'tests', '__tests__', 'spec', 'specs'])
        
        # Get license info
        license_name = None
        try:
            if repo.license:
                license_name = repo.license.name
        except:
            pass
        
        repo_data = RepoData(
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description or "",
            url=repo.html_url,
            clone_url=repo.clone_url,
            ssh_url=repo.ssh_url,
            language=repo.language or "Unknown",
            languages=languages,
            topics=repo.get_topics(),
            stars=repo.stargazers_count,
            forks=repo.forks_count,
            watchers=repo.watchers_count,
            size=repo.size,
            created_at=repo.created_at.isoformat(),
            updated_at=repo.updated_at.isoformat(),
            pushed_at=repo.pushed_at.isoformat() if repo.pushed_at else repo.updated_at.isoformat(),
            default_branch=repo.default_branch,
            is_private=repo.private,
            is_fork=repo.fork,
            is_archived=repo.archived,
            license_name=license_name,
            has_readme=has_readme,
            has_license=has_license,
            has_dockerfile=has_dockerfile,
            has_ci=has_ci,
            has_tests=has_tests
        )
        
        # Download files if requested
        if include_files:
            local_path = await self._download_repository_files(repo)
            repo_data.local_path = local_path
            repo_data.files_downloaded = True
        
        return repo_data
    
    def _repo_has_file(self, repo: Repository, filenames: List[str]) -> bool:
        """Check if repository has any of the specified files."""
        try:
            contents = repo.get_contents("")
            file_list = []
            
            for content in contents:
                if content.type == "file":
                    file_list.append(content.name)
                elif content.type == "dir" and content.name in ['.github', '.gitlab']:
                    # Check inside .github or .gitlab directories
                    try:
                        subcontents = repo.get_contents(content.path)
                        for subcontent in subcontents:
                            if subcontent.type == "file":
                                file_list.append(f"{content.name}/{subcontent.name}")
                            elif subcontent.name == "workflows":
                                # Check workflows directory
                                try:
                                    workflows = repo.get_contents(subcontent.path)
                                    if len(list(workflows)) > 0:
                                        file_list.append(".github/workflows")
                                except:
                                    pass
                    except:
                        pass
            
            # Check if any of our target files exist
            for filename in filenames:
                if filename in file_list:
                    return True
                # Check partial matches for directories
                if any(f.startswith(filename) for f in file_list):
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to check files in {repo.name}: {e}")
            return False
    
    async def _download_repository_files(self, repo: Repository) -> str:
        """Download repository files to local storage."""
        repo_local_dir = self.local_repos_dir / repo.owner.login / repo.name
        repo_local_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if repository files already exist
        if repo_local_dir.exists() and any(repo_local_dir.iterdir()):
            # Check if there are actual content files (not just empty dirs)
            has_content = any(
                item.is_file() or (item.is_dir() and any(item.iterdir()))
                for item in repo_local_dir.iterdir()
            )
            if has_content:
                self.logger.info(f"Repository {repo.name} already downloaded, skipping...")
                return str(repo_local_dir)
        
        try:
            # Download as zip file
            zip_url = f"https://github.com/{repo.full_name}/archive/refs/heads/{repo.default_branch}.zip"
            
            self.logger.info(f"Downloading {repo.name} files...")
            
            # Use requests to download the zip
            response = requests.get(zip_url, stream=True)
            response.raise_for_status()
            
            # Save zip temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_zip.write(chunk)
                temp_zip_path = temp_zip.name
            
            # Extract zip
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(repo_local_dir)
            
            # Clean up temp file
            os.unlink(temp_zip_path)
            
            # Move files from extracted folder to repo directory
            extracted_folder = repo_local_dir / f"{repo.name}-{repo.default_branch}"
            if extracted_folder.exists():
                for item in extracted_folder.iterdir():
                    shutil.move(str(item), repo_local_dir / item.name)
                extracted_folder.rmdir()
            
            self.logger.info(f"✅ Downloaded {repo.name} to {repo_local_dir}")
            return str(repo_local_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to download {repo.name}: {e}")
            return ""
    
    async def _build_github_profile(self, user_data: GitHubUserData) -> GitHubProfile:
        """Build GitHubProfile from user data."""
        profile = GitHubProfile()
        
        # Basic info
        profile.username = user_data.username
        profile.name = user_data.name
        profile.email = user_data.email
        profile.bio = user_data.bio
        profile.location = user_data.location
        profile.website = user_data.website
        profile.avatar_url = user_data.avatar_url
        profile.profile_url = f"https://github.com/{user_data.username}"
        
        # Repository stats
        profile.total_repositories = len(user_data.repositories)
        profile.public_repositories = len([r for r in user_data.repositories if not r.is_private])
        profile.private_repositories = len([r for r in user_data.repositories if r.is_private])
        profile.original_repositories = len([r for r in user_data.repositories if not r.is_fork])
        profile.forked_repositories = len([r for r in user_data.repositories if r.is_fork])
        
        # Engagement stats
        profile.total_stars_received = user_data.total_stars
        profile.total_forks_received = user_data.total_forks
        profile.followers = user_data.followers
        profile.following = user_data.following
        
        # Languages
        profile.languages_used = user_data.languages_used
        total_bytes = sum(user_data.languages_used.values()) or 1
        profile.languages_percentage = {
            lang: (bytes_count / total_bytes) * 100 
            for lang, bytes_count in user_data.languages_used.items()
        }
        profile.primary_languages = sorted(
            user_data.languages_used.keys(), 
            key=lambda x: user_data.languages_used[x], 
            reverse=True
        )[:10]
        
        # Project types
        profile.has_web_projects = any(
            'web' in r.topics or 'website' in r.topics or 
            r.language in ['JavaScript', 'TypeScript', 'HTML', 'CSS'] or
            'react' in r.topics or 'vue' in r.topics or 'angular' in r.topics
            for r in user_data.repositories
        )
        
        profile.has_mobile_projects = any(
            'mobile' in r.topics or 'android' in r.topics or 'ios' in r.topics or
            r.language in ['Swift', 'Kotlin', 'Java', 'Dart'] or
            'react-native' in r.topics or 'flutter' in r.topics
            for r in user_data.repositories
        )
        
        profile.has_apis = any(
            'api' in r.topics or 'rest' in r.topics or 'graphql' in r.topics or
            'fastapi' in r.topics or 'express' in r.topics
            for r in user_data.repositories
        )
        
        profile.has_libraries = any(
            'library' in r.topics or 'framework' in r.topics or 'package' in r.topics
            for r in user_data.repositories
        )
        
        profile.has_cli_tools = any(
            'cli' in r.topics or 'command-line' in r.topics or 'tool' in r.topics
            for r in user_data.repositories
        )
        
        # Quality metrics
        profile.repositories_with_readme = sum(1 for r in user_data.repositories if r.has_readme)
        profile.repositories_with_tests = sum(1 for r in user_data.repositories if r.has_tests)
        profile.repositories_with_ci = sum(1 for r in user_data.repositories if r.has_ci)
        profile.repositories_with_docker = sum(1 for r in user_data.repositories if r.has_dockerfile)
        
        # Calculate scores
        if profile.total_repositories > 0:
            profile.collaboration_score = min(100, (
                (profile.repositories_with_readme / profile.total_repositories * 40) +
                (profile.public_repositories / profile.total_repositories * 30) +
                (profile.total_forks_received / max(profile.total_repositories, 1) * 30)
            ))
            
            profile.innovation_score = min(100, (
                (profile.total_stars_received / max(profile.original_repositories, 1) * 50) +
                (len(profile.languages_used) * 5) +
                (profile.original_repositories / profile.total_repositories * 45)
            ))
        
        # Developer classification
        if profile.total_stars_received > 500 or profile.total_repositories > 50:
            profile.experience_level = "Senior"
        elif profile.total_stars_received > 100 or profile.total_repositories > 20:
            profile.experience_level = "Mid-level"
        else:
            profile.experience_level = "Junior"
        
        # Developer type
        if profile.has_web_projects and profile.has_mobile_projects:
            profile.developer_type = "Full-stack Developer"
        elif profile.has_web_projects:
            profile.developer_type = "Frontend Developer"
        elif profile.has_apis or any(lang in ['Python', 'Java', 'Go', 'Rust'] for lang in profile.primary_languages[:3]):
            profile.developer_type = "Backend Developer"
        else:
            profile.developer_type = "Software Developer"
        
        # Featured projects
        featured_repos = sorted([r for r in user_data.repositories if not r.is_fork], 
                              key=lambda x: x.stars, reverse=True)[:6]
        
        profile.featured_projects = [
            {
                'name': r.name,
                'description': r.description,
                'url': r.url,
                'stars': r.stars,
                'forks': r.forks,
                'language': r.language,
                'topics': r.topics,
                'updated_at': r.updated_at,
                'has_readme': r.has_readme,
                'project_type': self._classify_project_type(r)
            }
            for r in featured_repos
        ]
        
        return profile
    
    def _classify_project_type(self, repo_data: RepoData) -> str:
        """Classify project type based on repository data."""
        topics = [t.lower() for t in repo_data.topics]
        
        if any(t in topics for t in ['web', 'website', 'webapp', 'frontend']):
            return 'web-app'
        elif any(t in topics for t in ['mobile', 'android', 'ios']):
            return 'mobile-app'
        elif any(t in topics for t in ['api', 'rest', 'graphql']):
            return 'api'
        elif any(t in topics for t in ['library', 'framework', 'package']):
            return 'library'
        elif any(t in topics for t in ['cli', 'command-line', 'tool']):
            return 'cli-tool'
        else:
            return 'other'
    
    async def _cache_user_data(self, user_data: GitHubUserData):
        """Cache user data to local storage."""
        cache_file = self.cache_dir / f"{user_data.username}_data.json"
        
        try:
            # Convert to dict for JSON serialization
            data_dict = asdict(user_data)
            # Remove profile_data as it's too complex for JSON
            if 'profile_data' in data_dict:
                del data_dict['profile_data']
            
            with cache_file.open('w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, default=str)
                
            self.logger.info(f"Cached user data to {cache_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to cache user data: {e}")
    
    def get_cached_user_data(self, username: str) -> Optional[GitHubUserData]:
        """Load cached user data if available."""
        cache_file = self.cache_dir / f"{username}_data.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with cache_file.open('r', encoding='utf-8') as f:
                data_dict = json.load(f)
            
            # Convert back to GitHubUserData
            # Handle the repositories list
            repos = []
            for repo_dict in data_dict.get('repositories', []):
                repos.append(RepoData(**repo_dict))
            data_dict['repositories'] = repos
            
            user_data = GitHubUserData(**data_dict)
            
            self.logger.info(f"Loaded cached data for {username}")
            return user_data
            
        except Exception as e:
            self.logger.error(f"Failed to load cached data: {e}")
            return None
    
    def get_local_repositories_path(self, username: str) -> Path:
        """Get the local path where repositories are stored."""
        return self.local_repos_dir / username
    
    def cleanup_old_cache(self, days: int = 7):
        """Clean up cache files older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for cache_file in self.cache_dir.glob("*_data.json"):
            if cache_file.stat().st_mtime < cutoff_time:
                cache_file.unlink()
                self.logger.info(f"Removed old cache file: {cache_file.name}")