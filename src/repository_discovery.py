"""
Repository Discovery Module

Discovers and scans all repositories a user has access to across different Git providers.
"""

import os
import json
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, AsyncGenerator, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import tempfile
import shutil

try:
    from github import Github, GithubException
    from gitlab import Gitlab
    from gitlab.exceptions import GitlabError
except ImportError:
    Github = None
    Gitlab = None
    GithubException = Exception
    GitlabError = Exception

try:
    from .utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger


@dataclass
class RepositoryInfo:
    """Information about a discovered repository."""
    name: str
    full_name: str
    url: str
    clone_url: str
    ssh_url: str
    description: str
    language: str
    stars: int
    forks: int
    is_private: bool
    is_fork: bool
    provider: str  # github, gitlab, bitbucket, etc.
    owner: str
    created_at: str
    updated_at: str
    size_kb: int
    default_branch: str
    topics: List[str]
    has_readme: bool
    license: Optional[str] = None


@dataclass
class DiscoveryConfig:
    """Configuration for repository discovery."""
    # Provider settings
    include_github: bool = True
    include_gitlab: bool = True
    include_bitbucket: bool = False
    
    # Authentication
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None
    ssh_key_path: Optional[str] = None
    
    # Filters
    include_private: bool = True
    include_forks: bool = False
    include_archived: bool = False
    min_stars: int = 0
    languages: List[str] = None  # None = all languages
    exclude_patterns: List[str] = None  # Repository name patterns to exclude
    
    # Limits
    max_repos_per_provider: int = 1000
    concurrent_requests: int = 10


