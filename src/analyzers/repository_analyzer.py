#!/usr/bin/env python3
"""
RepoReadme - Repository Analysis Engine

Analyzes repository structure, detects technologies, and extracts metadata
for automated README generation. Reuses GitGuard's proven scanning architecture.

Features:
- Technology stack detection
- Project structure analysis  
- Dependency parsing
- License and documentation detection
- Code metrics and statistics
- Development workflow analysis
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import subprocess
import time

try:
    from ..utils.logger import get_logger
    from github import Github
except ImportError:
    from utils.logger import get_logger
    try:
        from github import Github
    except ImportError:
        Github = None


@dataclass
class ProjectMetadata:
    """Container for project metadata and analysis results."""
    
    # Basic information
    name: str = ""
    description: str = ""
    version: str = ""
    license: str = ""
    author: str = ""
    homepage: str = ""
    repository_url: str = ""
    
    # Technology stack
    primary_language: str = ""
    languages: Dict[str, float] = field(default_factory=dict)  # language -> percentage
    frameworks: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    
    # Project structure
    project_type: str = ""  # web-app, library, cli-tool, etc.
    structure: Dict[str, Any] = field(default_factory=dict)
    has_tests: bool = False
    has_docs: bool = False
    has_ci: bool = False
    has_docker: bool = False
    
    # Dependencies
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # package_manager -> [deps]
    dev_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    # Code metrics
    total_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Git information
    commits: int = 0
    contributors: int = 0
    created_date: Optional[str] = None
    last_updated: Optional[str] = None
    
    # Features and capabilities
    features: List[str] = field(default_factory=list)
    installation_commands: List[str] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)
    api_endpoints: List[Dict] = field(default_factory=list)
    
    # Documentation
    existing_readme: str = ""
    changelog: str = ""
    contributing_guide: str = ""
    
    # Quality indicators
    has_badges: bool = False
    has_screenshots: bool = False
    has_examples: bool = False
    code_quality_score: float = 0.0


class RepositoryAnalyzer:
    """
    Advanced repository analyzer for README generation.
    
    Analyzes repository structure, detects technologies, and extracts
    comprehensive metadata for generating professional README files.
    """
    
    def __init__(self, github_client: Optional[Github] = None):
        """Initialize the analyzer."""
        self.github_client = github_client
        self.logger = get_logger()
        
        # Technology detection patterns
        self.tech_patterns = {
            # Web frameworks
            'react': [r'react', r'@types/react', r'create-react-app'],
            'vue': [r'vue', r'@vue/', r'vue-cli'],
            'angular': [r'@angular/', r'angular-cli', r'ng\s'],
            'express': [r'express', r'expressjs'],
            'fastapi': [r'fastapi', r'uvicorn'],
            'django': [r'django', r'Django'],
            'flask': [r'flask', r'Flask'],
            'spring': [r'spring-boot', r'@SpringBootApplication'],
            'rails': [r'rails', r'Ruby on Rails'],
            
            # Databases
            'mongodb': [r'mongodb', r'mongoose', r'pymongo'],
            'postgresql': [r'postgresql', r'psycopg2', r'pg'],
            'mysql': [r'mysql', r'pymysql', r'mysql2'],
            'sqlite': [r'sqlite', r'sqlite3'],
            'redis': [r'redis', r'ioredis'],
            
            # Cloud & DevOps
            'docker': [r'dockerfile', r'docker-compose', r'.dockerignore'],
            'kubernetes': [r'kubernetes', r'kubectl', r'k8s'],
            'aws': [r'aws-sdk', r'boto3', r'@aws-sdk'],
            'terraform': [r'terraform', r'\.tf$'],
            
            # Testing
            'jest': [r'jest', r'@jest/'],
            'pytest': [r'pytest', r'test_.*\.py'],
            'mocha': [r'mocha', r'chai'],
            'junit': [r'junit', r'@Test'],
            
            # Build tools
            'webpack': [r'webpack', r'webpack.config'],
            'vite': [r'vite', r'vite.config'],
            'gradle': [r'gradle', r'build.gradle'],
            'maven': [r'maven', r'pom.xml'],
        }
        
        # File type patterns
        self.language_extensions = {
            'python': ['.py', '.pyx', '.pyi'],
            'javascript': ['.js', '.jsx', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'c++': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'c': ['.c', '.h'],
            'c#': ['.cs'],
            'kotlin': ['.kt'],
            'swift': ['.swift'],
            'dart': ['.dart'],
            'scala': ['.scala'],
            'r': ['.r', '.R'],
            'shell': ['.sh', '.bash', '.zsh'],
        }
        
        # Project type indicators
        self.project_type_patterns = {
            'web-app': ['package.json', 'requirements.txt', 'index.html', 'app.py', 'server.js'],
            'mobile-app': ['android/', 'ios/', 'pubspec.yaml', 'Package.swift'],
            'library': ['setup.py', '__init__.py', 'lib/', 'src/', 'package.json'],
            'cli-tool': ['bin/', 'cli.py', 'main.go', 'cmd/'],
            'data-science': ['jupyter/', '*.ipynb', 'data/', 'notebooks/'],
            'game': ['unity/', 'unreal/', 'godot/', 'assets/'],
            'api': ['api/', 'routes/', 'controllers/', 'endpoints/'],
            'desktop-app': ['electron/', 'tauri/', 'gui.py', 'main.cpp'],
        }
    
    def analyze_repository(self, repo_path: str, repo_name: str = None, github_url: str = None) -> ProjectMetadata:
        """
        Perform comprehensive repository analysis.
        
        Args:
            repo_path: Path to local repository
            repo_name: Repository name (optional)
            github_url: GitHub repository URL (optional)
            
        Returns:
            ProjectMetadata with complete analysis results
        """
        start_time = time.time()
        
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
        
        self.logger.info(f"Starting repository analysis: {repo_path}", "ANALYSIS")
        
        metadata = ProjectMetadata()
        metadata.name = repo_name or os.path.basename(repo_path)
        metadata.repository_url = github_url or ""
        
        # Perform analysis steps
        self._analyze_basic_info(repo_path, metadata)
        self._analyze_file_structure(repo_path, metadata)
        self._analyze_languages(repo_path, metadata)
        self._analyze_technologies(repo_path, metadata)
        self._analyze_dependencies(repo_path, metadata)
        self._analyze_project_type(repo_path, metadata)
        self._analyze_development_setup(repo_path, metadata)
        self._analyze_documentation(repo_path, metadata)
        self._analyze_git_history(repo_path, metadata)
        self._analyze_code_metrics(repo_path, metadata)
        self._extract_features_and_usage(repo_path, metadata)
        self._calculate_quality_score(metadata)
        
        duration = (time.time() - start_time) * 1000
        self.logger.log_performance("repository_analysis", duration, {
            "repo": metadata.name,
            "files": metadata.total_files,
            "languages": len(metadata.languages)
        })
        
        self.logger.log_repository_analysis(
            metadata.name, "comprehensive", "completed",
            f"{metadata.total_files} files, {len(metadata.languages)} languages"
        )
        
        return metadata
    
    def _analyze_basic_info(self, repo_path: str, metadata: ProjectMetadata):
        """Extract basic repository information."""
        repo_path = Path(repo_path)
        
        # Try to get info from various config files
        config_files = [
            ('package.json', self._parse_package_json),
            ('setup.py', self._parse_setup_py),
            ('Cargo.toml', self._parse_cargo_toml),
            ('pom.xml', self._parse_pom_xml),
            ('build.gradle', self._parse_gradle),
            ('composer.json', self._parse_composer_json),
            ('pubspec.yaml', self._parse_pubspec_yaml),
        ]
        
        for filename, parser in config_files:
            config_file = repo_path / filename
            if config_file.exists():
                try:
                    parser(config_file, metadata)
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to parse {filename}: {e}", "PARSE")
        
        # Check for license
        license_files = ['LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING']
        for license_file in license_files:
            license_path = repo_path / license_file
            if license_path.exists():
                metadata.license = self._detect_license_type(license_path)
                break
    
    def _analyze_file_structure(self, repo_path: str, metadata: ProjectMetadata):
        """Analyze repository file structure."""
        repo_path = Path(repo_path)
        structure = {}
        
        # Common directory patterns
        important_dirs = {
            'src', 'lib', 'app', 'components', 'pages', 'views', 'models',
            'controllers', 'routes', 'api', 'services', 'utils', 'helpers',
            'tests', 'test', 'spec', '__tests__', 'docs', 'documentation',
            'examples', 'demo', 'scripts', 'bin', 'config', 'assets',
            'static', 'public', 'resources', 'data'
        }
        
        for item in repo_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if item.name.lower() in important_dirs:
                    structure[item.name] = self._analyze_directory(item)
        
        metadata.structure = structure
        
        # Check for important indicators
        metadata.has_tests = any(
            test_dir in structure for test_dir in ['tests', 'test', 'spec', '__tests__']
        )
        metadata.has_docs = any(
            doc_dir in structure for doc_dir in ['docs', 'documentation']
        )
        metadata.has_docker = (repo_path / 'Dockerfile').exists() or (repo_path / 'docker-compose.yml').exists()
        
        # CI/CD detection
        ci_indicators = ['.github/workflows', '.gitlab-ci.yml', '.travis.yml', 'Jenkinsfile', '.circleci']
        metadata.has_ci = any((repo_path / indicator).exists() for indicator in ci_indicators)
    
    def _analyze_languages(self, repo_path: str, metadata: ProjectMetadata):
        """Detect and analyze programming languages used."""
        repo_path = Path(repo_path)
        language_counts = defaultdict(int)
        total_files = 0
        
        # Scan all source files
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                extension = file_path.suffix.lower()
                
                # Map extension to language
                for language, extensions in self.language_extensions.items():
                    if extension in extensions:
                        try:
                            line_count = len(file_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                            language_counts[language] += line_count
                            total_files += 1
                        except Exception:
                            continue
                        break
        
        # Calculate percentages
        total_lines = sum(language_counts.values())
        if total_lines > 0:
            metadata.languages = {
                lang: (count / total_lines) * 100 
                for lang, count in language_counts.items()
            }
            # Primary language is the most used one
            metadata.primary_language = max(metadata.languages.items(), key=lambda x: x[1])[0]
    
    def _analyze_technologies(self, repo_path: str, metadata: ProjectMetadata):
        """Detect technologies, frameworks, and tools used."""
        repo_path = Path(repo_path)
        detected_tech = set()
        
        # Scan files for technology patterns
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
                    filename = file_path.name.lower()
                    
                    # Check each technology pattern
                    for tech, patterns in self.tech_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, content) or re.search(pattern, filename):
                                detected_tech.add(tech)
                                break
                
                except Exception:
                    continue
        
        # Categorize detected technologies
        web_frameworks = {'react', 'vue', 'angular', 'express', 'fastapi', 'django', 'flask', 'spring', 'rails'}
        databases = {'mongodb', 'postgresql', 'mysql', 'sqlite', 'redis'}
        devops_tools = {'docker', 'kubernetes', 'aws', 'terraform'}
        
        metadata.frameworks = [tech for tech in detected_tech if tech in web_frameworks]
        metadata.databases = [tech for tech in detected_tech if tech in databases]
        metadata.tools = [tech for tech in detected_tech if tech in devops_tools]
    
    def _analyze_dependencies(self, repo_path: str, metadata: ProjectMetadata):
        """Parse and analyze project dependencies."""
        repo_path = Path(repo_path)
        
        # Package.json (Node.js)
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                metadata.dependencies['npm'] = list(data.get('dependencies', {}).keys())
                metadata.dev_dependencies['npm'] = list(data.get('devDependencies', {}).keys())
            except Exception as e:
                self.logger.debug(f"Failed to parse package.json: {e}", "DEPS")
        
        # Requirements.txt (Python)
        requirements = repo_path / 'requirements.txt'
        if requirements.exists():
            try:
                deps = []
                for line in requirements.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps.append(line.split('==')[0].split('>=')[0].split('<=')[0])
                metadata.dependencies['pip'] = deps
            except Exception as e:
                self.logger.debug(f"Failed to parse requirements.txt: {e}", "DEPS")
        
        # Add other dependency file parsers as needed
        # Cargo.toml, pom.xml, build.gradle, etc.
    
    def _analyze_project_type(self, repo_path: str, metadata: ProjectMetadata):
        """Determine the type of project."""
        repo_path = Path(repo_path)
        type_scores = defaultdict(int)
        
        # Check for type indicators
        for project_type, indicators in self.project_type_patterns.items():
            for indicator in indicators:
                if '*' in indicator:
                    # Glob pattern
                    if list(repo_path.glob(indicator)):
                        type_scores[project_type] += 1
                else:
                    # Direct path check
                    if (repo_path / indicator).exists():
                        type_scores[project_type] += 1
        
        # Determine primary project type
        if type_scores:
            metadata.project_type = max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            metadata.project_type = "general"
    
    def _analyze_development_setup(self, repo_path: str, metadata: ProjectMetadata):
        """Analyze development setup and installation requirements."""
        repo_path = Path(repo_path)
        
        # Generate installation commands based on detected technologies
        install_commands = []
        
        if (repo_path / 'package.json').exists():
            install_commands.extend(['npm install', 'npm start'])
        
        if (repo_path / 'requirements.txt').exists():
            install_commands.extend(['pip install -r requirements.txt', 'python main.py'])
        
        if (repo_path / 'Cargo.toml').exists():
            install_commands.extend(['cargo build', 'cargo run'])
        
        if (repo_path / 'pom.xml').exists():
            install_commands.extend(['mvn install', 'mvn spring-boot:run'])
        
        if (repo_path / 'build.gradle').exists():
            install_commands.extend(['./gradlew build', './gradlew run'])
        
        metadata.installation_commands = install_commands
    
    def _analyze_documentation(self, repo_path: str, metadata: ProjectMetadata):
        """Analyze existing documentation."""
        repo_path = Path(repo_path)
        
        # Check for existing README
        readme_files = ['README.md', 'README.txt', 'README.rst', 'readme.md']
        for readme_file in readme_files:
            readme_path = repo_path / readme_file
            if readme_path.exists():
                try:
                    metadata.existing_readme = readme_path.read_text(encoding='utf-8')[:5000]  # First 5KB
                    break
                except Exception:
                    pass
        
        # Check for other documentation
        if (repo_path / 'CHANGELOG.md').exists():
            try:
                metadata.changelog = (repo_path / 'CHANGELOG.md').read_text(encoding='utf-8')[:2000]
            except Exception:
                pass
        
        if (repo_path / 'CONTRIBUTING.md').exists():
            try:
                metadata.contributing_guide = (repo_path / 'CONTRIBUTING.md').read_text(encoding='utf-8')[:2000]
            except Exception:
                pass
    
    def _analyze_git_history(self, repo_path: str, metadata: ProjectMetadata):
        """Analyze git history for repository statistics."""
        try:
            # Get commit count
            result = subprocess.run(
                ['git', 'rev-list', '--all', '--count'],
                cwd=repo_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                metadata.commits = int(result.stdout.strip())
            
            # Get contributor count
            result = subprocess.run(
                ['git', 'shortlog', '-sn'],
                cwd=repo_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                metadata.contributors = len(result.stdout.strip().splitlines())
            
            # Get creation and last update dates
            result = subprocess.run(
                ['git', 'log', '--format=%ai', '--reverse'],
                cwd=repo_path, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                dates = result.stdout.strip().splitlines()
                if dates:
                    metadata.created_date = dates[0][:10]  # YYYY-MM-DD
                    metadata.last_updated = dates[-1][:10]
        
        except Exception as e:
            self.logger.debug(f"Git analysis failed: {e}", "GIT")
    
    def _analyze_code_metrics(self, repo_path: str, metadata: ProjectMetadata):
        """Calculate code metrics and statistics."""
        repo_path = Path(repo_path)
        
        total_files = 0
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.splitlines()
                    
                    total_files += 1
                    total_lines += len(lines)
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            blank_lines += 1
                        elif line.startswith('#') or line.startswith('//') or line.startswith('/*'):
                            comment_lines += 1
                        else:
                            code_lines += 1
                
                except Exception:
                    continue
        
        metadata.total_files = total_files
        metadata.total_lines = total_lines
        metadata.code_lines = code_lines
        metadata.comment_lines = comment_lines
        metadata.blank_lines = blank_lines
    
    def _extract_features_and_usage(self, repo_path: str, metadata: ProjectMetadata):
        """Extract features and usage examples from code and docs."""
        # This is a simplified implementation
        # In a full version, this would use more sophisticated parsing
        
        features = []
        usage_examples = []
        
        # Look for feature indicators in file names and structure
        if 'api' in metadata.structure:
            features.append("REST API")
        if 'auth' in str(metadata.structure).lower():
            features.append("Authentication")
        if 'database' in str(metadata.dependencies).lower():
            features.append("Database Integration")
        if metadata.has_tests:
            features.append("Automated Testing")
        if metadata.has_docker:
            features.append("Docker Support")
        
        # Extract usage examples from README if it exists
        if metadata.existing_readme:
            # Look for code blocks
            code_blocks = re.findall(r'```.*?\n(.*?)```', metadata.existing_readme, re.DOTALL)
            usage_examples = code_blocks[:3]  # First 3 code blocks
        
        metadata.features = features
        metadata.usage_examples = usage_examples
    
    def _calculate_quality_score(self, metadata: ProjectMetadata):
        """Calculate a code quality score based on various indicators."""
        score = 0.0
        
        # Documentation (30%)
        if metadata.existing_readme:
            score += 15
        if metadata.changelog:
            score += 5
        if metadata.contributing_guide:
            score += 5
        if metadata.has_docs:
            score += 5
        
        # Testing (25%)
        if metadata.has_tests:
            score += 25
        
        # CI/CD (15%)
        if metadata.has_ci:
            score += 15
        
        # Code organization (20%)
        if len(metadata.structure) >= 3:
            score += 10
        if metadata.license:
            score += 5
        if len(metadata.dependencies) > 0:
            score += 5
        
        # Activity (10%)
        if metadata.commits > 10:
            score += 5
        if metadata.contributors > 1:
            score += 5
        
        metadata.code_quality_score = min(score, 100.0)
    
    # Helper methods
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored during analysis."""
        ignore_patterns = [
            '.git', '__pycache__', 'node_modules', '.env', 'venv',
            'build', 'dist', '.cache', 'coverage', '.nyc_output',
            '.pytest_cache', '.mypy_cache', '.tox'
        ]
        
        path_str = str(file_path).lower()
        return any(pattern in path_str for pattern in ignore_patterns)
    
    def _analyze_directory(self, dir_path: Path) -> Dict[str, int]:
        """Analyze a directory and return statistics."""
        file_count = 0
        subdir_count = 0
        
        try:
            for item in dir_path.iterdir():
                if item.is_file():
                    file_count += 1
                elif item.is_dir() and not item.name.startswith('.'):
                    subdir_count += 1
        except PermissionError:
            pass
        
        return {"files": file_count, "subdirs": subdir_count}
    
    def _parse_package_json(self, file_path: Path, metadata: ProjectMetadata):
        """Parse package.json for Node.js projects."""
        data = json.loads(file_path.read_text())
        metadata.description = data.get('description', '')
        metadata.version = data.get('version', '')
        metadata.author = data.get('author', '')
        metadata.homepage = data.get('homepage', '')
        metadata.license = data.get('license', '')
    
    def _parse_setup_py(self, file_path: Path, metadata: ProjectMetadata):
        """Parse setup.py for Python projects."""
        # Simplified parsing - in production, use AST parsing
        content = file_path.read_text()
        
        # Extract common fields using regex
        patterns = {
            'name': r'name\s*=\s*["\']([^"\']+)["\']',
            'version': r'version\s*=\s*["\']([^"\']+)["\']',
            'description': r'description\s*=\s*["\']([^"\']+)["\']',
            'author': r'author\s*=\s*["\']([^"\']+)["\']',
            'license': r'license\s*=\s*["\']([^"\']+)["\']',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                setattr(metadata, field, match.group(1))
    
    def _parse_cargo_toml(self, file_path: Path, metadata: ProjectMetadata):
        """Parse Cargo.toml for Rust projects."""
        try:
            import toml
            data = toml.loads(file_path.read_text())
            package = data.get('package', {})
            metadata.name = package.get('name', '')
            metadata.version = package.get('version', '')
            metadata.description = package.get('description', '')
            metadata.license = package.get('license', '')
        except ImportError:
            self.logger.debug("toml library not available for Cargo.toml parsing", "PARSE")
        except Exception as e:
            self.logger.debug(f"Failed to parse Cargo.toml: {e}", "PARSE")
    
    def _parse_pom_xml(self, file_path: Path, metadata: ProjectMetadata):
        """Parse pom.xml for Maven projects."""
        # Simplified XML parsing
        content = file_path.read_text()
        
        patterns = {
            'name': r'<artifactId>([^<]+)</artifactId>',
            'version': r'<version>([^<]+)</version>',
            'description': r'<description>([^<]+)</description>',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                setattr(metadata, field, match.group(1))
    
    def _parse_gradle(self, file_path: Path, metadata: ProjectMetadata):
        """Parse build.gradle for Gradle projects."""
        # Simplified Gradle parsing
        pass
    
    def _parse_composer_json(self, file_path: Path, metadata: ProjectMetadata):
        """Parse composer.json for PHP projects."""
        data = json.loads(file_path.read_text())
        metadata.name = data.get('name', '')
        metadata.description = data.get('description', '')
        metadata.version = data.get('version', '')
        metadata.license = data.get('license', '')
    
    def _parse_pubspec_yaml(self, file_path: Path, metadata: ProjectMetadata):
        """Parse pubspec.yaml for Dart/Flutter projects."""
        try:
            import yaml
            data = yaml.safe_load(file_path.read_text())
            metadata.name = data.get('name', '')
            metadata.version = data.get('version', '')
            metadata.description = data.get('description', '')
        except ImportError:
            self.logger.debug("yaml library not available for pubspec.yaml parsing", "PARSE")
        except Exception as e:
            self.logger.debug(f"Failed to parse pubspec.yaml: {e}", "PARSE")
    
    def _detect_license_type(self, license_path: Path) -> str:
        """Detect license type from license file."""
        try:
            content = license_path.read_text().lower()
            
            if 'mit license' in content:
                return 'MIT'
            elif 'apache license' in content:
                return 'Apache 2.0'
            elif 'gnu general public license' in content:
                return 'GPL'
            elif 'bsd license' in content:
                return 'BSD'
            elif 'mozilla public license' in content:
                return 'MPL'
            else:
                return 'Custom'
        except Exception:
            return 'Unknown'