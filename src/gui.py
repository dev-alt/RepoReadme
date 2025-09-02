#!/usr/bin/env python3
"""
RepoReadme - Main GUI Application

Professional GUI for automatic README generation, built on GitGuard's
proven architecture with modern enhancements for repository analysis
and documentation creation.

Features:
- Repository selection (local folders and GitHub repos)
- Template customization and preview
- Batch processing capabilities
- Real-time README generation
- Multiple export formats
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    from .analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata
    from .templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
    from .utils.logger import get_logger
    from .config.settings import SettingsManager
    from github import Github
except ImportError:
    from analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata  
    from templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
    from utils.logger import get_logger
    from config.settings import SettingsManager
    try:
        from github import Github
    except ImportError:
        Github = None


class RepositoryItem:
    """Container for repository information in the GUI."""
    
    def __init__(self, name: str, path: str = "", url: str = "", repo_type: str = "local"):
        self.name = name
        self.path = path
        self.url = url
        self.repo_type = repo_type  # local, github
        self.metadata: Optional[ProjectMetadata] = None
        self.generated_readme: str = ""
        self.status = "pending"  # pending, analyzing, completed, error


class RepoReadmeGUI:
    """
    Main GUI application for RepoReadme.
    
    Provides an intuitive interface for repository analysis, template
    customization, and README generation with real-time preview.
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("RepoReadme - Automatic README Generator v1.0.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Initialize components
        self.logger = get_logger()
        self.analyzer = RepositoryAnalyzer()
        self.template_engine = ReadmeTemplateEngine()
        self.settings_manager = SettingsManager()
        
        # Data
        self.repositories: List[RepositoryItem] = []
        self.selected_repo: Optional[RepositoryItem] = None
        self.github_client: Optional[Github] = None
        
        # Initialize GitHub client (optional)
        self.initialize_github_client()
        
        # GUI state
        self.analysis_thread: Optional[threading.Thread] = None
        self.is_analyzing = False
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        
        # Load settings
        self.load_settings()
        
        self.logger.info("RepoReadme GUI initialized", "GUI")
    
    def initialize_github_client(self):
        """Initialize GitHub client if available."""
        try:
            if Github is not None:
                # Try to initialize without token first (public repos only)
                self.github_client = Github()
                self.logger.info("GitHub client initialized (public access only)", "GUI")
            else:
                self.logger.warning("PyGithub not available - GitHub features disabled", "GUI")
        except Exception as e:
            self.logger.warning(f"Failed to initialize GitHub client: {e}", "GUI")
            self.github_client = None
    
    def setup_styles(self):
        """Configure GUI styles and themes."""
        style = ttk.Style()
        
        # Configure modern flat design
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#2c3e50')
        style.configure('Subheader.TLabel', font=('Segoe UI', 10, 'bold'), foreground='#34495e')
        style.configure('Action.TButton', font=('Segoe UI', 9))
        style.configure('Primary.TButton', font=('Segoe UI', 9, 'bold'))
        
        # Treeview styling
        style.configure('Treeview', rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))
    
    def create_widgets(self):
        """Create and configure all GUI widgets."""
        
        # Main container with paned window for resizable layout
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        
        # Left panel - Repository management
        self.left_frame = ttk.Frame(self.main_paned, width=400)
        self.create_repository_panel()
        
        # Right panel - Configuration and preview
        self.right_frame = ttk.Frame(self.main_paned, width=800)
        self.create_configuration_panel()
        
        self.main_paned.add(self.left_frame, weight=1)
        self.main_paned.add(self.right_frame, weight=2)
    
    def create_repository_panel(self):
        """Create the repository management panel."""
        
        # Header
        header_frame = ttk.Frame(self.left_frame)
        ttk.Label(header_frame, text="📁 Repository Manager", 
                 style='Header.TLabel').pack(side='left')
        
        # Repository list with actions
        list_frame = ttk.LabelFrame(self.left_frame, text="Repositories", padding=10)
        
        # Action buttons
        button_frame = ttk.Frame(list_frame)
        ttk.Button(button_frame, text="➕ Add Local Folder", 
                  command=self.add_local_repository, style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="🐙 Add GitHub Repo", 
                  command=self.add_github_repository, style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="🗑️ Remove", 
                  command=self.remove_repository, style='Action.TButton').pack(side='left', padx=5)
        
        # Repository list
        self.repo_tree = ttk.Treeview(list_frame, columns=('type', 'status'), show='tree headings', height=12)
        self.repo_tree.heading('#0', text='Repository', anchor='w')
        self.repo_tree.heading('type', text='Type', anchor='center')
        self.repo_tree.heading('status', text='Status', anchor='center')
        
        self.repo_tree.column('#0', width=200)
        self.repo_tree.column('type', width=80)
        self.repo_tree.column('status', width=100)
        
        # Scrollbar for repository list
        repo_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.repo_tree.yview)
        self.repo_tree.configure(yscrollcommand=repo_scrollbar.set)
        
        self.repo_tree.bind('<<TreeviewSelect>>', self.on_repository_select)
        
        # Repository info panel
        info_frame = ttk.LabelFrame(self.left_frame, text="Repository Information", padding=10)
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8, width=45, 
                                                  font=('Consolas', 9), state='disabled')
        
        # Batch operations
        batch_frame = ttk.LabelFrame(self.left_frame, text="Batch Operations", padding=10)
        ttk.Button(batch_frame, text="🔍 Analyze All", 
                  command=self.analyze_all_repositories, style='Primary.TButton').pack(fill='x', pady=2)
        ttk.Button(batch_frame, text="📝 Generate All READMEs", 
                  command=self.generate_all_readmes, style='Primary.TButton').pack(fill='x', pady=2)
        ttk.Button(batch_frame, text="💾 Export All", 
                  command=self.export_all_readmes, style='Action.TButton').pack(fill='x', pady=2)
        
        # Layout repository panel
        header_frame.pack(fill='x', pady=(0, 10))
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        button_frame.pack(fill='x', pady=(0, 10))
        self.repo_tree.pack(side='left', fill='both', expand=True)
        repo_scrollbar.pack(side='right', fill='y')
        info_frame.pack(fill='both', expand=True, pady=(0, 10))
        self.info_text.pack(fill='both', expand=True)
        batch_frame.pack(fill='x')
    
    def create_configuration_panel(self):
        """Create the configuration and preview panel."""
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.right_frame)
        
        # Template Configuration Tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="⚙️ Configuration")
        self.create_configuration_tab()
        
        # README Preview Tab
        self.preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_frame, text="👁️ Preview")
        self.create_preview_tab()
        
        # Analysis Results Tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="📊 Analysis")
        self.create_analysis_tab()
        
        self.notebook.pack(fill='both', expand=True)
    
    def create_configuration_tab(self):
        """Create the template configuration tab."""
        
        # Scrollable frame for configuration
        canvas = tk.Canvas(self.config_frame)
        scrollbar = ttk.Scrollbar(self.config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Template Selection
        template_frame = ttk.LabelFrame(scrollable_frame, text="README Template", padding=15)
        
        self.template_var = tk.StringVar(value="modern")
        templates = self.template_engine.get_available_templates()
        
        for template in templates:
            description = self.template_engine.get_template_description(template)
            ttk.Radiobutton(template_frame, text=f"{template.title()}: {description}",
                           variable=self.template_var, value=template,
                           command=self.on_template_change).pack(anchor='w', pady=2)
        
        # Template Options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Template Options", padding=15)
        
        self.include_badges_var = tk.BooleanVar(value=True)
        self.include_toc_var = tk.BooleanVar(value=True)
        self.include_screenshots_var = tk.BooleanVar(value=True)
        self.include_api_docs_var = tk.BooleanVar(value=True)
        self.include_contributing_var = tk.BooleanVar(value=True)
        self.include_license_var = tk.BooleanVar(value=True)
        self.include_acknowledgments_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Include badges", 
                       variable=self.include_badges_var, command=self.on_option_change).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Include table of contents", 
                       variable=self.include_toc_var, command=self.on_option_change).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Include screenshots section", 
                       variable=self.include_screenshots_var, command=self.on_option_change).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Include API documentation", 
                       variable=self.include_api_docs_var, command=self.on_option_change).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Include contributing guidelines", 
                       variable=self.include_contributing_var, command=self.on_option_change).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Include license section", 
                       variable=self.include_license_var, command=self.on_option_change).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="Include acknowledgments", 
                       variable=self.include_acknowledgments_var, command=self.on_option_change).pack(anchor='w')
        
        # Style Options
        style_frame = ttk.LabelFrame(scrollable_frame, text="Style Options", padding=15)
        
        ttk.Label(style_frame, text="Emoji Style:").pack(anchor='w')
        self.emoji_var = tk.StringVar(value="unicode")
        emoji_frame = ttk.Frame(style_frame)
        ttk.Radiobutton(emoji_frame, text="Unicode 🚀", variable=self.emoji_var, 
                       value="unicode", command=self.on_option_change).pack(side='left')
        ttk.Radiobutton(emoji_frame, text="GitHub :rocket:", variable=self.emoji_var, 
                       value="github", command=self.on_option_change).pack(side='left')
        ttk.Radiobutton(emoji_frame, text="None", variable=self.emoji_var, 
                       value="none", command=self.on_option_change).pack(side='left')
        emoji_frame.pack(anchor='w', pady=(0, 10))
        
        ttk.Label(style_frame, text="Badge Style:").pack(anchor='w')
        self.badge_style_var = tk.StringVar(value="flat")
        badge_frame = ttk.Frame(style_frame)
        for style in ["flat", "flat-square", "plastic"]:
            ttk.Radiobutton(badge_frame, text=style.title(), variable=self.badge_style_var,
                           value=style, command=self.on_option_change).pack(side='left')
        badge_frame.pack(anchor='w')
        
        # Action Buttons
        action_frame = ttk.Frame(scrollable_frame)
        ttk.Button(action_frame, text="🔍 Analyze Repository", 
                  command=self.analyze_selected_repository, 
                  style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(action_frame, text="📝 Generate README", 
                  command=self.generate_readme_for_selected, 
                  style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(action_frame, text="💾 Save README", 
                  command=self.save_readme, style='Action.TButton').pack(side='left', padx=5)
        
        # Layout configuration tab
        template_frame.pack(fill='x', pady=(0, 10))
        options_frame.pack(fill='x', pady=(0, 10))
        style_frame.pack(fill='x', pady=(0, 10))
        action_frame.pack(fill='x', pady=(10, 0))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_preview_tab(self):
        """Create the README preview tab."""
        
        # Preview controls
        control_frame = ttk.Frame(self.preview_frame)
        ttk.Label(control_frame, text="📄 README Preview", 
                 style='Header.TLabel').pack(side='left')
        
        ttk.Button(control_frame, text="🔄 Refresh", 
                  command=self.refresh_preview, style='Action.TButton').pack(side='right')
        
        # Preview text area
        self.preview_text = scrolledtext.ScrolledText(self.preview_frame, 
                                                     font=('Consolas', 10), 
                                                     wrap=tk.WORD)
        self.preview_text.insert('1.0', "Select a repository and configure template to see preview...")
        
        control_frame.pack(fill='x', pady=(0, 10))
        self.preview_text.pack(fill='both', expand=True)
    
    def create_analysis_tab(self):
        """Create the repository analysis results tab."""
        
        # Analysis header
        analysis_header = ttk.Frame(self.analysis_frame)
        ttk.Label(analysis_header, text="📊 Repository Analysis", 
                 style='Header.TLabel').pack(side='left')
        
        # Progress bar for analysis
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(analysis_header, textvariable=self.progress_var).pack(side='right')
        
        self.analysis_progress = ttk.Progressbar(analysis_header, mode='indeterminate')
        
        # Analysis results area  
        self.analysis_text = scrolledtext.ScrolledText(self.analysis_frame,
                                                      font=('Consolas', 9),
                                                      wrap=tk.WORD)
        self.analysis_text.insert('1.0', "No analysis results available.\\nSelect a repository and click 'Analyze Repository' to begin.")
        
        analysis_header.pack(fill='x', pady=(0, 10))
        self.analysis_text.pack(fill='both', expand=True)
    
    def setup_layout(self):
        """Setup the main window layout."""
        self.main_paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Status bar
        self.status_bar = ttk.Frame(self.root)
        self.status_var = tk.StringVar(value="Ready - Select repositories to get started")
        ttk.Label(self.status_bar, textvariable=self.status_var).pack(side='left')
        self.status_bar.pack(fill='x', side='bottom')
    
    # Repository Management Methods
    
    def add_local_repository(self):
        """Add a local repository folder."""
        folder_path = filedialog.askdirectory(title="Select Repository Folder")
        if folder_path:
            repo_name = os.path.basename(folder_path)
            repo_item = RepositoryItem(repo_name, folder_path, "", "local")
            self.repositories.append(repo_item)
            self.update_repository_list()
            self.logger.info(f"Added local repository: {repo_name}", "GUI")
    
    def add_github_repository(self):
        """Add a GitHub repository."""
        if self.github_client is None:
            messagebox.showerror("GitHub Unavailable", 
                               "GitHub client not available. Please ensure PyGithub is installed.")
            return
            
        dialog = GitHubRepoDialog(self.root, self.github_client)
        if dialog.result:
            repo_name, repo_url = dialog.result
            repo_item = RepositoryItem(repo_name, "", repo_url, "github")
            self.repositories.append(repo_item)
            self.update_repository_list()
            self.logger.info(f"Added GitHub repository: {repo_name}", "GUI")
    
    def remove_repository(self):
        """Remove selected repository."""
        selection = self.repo_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a repository to remove.")
            return
        
        item_id = selection[0]
        repo_name = self.repo_tree.item(item_id)['text']
        
        if messagebox.askyesno("Confirm Removal", f"Remove repository '{repo_name}'?"):
            # Find and remove from list
            self.repositories = [r for r in self.repositories if r.name != repo_name]
            self.update_repository_list()
            self.clear_info_panel()
            self.logger.info(f"Removed repository: {repo_name}", "GUI")
    
    def update_repository_list(self):
        """Update the repository list display."""
        # Clear existing items
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        # Add repositories
        for repo in self.repositories:
            type_icon = "📁" if repo.repo_type == "local" else "🐙"
            status_icon = {
                "pending": "⏳",
                "analyzing": "🔍", 
                "completed": "✅",
                "error": "❌"
            }.get(repo.status, "❓")
            
            self.repo_tree.insert('', 'end', text=f"{type_icon} {repo.name}",
                                values=(repo.repo_type, f"{status_icon} {repo.status}"))
    
    def on_repository_select(self, event):
        """Handle repository selection."""
        selection = self.repo_tree.selection()
        if selection:
            item_id = selection[0]
            repo_name = self.repo_tree.item(item_id)['text'].split(' ', 1)[1]  # Remove emoji
            
            # Find repository object
            self.selected_repo = next((r for r in self.repositories if r.name == repo_name), None)
            
            if self.selected_repo:
                self.update_info_panel()
                self.refresh_preview()
    
    def update_info_panel(self):
        """Update repository information panel."""
        if not self.selected_repo:
            return
        
        info_lines = []
        info_lines.append(f"📁 Repository: {self.selected_repo.name}")
        info_lines.append(f"🔗 Type: {self.selected_repo.repo_type}")
        
        if self.selected_repo.path:
            info_lines.append(f"📂 Path: {self.selected_repo.path}")
        if self.selected_repo.url:
            info_lines.append(f"🌐 URL: {self.selected_repo.url}")
        
        info_lines.append(f"📊 Status: {self.selected_repo.status}")
        
        if self.selected_repo.metadata:
            metadata = self.selected_repo.metadata
            info_lines.append("")
            info_lines.append("--- Analysis Results ---")
            info_lines.append(f"Language: {metadata.primary_language}")
            info_lines.append(f"Project Type: {metadata.project_type}")
            info_lines.append(f"Files: {metadata.total_files:,}")
            info_lines.append(f"Lines of Code: {metadata.code_lines:,}")
            
            if metadata.frameworks:
                info_lines.append(f"Frameworks: {', '.join(metadata.frameworks)}")
            if metadata.license:
                info_lines.append(f"License: {metadata.license}")
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', "\\n".join(info_lines))
        self.info_text.config(state='disabled')
    
    def clear_info_panel(self):
        """Clear the information panel."""
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', "No repository selected")
        self.info_text.config(state='disabled')
        
        self.analysis_text.delete('1.0', tk.END)
        self.analysis_text.insert('1.0', "No analysis results available.")
        
        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', "Select a repository to see preview...")
    
    # Analysis and Generation Methods
    
    def analyze_selected_repository(self):
        """Analyze the currently selected repository."""
        if not self.selected_repo:
            messagebox.showwarning("No Selection", "Please select a repository to analyze.")
            return
        
        if self.is_analyzing:
            messagebox.showinfo("Analysis in Progress", "Please wait for the current analysis to complete.")
            return
        
        self.analysis_thread = threading.Thread(
            target=self._analyze_repository_thread,
            args=(self.selected_repo,),
            daemon=True
        )
        self.analysis_thread.start()
    
    def _analyze_repository_thread(self, repo_item: RepositoryItem):
        """Analyze repository in background thread."""
        self.is_analyzing = True
        
        try:
            # Update UI
            self.root.after(0, lambda: self._update_analysis_ui(repo_item, "analyzing"))
            
            # Perform analysis
            if repo_item.repo_type == "local":
                metadata = self.analyzer.analyze_repository(repo_item.path, repo_item.name)
            else:
                # For GitHub repos, would need to clone or use API
                # Simplified for this example
                metadata = ProjectMetadata()
                metadata.name = repo_item.name
            
            repo_item.metadata = metadata
            repo_item.status = "completed"
            
            # Update UI
            self.root.after(0, lambda: self._update_analysis_ui(repo_item, "completed"))
            
        except Exception as e:
            repo_item.status = "error"
            self.logger.error(f"Repository analysis failed: {e}", "ANALYSIS", e)
            self.root.after(0, lambda: self._update_analysis_ui(repo_item, "error", str(e)))
        
        finally:
            self.is_analyzing = False
    
    def _update_analysis_ui(self, repo_item: RepositoryItem, status: str, error_msg: str = ""):
        """Update analysis UI elements."""
        repo_item.status = status
        
        if status == "analyzing":
            self.progress_var.set("Analyzing repository...")
            self.analysis_progress.pack(side='right', padx=(10, 0))
            self.analysis_progress.start()
            self.status_var.set(f"Analyzing {repo_item.name}...")
        
        elif status == "completed":
            self.progress_var.set("Analysis completed")
            self.analysis_progress.stop()
            self.analysis_progress.pack_forget()
            self.status_var.set(f"Analysis completed for {repo_item.name}")
            
            # Display analysis results
            if repo_item.metadata:
                self.display_analysis_results(repo_item.metadata)
            
            # Refresh UI
            self.update_repository_list()
            self.update_info_panel()
            self.refresh_preview()
        
        elif status == "error":
            self.progress_var.set("Analysis failed")
            self.analysis_progress.stop()
            self.analysis_progress.pack_forget()
            self.status_var.set(f"Analysis failed for {repo_item.name}")
            
            self.analysis_text.delete('1.0', tk.END)
            self.analysis_text.insert('1.0', f"Analysis Error: {error_msg}")
            
            self.update_repository_list()
    
    def display_analysis_results(self, metadata: ProjectMetadata):
        """Display detailed analysis results."""
        results = []
        
        results.append(f"📊 REPOSITORY ANALYSIS RESULTS")
        results.append("=" * 50)
        results.append("")
        
        # Basic Information
        results.append("🏷️  BASIC INFORMATION")
        results.append(f"Name: {metadata.name}")
        results.append(f"Description: {metadata.description or 'Not specified'}")
        results.append(f"Version: {metadata.version or 'Not specified'}")
        results.append(f"License: {metadata.license or 'Not specified'}")
        results.append(f"Author: {metadata.author or 'Not specified'}")
        results.append("")
        
        # Technology Stack
        results.append("💻 TECHNOLOGY STACK")
        results.append(f"Primary Language: {metadata.primary_language or 'Unknown'}")
        results.append(f"Project Type: {metadata.project_type or 'General'}")
        
        if metadata.languages:
            results.append("Languages:")
            for lang, percentage in sorted(metadata.languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                results.append(f"  - {lang}: {percentage:.1f}%")
        
        if metadata.frameworks:
            results.append(f"Frameworks: {', '.join(metadata.frameworks)}")
        if metadata.databases:
            results.append(f"Databases: {', '.join(metadata.databases)}")
        if metadata.tools:
            results.append(f"Tools: {', '.join(metadata.tools)}")
        results.append("")
        
        # Project Structure
        results.append("📁 PROJECT STRUCTURE")
        if metadata.structure:
            for directory, info in metadata.structure.items():
                results.append(f"  {directory}/ - {info.get('files', 0)} files, {info.get('subdirs', 0)} subdirs")
        results.append("")
        
        # Code Metrics
        results.append("📈 CODE METRICS")
        results.append(f"Total Files: {metadata.total_files:,}")
        results.append(f"Total Lines: {metadata.total_lines:,}")
        results.append(f"Code Lines: {metadata.code_lines:,}")
        results.append(f"Comment Lines: {metadata.comment_lines:,}")
        results.append(f"Blank Lines: {metadata.blank_lines:,}")
        results.append("")
        
        # Repository Activity
        results.append("📊 REPOSITORY ACTIVITY")
        results.append(f"Commits: {metadata.commits or 'Unknown'}")
        results.append(f"Contributors: {metadata.contributors or 'Unknown'}")
        results.append(f"Created: {metadata.created_date or 'Unknown'}")
        results.append(f"Last Updated: {metadata.last_updated or 'Unknown'}")
        results.append("")
        
        # Quality Indicators
        results.append("✨ QUALITY INDICATORS")
        results.append(f"Has Tests: {'✅' if metadata.has_tests else '❌'}")
        results.append(f"Has Documentation: {'✅' if metadata.has_docs else '❌'}")
        results.append(f"Has CI/CD: {'✅' if metadata.has_ci else '❌'}")
        results.append(f"Has Docker: {'✅' if metadata.has_docker else '❌'}")
        results.append(f"Code Quality Score: {metadata.code_quality_score:.1f}/100")
        results.append("")
        
        # Features
        if metadata.features:
            results.append("🚀 DETECTED FEATURES")
            for feature in metadata.features:
                results.append(f"  - {feature}")
            results.append("")
        
        # Dependencies
        if metadata.dependencies:
            results.append("📦 DEPENDENCIES")
            for pkg_manager, deps in metadata.dependencies.items():
                results.append(f"{pkg_manager.upper()}: {len(deps)} packages")
                for dep in deps[:10]:  # Show first 10
                    results.append(f"  - {dep}")
                if len(deps) > 10:
                    results.append(f"  ... and {len(deps) - 10} more")
            results.append("")
        
        self.analysis_text.delete('1.0', tk.END)
        self.analysis_text.insert('1.0', "\\n".join(results))
    
    def generate_readme_for_selected(self):
        """Generate README for the selected repository."""
        if not self.selected_repo:
            messagebox.showwarning("No Selection", "Please select a repository.")
            return
        
        if not self.selected_repo.metadata:
            if messagebox.askyesno("No Analysis", "Repository not analyzed. Analyze now?"):
                self.analyze_selected_repository()
                return
            else:
                return
        
        try:
            # Create template configuration
            config = TemplateConfig(
                template_name=self.template_var.get(),
                include_badges=self.include_badges_var.get(),
                include_toc=self.include_toc_var.get(),
                include_screenshots=self.include_screenshots_var.get(),
                include_api_docs=self.include_api_docs_var.get(),
                include_contributing=self.include_contributing_var.get(),
                include_license_section=self.include_license_var.get(),
                include_acknowledgments=self.include_acknowledgments_var.get(),
                emoji_style=self.emoji_var.get(),
                badge_style=self.badge_style_var.get()
            )
            
            # Generate README
            readme_content = self.template_engine.generate_readme(self.selected_repo.metadata, config)
            self.selected_repo.generated_readme = readme_content
            
            # Update preview
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', readme_content)
            
            # Switch to preview tab
            self.notebook.select(1)
            
            self.status_var.set(f"README generated for {self.selected_repo.name}")
            
        except Exception as e:
            self.logger.error(f"README generation failed: {e}", "GENERATION", e)
            messagebox.showerror("Generation Error", f"Failed to generate README: {str(e)}")
    
    def save_readme(self):
        """Save the generated README to file."""
        if not self.selected_repo or not self.selected_repo.generated_readme:
            messagebox.showwarning("No README", "Generate a README first.")
            return
        
        # Default filename
        default_name = f"{self.selected_repo.name}_README.md"
        
        # Get save location
        file_path = filedialog.asksaveasfilename(
            title="Save README As",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfilename=default_name
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.selected_repo.generated_readme)
                
                messagebox.showinfo("Success", f"README saved to {file_path}")
                self.logger.log_readme_generation(
                    self.selected_repo.name, self.template_var.get(), file_path, True
                )
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save README: {str(e)}")
                self.logger.error(f"README save failed: {e}", "SAVE", e)
    
    # Event Handlers
    
    def on_template_change(self):
        """Handle template selection change."""
        if self.selected_repo and self.selected_repo.metadata:
            self.refresh_preview()
    
    def on_option_change(self):
        """Handle option change."""
        if self.selected_repo and self.selected_repo.metadata:
            self.refresh_preview()
    
    def refresh_preview(self):
        """Refresh the README preview."""
        if not self.selected_repo or not self.selected_repo.metadata:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', "Select and analyze a repository to see preview...")
            return
        
        try:
            # Create configuration
            config = TemplateConfig(
                template_name=self.template_var.get(),
                include_badges=self.include_badges_var.get(),
                include_toc=self.include_toc_var.get(),
                include_screenshots=self.include_screenshots_var.get(),
                include_api_docs=self.include_api_docs_var.get(),
                include_contributing=self.include_contributing_var.get(),
                include_license_section=self.include_license_var.get(),
                include_acknowledgments=self.include_acknowledgments_var.get(),
                emoji_style=self.emoji_var.get(),
                badge_style=self.badge_style_var.get()
            )
            
            # Generate preview
            preview_content = self.template_engine.generate_readme(self.selected_repo.metadata, config)
            
            # Update preview
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview_content)
            
        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Preview Error: {str(e)}")
    
    # Batch Operations
    
    def analyze_all_repositories(self):
        """Analyze all repositories."""
        if not self.repositories:
            messagebox.showinfo("No Repositories", "Add some repositories first.")
            return
        
        if messagebox.askyesno("Batch Analysis", f"Analyze all {len(self.repositories)} repositories?"):
            threading.Thread(target=self._batch_analyze_thread, daemon=True).start()
    
    def _batch_analyze_thread(self):
        """Batch analysis in background thread."""
        total = len(self.repositories)
        
        for i, repo in enumerate(self.repositories, 1):
            if repo.status == "completed":
                continue  # Skip already analyzed
            
            self.root.after(0, lambda r=repo, idx=i, tot=total: 
                           self.status_var.set(f"Analyzing {r.name} ({idx}/{tot})..."))
            
            try:
                if repo.repo_type == "local":
                    metadata = self.analyzer.analyze_repository(repo.path, repo.name)
                    repo.metadata = metadata
                    repo.status = "completed"
                else:
                    # GitHub analysis would go here
                    pass
            
            except Exception as e:
                repo.status = "error"
                self.logger.error(f"Batch analysis failed for {repo.name}: {e}", "BATCH")
        
        self.root.after(0, lambda: [
            self.update_repository_list(),
            self.status_var.set(f"Batch analysis completed ({total} repositories)")
        ])
    
    def generate_all_readmes(self):
        """Generate READMEs for all analyzed repositories."""
        analyzed_repos = [r for r in self.repositories if r.metadata]
        
        if not analyzed_repos:
            messagebox.showinfo("No Analyzed Repos", "Analyze repositories first.")
            return
        
        if messagebox.askyesno("Batch Generation", f"Generate READMEs for {len(analyzed_repos)} repositories?"):
            threading.Thread(target=self._batch_generate_thread, daemon=True).start()
    
    def _batch_generate_thread(self):
        """Batch README generation in background thread."""
        analyzed_repos = [r for r in self.repositories if r.metadata]
        
        config = TemplateConfig(
            template_name=self.template_var.get(),
            include_badges=self.include_badges_var.get(),
            include_toc=self.include_toc_var.get(),
            # ... other config options
        )
        
        for i, repo in enumerate(analyzed_repos, 1):
            self.root.after(0, lambda r=repo, idx=i, tot=len(analyzed_repos):
                           self.status_var.set(f"Generating README for {r.name} ({idx}/{tot})..."))
            
            try:
                readme_content = self.template_engine.generate_readme(repo.metadata, config)
                repo.generated_readme = readme_content
            
            except Exception as e:
                self.logger.error(f"Batch generation failed for {repo.name}: {e}", "BATCH")
        
        self.root.after(0, lambda: 
                       self.status_var.set(f"Batch generation completed ({len(analyzed_repos)} READMEs)"))
    
    def export_all_readmes(self):
        """Export all generated READMEs to files."""
        repos_with_readme = [r for r in self.repositories if r.generated_readme]
        
        if not repos_with_readme:
            messagebox.showinfo("No Generated READMEs", "Generate READMEs first.")
            return
        
        # Choose export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        success_count = 0
        for repo in repos_with_readme:
            try:
                file_path = os.path.join(export_dir, f"{repo.name}_README.md")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(repo.generated_readme)
                success_count += 1
            
            except Exception as e:
                self.logger.error(f"Export failed for {repo.name}: {e}", "EXPORT")
        
        messagebox.showinfo("Export Complete", f"Exported {success_count} README files to {export_dir}")
    
    # Settings and Configuration
    
    def load_settings(self):
        """Load application settings using SettingsManager."""
        try:
            settings = self.settings_manager.load_settings()
            
            # Apply template settings to GUI
            self.template_var.set(settings.default_template)
            self.include_badges_var.set(settings.include_badges)
            self.include_toc_var.set(settings.include_toc)
            self.include_screenshots_var.set(settings.include_screenshots)
            self.include_api_docs_var.set(settings.include_api_docs)
            self.include_contributing_var.set(settings.include_contributing)
            self.include_license_var.set(settings.include_license_section)
            self.include_acknowledgments_var.set(settings.include_acknowledgments)
            self.emoji_var.set(settings.emoji_style)
            self.badge_style_var.set(settings.badge_style)
            
            # Apply window settings
            if settings.window_geometry and not settings.window_maximized:
                self.root.geometry(settings.window_geometry)
            
            self.logger.info("Settings loaded successfully", "SETTINGS")
                
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}", "SETTINGS")
    
    def save_settings(self):
        """Save application settings using SettingsManager."""
        try:
            settings = self.settings_manager.load_settings()
            
            # Update template settings from GUI
            settings.default_template = self.template_var.get()
            settings.include_badges = self.include_badges_var.get()
            settings.include_toc = self.include_toc_var.get()
            settings.include_screenshots = self.include_screenshots_var.get()
            settings.include_api_docs = self.include_api_docs_var.get()
            settings.include_contributing = self.include_contributing_var.get()
            settings.include_license_section = self.include_license_var.get()
            settings.include_acknowledgments = self.include_acknowledgments_var.get()
            settings.emoji_style = self.emoji_var.get()
            settings.badge_style = self.badge_style_var.get()
            
            # Update window settings
            settings.window_geometry = self.root.geometry()
            settings.window_maximized = (self.root.state() == 'zoomed')
            
            # Save settings
            self.settings_manager.save_settings(settings)
            self.logger.info("Settings saved successfully", "SETTINGS")
        
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}", "SETTINGS")
    
    def run(self):
        """Start the GUI application."""
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start main loop
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing."""
        self.save_settings()
        self.logger.info("RepoReadme GUI shutting down", "GUI")
        self.root.destroy()


class GitHubRepoDialog:
    """Dialog for adding GitHub repositories."""
    
    def __init__(self, parent, github_client):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add GitHub Repository")
        self.dialog.geometry("500x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        self.dialog.geometry(f"+{x}+{y}")
        
        # URL input
        ttk.Label(self.dialog, text="GitHub Repository URL:").pack(pady=10)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(self.dialog, textvariable=self.url_var, width=60)
        url_entry.pack(pady=5)
        url_entry.focus()
        
        # Example
        ttk.Label(self.dialog, text="Example: https://github.com/username/repository", 
                 foreground='gray').pack()
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        ttk.Button(button_frame, text="Add", command=self.on_add).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='left')
        button_frame.pack(pady=20)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.on_add())
    
    def on_add(self):
        """Handle add button click."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Invalid URL", "Please enter a repository URL.")
            return
        
        # Parse repository name from URL
        try:
            if 'github.com' in url:
                parts = url.rstrip('/').split('/')
                if len(parts) >= 2:
                    repo_name = f"{parts[-2]}/{parts[-1]}"
                else:
                    repo_name = parts[-1]
            else:
                repo_name = url.split('/')[-1]
            
            self.result = (repo_name, url)
            self.dialog.destroy()
        
        except Exception:
            messagebox.showerror("Invalid URL", "Please enter a valid GitHub repository URL.")
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.dialog.destroy()