class RepositoryDiscovery:
    """Main repository discovery engine."""
    
    def __init__(self, config: DiscoveryConfig):
        """Initialize the discovery engine."""
        self.config = config
        self.logger = get_logger()
        self.discovered_repos: List[RepositoryInfo] = []
        self.stats = {
            'total_discovered': 0,
            'github_repos': 0,
            'gitlab_repos': 0,
            'private_repos': 0,
            'public_repos': 0,
            'forks': 0,
            'languages': {},
            'providers': {}
        }
        
    async def discover_all_repositories(self, 
                                      progress_callback: Optional[Callable] = None) -> List[RepositoryInfo]:
        """Discover repositories from all configured providers."""
        self.logger.info("Starting repository discovery across all providers")
        
        all_repos = []
        tasks = []
        
        # GitHub discovery
        if self.config.include_github and self._can_use_github():
            tasks.append(self._discover_github_repositories(progress_callback))
        
        # GitLab discovery
        if self.config.include_gitlab and self._can_use_gitlab():
            tasks.append(self._discover_gitlab_repositories(progress_callback))
        
        # Execute all discovery tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Repository discovery failed: {result}")
                else:
                    all_repos.extend(result)
        
        # Apply filters and deduplication
        filtered_repos = self._filter_and_deduplicate(all_repos)
        
        # Update statistics
        self._update_statistics(filtered_repos)
        
        self.discovered_repos = filtered_repos
        self.logger.info(f"Discovery completed: {len(filtered_repos)} repositories found")
        
        return filtered_repos
    
    async def _discover_github_repositories(self, 
                                          progress_callback: Optional[Callable] = None) -> List[RepositoryInfo]:
        """Discover GitHub repositories."""
        if not Github:
            self.logger.warning("PyGithub not available, skipping GitHub discovery")
            return []
        
        try:
            # Initialize GitHub client
            if self.config.github_token:
                github = Github(self.config.github_token)
            else:
                github = Github()  # Anonymous access
            
            user = github.get_user()
            repos = []
            
            self.logger.info(f"Discovering GitHub repositories for user: {user.login}")
            
            # Get user's repositories
            repo_count = 0
            for repo in user.get_repos():
                if repo_count >= self.config.max_repos_per_provider:
                    break
                
                try:
                    repo_info = await self._convert_github_repo(repo)
                    if repo_info:
                        repos.append(repo_info)
                        repo_count += 1
                        
                        if progress_callback:
                            progress_callback(f"GitHub: Found {repo.full_name}", repo_count)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process GitHub repo {repo.full_name}: {e}")
                    continue
            
            # Get organization repositories if token provided
            if self.config.github_token:
                try:
                    for org in user.get_orgs():
                        if repo_count >= self.config.max_repos_per_provider:
                            break
                            
                        for repo in org.get_repos():
                            if repo_count >= self.config.max_repos_per_provider:
                                break
                                
                            try:
                                repo_info = await self._convert_github_repo(repo)
                                if repo_info:
                                    repos.append(repo_info)
                                    repo_count += 1
                                    
                                    if progress_callback:
                                        progress_callback(f"GitHub Org: Found {repo.full_name}", repo_count)
                                        
                            except Exception as e:
                                self.logger.warning(f"Failed to process GitHub org repo {repo.full_name}: {e}")
                                continue
                                
                except Exception as e:
                    self.logger.info(f"Could not access organizations: {e}")
            
            self.logger.info(f"GitHub discovery completed: {len(repos)} repositories")
            return repos
            
        except Exception as e:
            self.logger.error(f"GitHub discovery failed: {e}")
            return []
    
    async def _discover_gitlab_repositories(self, 
                                          progress_callback: Optional[Callable] = None) -> List[RepositoryInfo]:
        """Discover GitLab repositories."""
        if not Gitlab:
            self.logger.warning("python-gitlab not available, skipping GitLab discovery")
            return []
        
        try:
            # Initialize GitLab client
            if self.config.gitlab_token:
                gitlab = Gitlab("https://gitlab.com", private_token=self.config.gitlab_token)
            else:
                self.logger.warning("GitLab token required for repository discovery")
                return []
            
            gitlab.auth()
            user = gitlab.user
            repos = []
            
            self.logger.info(f"Discovering GitLab repositories for user: {user.username}")
            
            # Get user's projects
            projects = gitlab.projects.list(owned=True, all=True)
            
            repo_count = 0
            for project in projects:
                if repo_count >= self.config.max_repos_per_provider:
                    break
                
                try:
                    repo_info = await self._convert_gitlab_project(project)
                    if repo_info:
                        repos.append(repo_info)
                        repo_count += 1
                        
                        if progress_callback:
                            progress_callback(f"GitLab: Found {project.path_with_namespace}", repo_count)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process GitLab project {project.path_with_namespace}: {e}")
                    continue
            
            self.logger.info(f"GitLab discovery completed: {len(repos)} repositories")
            return repos
            
        except Exception as e:
            self.logger.error(f"GitLab discovery failed: {e}")
            return []
    
    async def _convert_github_repo(self, repo) -> Optional[RepositoryInfo]:
        """Convert GitHub repository to RepositoryInfo."""
        try:
            # Check if repository has a README
            has_readme = False
            try:
                repo.get_readme()
                has_readme = True
            except:
                pass
            
            return RepositoryInfo(
                name=repo.name,
                full_name=repo.full_name,
                url=repo.html_url,
                clone_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                description=repo.description or "",
                language=repo.language or "Unknown",
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                is_private=repo.private,
                is_fork=repo.fork,
                provider="github",
                owner=repo.owner.login,
                created_at=repo.created_at.isoformat() if repo.created_at else "",
                updated_at=repo.updated_at.isoformat() if repo.updated_at else "",
                size_kb=repo.size,
                default_branch=repo.default_branch,
                topics=repo.get_topics() if hasattr(repo, 'get_topics') else [],
                has_readme=has_readme,
                license=repo.license.name if hasattr(repo, 'license') and repo.license else None
            )
        except Exception as e:
            self.logger.warning(f"Failed to convert GitHub repo {repo.full_name}: {e}")
            return None
    
    async def _convert_gitlab_project(self, project) -> Optional[RepositoryInfo]:
        """Convert GitLab project to RepositoryInfo."""
        try:
            # Check if project has a README
            has_readme = False
            try:
                project.files.get('README.md', ref=project.default_branch)
                has_readme = True
            except:
                try:
                    project.files.get('readme.md', ref=project.default_branch)
                    has_readme = True
                except:
                    pass
            
            return RepositoryInfo(
                name=project.name,
                full_name=project.path_with_namespace,
                url=project.web_url,
                clone_url=project.http_url_to_repo,
                ssh_url=project.ssh_url_to_repo,
                description=project.description or "",
                language="Unknown",  # GitLab doesn't provide primary language easily
                stars=project.star_count,
                forks=project.forks_count,
                is_private=project.visibility == 'private',
                is_fork=project.forked_from_project is not None,
                provider="gitlab",
                owner=project.namespace['path'],
                created_at=project.created_at,
                updated_at=project.last_activity_at,
                size_kb=0,  # GitLab doesn't provide size easily
                default_branch=project.default_branch,
                topics=project.tag_list or [],
                has_readme=has_readme,
                license=None  # Would need additional API call
            )
        except Exception as e:
            self.logger.warning(f"Failed to convert GitLab project {project.path_with_namespace}: {e}")
            return None
    
    def _filter_and_deduplicate(self, repos: List[RepositoryInfo]) -> List[RepositoryInfo]:
        """Apply filters and remove duplicates."""
        filtered_repos = []
        seen_urls = set()
        
        for repo in repos:
            # Skip duplicates (same clone URL)
            if repo.clone_url in seen_urls:
                continue
            seen_urls.add(repo.clone_url)
            
            # Apply filters
            if not self.config.include_private and repo.is_private:
                continue
            
            if not self.config.include_forks and repo.is_fork:
                continue
            
            if repo.stars < self.config.min_stars:
                continue
            
            if self.config.languages and repo.language not in self.config.languages:
                continue
            
            if self.config.exclude_patterns:
                skip = False
                for pattern in self.config.exclude_patterns:
                    if pattern.lower() in repo.name.lower():
                        skip = True
                        break
                if skip:
                    continue
            
            filtered_repos.append(repo)
        
        return filtered_repos
    
    def _update_statistics(self, repos: List[RepositoryInfo]):
        """Update discovery statistics."""
        self.stats['total_discovered'] = len(repos)
        self.stats['private_repos'] = sum(1 for r in repos if r.is_private)
        self.stats['public_repos'] = sum(1 for r in repos if not r.is_private)
        self.stats['forks'] = sum(1 for r in repos if r.is_fork)
        
        # Provider stats
        for repo in repos:
            self.stats['providers'][repo.provider] = self.stats['providers'].get(repo.provider, 0) + 1
            if repo.provider == 'github':
                self.stats['github_repos'] += 1
            elif repo.provider == 'gitlab':
                self.stats['gitlab_repos'] += 1
        
        # Language stats
        for repo in repos:
            lang = repo.language or 'Unknown'
            self.stats['languages'][lang] = self.stats['languages'].get(lang, 0) + 1
    
    def _can_use_github(self) -> bool:
        """Check if GitHub can be used."""
        return Github is not None
    
    def _can_use_gitlab(self) -> bool:
        """Check if GitLab can be used."""
        return Gitlab is not None and self.config.gitlab_token is not None
    
    def get_statistics(self) -> Dict:
        """Get discovery statistics."""
        return self.stats.copy()
    
    def save_discovered_repos(self, file_path: str):
        """Save discovered repositories to JSON file."""
        try:
            data = {
                'discovery_date': datetime.now().isoformat(),
                'config': asdict(self.config),
                'statistics': self.stats,
                'repositories': [asdict(repo) for repo in self.discovered_repos]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Discovered repositories saved to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save discovered repositories: {e}")
    
    def load_discovered_repos(self, file_path: str) -> bool:
        """Load discovered repositories from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.stats = data.get('statistics', {})
            repo_data = data.get('repositories', [])
            self.discovered_repos = [RepositoryInfo(**repo) for repo in repo_data]
            
            self.logger.info(f"Loaded {len(self.discovered_repos)} repositories from: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load discovered repositories: {e}")
            return False


class BulkRepositoryCloner:
    """Handles bulk cloning of discovered repositories."""
    
    def __init__(self, ssh_key_path: Optional[str] = None):
        """Initialize the bulk cloner."""
        self.ssh_key_path = ssh_key_path
        self.logger = get_logger()
        self.temp_dirs = []
    
    async def clone_repository(self, repo: RepositoryInfo, 
                             temp_dir: Optional[str] = None) -> Optional[str]:
        """Clone a single repository."""
        try:
            if temp_dir is None:
                temp_dir = tempfile.mkdtemp(prefix=f"reporeadme_{repo.name}_")
                self.temp_dirs.append(temp_dir)
            
            clone_path = os.path.join(temp_dir, repo.name)
            
            # Prepare git command
            if self.ssh_key_path and repo.ssh_url:
                # Use SSH with specific key
                env = os.environ.copy()
                env['GIT_SSH_COMMAND'] = f'ssh -i {self.ssh_key_path} -o IdentitiesOnly=yes'
                clone_url = repo.ssh_url
            else:
                # Use HTTPS
                env = os.environ.copy()
                clone_url = repo.clone_url
            
            # Clone repository
            result = subprocess.run([
                'git', 'clone', '--depth', '1', clone_url, clone_path
            ], env=env, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully cloned {repo.full_name}")
                return clone_path
            else:
                self.logger.warning(f"Failed to clone {repo.full_name}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Timeout cloning {repo.full_name}")
            return None
        except Exception as e:
            self.logger.error(f"Error cloning {repo.full_name}: {e}")
            return None
    
    def cleanup_temp_dirs(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                self.logger.debug(f"Cleaned up temp dir: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_temp_dirs()


# Utility functions
async def discover_user_repositories(github_token: Optional[str] = None,
                                   gitlab_token: Optional[str] = None,
                                   ssh_key_path: Optional[str] = None,
                                   progress_callback: Optional[Callable] = None) -> List[RepositoryInfo]:
    """Quick function to discover all user repositories."""
    config = DiscoveryConfig(
        github_token=github_token,
        gitlab_token=gitlab_token,
        ssh_key_path=ssh_key_path,
        include_forks=False,  # Skip forks by default
        include_archived=False  # Skip archived by default
    )
    
    discovery = RepositoryDiscovery(config)
    return await discovery.discover_all_repositories(progress_callback)


def get_ssh_key_path() -> Optional[str]:
    """Get the SSH key path for repository access."""
    # Check for RepoReadme specific key first
    ssh_dir = Path.home() / '.ssh'
    
    potential_keys = [
        ssh_dir / 'reporeadme_github',
        ssh_dir / 'id_ed25519',
        ssh_dir / 'id_rsa'
    ]
    
    for key_path in potential_keys:
        if key_path.exists():
            return str(key_path)
    
    return None