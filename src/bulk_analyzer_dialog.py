"""
Bulk Repository Analyzer Dialog

GUI for discovering and analyzing all repositories a user has access to.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import asyncio
import json
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from .repository_discovery import (
        RepositoryDiscovery, DiscoveryConfig, RepositoryInfo, 
        BulkRepositoryCloner, get_ssh_key_path
    )
    from .analyzers.repository_analyzer import RepositoryAnalyzer
    from .templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
    from .utils.logger import get_logger
except ImportError:
    from repository_discovery import (
        RepositoryDiscovery, DiscoveryConfig, RepositoryInfo, 
        BulkRepositoryCloner, get_ssh_key_path
    )
    from analyzers.repository_analyzer import RepositoryAnalyzer
    from templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
    from utils.logger import get_logger


class BulkAnalyzerDialog:
    """Dialog for bulk repository discovery and analysis."""
    
    def __init__(self, parent):
        """Initialize the bulk analyzer dialog."""
        self.parent = parent
        self.logger = get_logger()
        
        # Create main dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔍 Bulk Repository Analyzer")
        self.dialog.geometry("1000x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        # State variables
        self.discovered_repos: List[RepositoryInfo] = []
        self.selected_repos: List[RepositoryInfo] = []
        self.completed_repos: Dict[str, Dict] = {}  # Track completed analysis and READMEs
        self.is_discovering = False
        self.is_analyzing = False
        self.discovery_task = None
        self.analysis_task = None
        
        # Initialize components
        self.repository_analyzer = RepositoryAnalyzer()
        self.template_engine = ReadmeTemplateEngine()
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Discovery Configuration
        self.create_discovery_tab()
        
        # Tab 2: Repository Selection
        self.create_selection_tab()
        
        # Tab 3: Bulk Analysis
        self.create_analysis_tab()
        
        # Tab 4: Results & Export
        self.create_results_tab()
        
        # Bottom buttons
        self.create_bottom_buttons()
    
    def create_discovery_tab(self):
        """Create the repository discovery configuration tab."""
        discovery_frame = ttk.Frame(self.notebook)
        self.notebook.add(discovery_frame, text="🔍 Discovery")
        
        # Main container with scrollbar
        canvas = tk.Canvas(discovery_frame)
        scrollbar = ttk.Scrollbar(discovery_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Authentication Settings
        auth_frame = ttk.LabelFrame(scrollable_frame, text="🔑 Authentication", padding=15)
        auth_frame.pack(fill='x', padx=10, pady=10)
        
        # GitHub Token
        ttk.Label(auth_frame, text="GitHub Token:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5)
        self.github_token_var = tk.StringVar()
        github_entry = ttk.Entry(auth_frame, textvariable=self.github_token_var, 
                                width=50, show='*')
        github_entry.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        ttk.Button(auth_frame, text="Test", 
                  command=self.test_github_connection).grid(row=0, column=2, padx=5)
        
        # GitLab Token
        ttk.Label(auth_frame, text="GitLab Token:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5)
        self.gitlab_token_var = tk.StringVar()
        gitlab_entry = ttk.Entry(auth_frame, textvariable=self.gitlab_token_var, 
                                width=50, show='*')
        gitlab_entry.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        ttk.Button(auth_frame, text="Test", 
                  command=self.test_gitlab_connection).grid(row=1, column=2, padx=5)
        
        # SSH Key Path
        ttk.Label(auth_frame, text="SSH Key Path:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky='w', pady=5)
        self.ssh_key_var = tk.StringVar(value=get_ssh_key_path() or "")
        ssh_frame = ttk.Frame(auth_frame)
        ssh_frame.grid(row=2, column=1, columnspan=2, sticky='ew', padx=10, pady=5)
        ttk.Entry(ssh_frame, textvariable=self.ssh_key_var, width=40).pack(side='left', fill='x', expand=True)
        ttk.Button(ssh_frame, text="Browse", 
                  command=self.browse_ssh_key).pack(side='right', padx=5)
        
        auth_frame.columnconfigure(1, weight=1)
        
        # Provider Selection
        provider_frame = ttk.LabelFrame(scrollable_frame, text="📡 Git Providers", padding=15)
        provider_frame.pack(fill='x', padx=10, pady=10)
        
        self.github_enabled_var = tk.BooleanVar(value=True)
        self.gitlab_enabled_var = tk.BooleanVar(value=True)
        self.bitbucket_enabled_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(provider_frame, text="🐙 GitHub", 
                       variable=self.github_enabled_var).pack(anchor='w')
        ttk.Checkbutton(provider_frame, text="🦊 GitLab", 
                       variable=self.gitlab_enabled_var).pack(anchor='w')
        ttk.Checkbutton(provider_frame, text="🌊 Bitbucket (Coming Soon)", 
                       variable=self.bitbucket_enabled_var, state='disabled').pack(anchor='w')
        
        # Filter Settings
        filter_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Discovery Filters", padding=15)
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        # Repository Type Filters
        type_frame = ttk.Frame(filter_frame)
        type_frame.pack(fill='x', pady=5)
        
        self.include_private_var = tk.BooleanVar(value=True)
        self.include_forks_var = tk.BooleanVar(value=False)
        self.include_archived_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(type_frame, text="🔒 Include Private Repositories", 
                       variable=self.include_private_var).pack(anchor='w')
        ttk.Checkbutton(type_frame, text="🍴 Include Forks", 
                       variable=self.include_forks_var).pack(anchor='w')
        ttk.Checkbutton(type_frame, text="📦 Include Archived", 
                       variable=self.include_archived_var).pack(anchor='w')
        
        # Minimum Stars Filter
        stars_frame = ttk.Frame(filter_frame)
        stars_frame.pack(fill='x', pady=5)
        ttk.Label(stars_frame, text="⭐ Minimum Stars:").pack(side='left')
        self.min_stars_var = tk.IntVar(value=0)
        ttk.Spinbox(stars_frame, from_=0, to=1000, textvariable=self.min_stars_var, 
                   width=10).pack(side='left', padx=10)
        
        # Language Filter
        lang_frame = ttk.Frame(filter_frame)
        lang_frame.pack(fill='x', pady=5)
        ttk.Label(lang_frame, text="💻 Languages (comma-separated, empty = all):").pack(anchor='w')
        self.languages_var = tk.StringVar()
        ttk.Entry(lang_frame, textvariable=self.languages_var, width=50).pack(fill='x', pady=2)
        
        # Exclude Patterns
        exclude_frame = ttk.Frame(filter_frame)
        exclude_frame.pack(fill='x', pady=5)
        ttk.Label(exclude_frame, text="🚫 Exclude Patterns (comma-separated):").pack(anchor='w')
        self.exclude_patterns_var = tk.StringVar(value="test,demo,backup,archive")
        ttk.Entry(exclude_frame, textvariable=self.exclude_patterns_var, width=50).pack(fill='x', pady=2)
        
        # Limits
        limits_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Performance Settings", padding=15)
        limits_frame.pack(fill='x', padx=10, pady=10)
        
        # Max repositories per provider
        max_repos_frame = ttk.Frame(limits_frame)
        max_repos_frame.pack(fill='x', pady=5)
        ttk.Label(max_repos_frame, text="📊 Max Repos per Provider:").pack(side='left')
        self.max_repos_var = tk.IntVar(value=500)
        ttk.Spinbox(max_repos_frame, from_=10, to=5000, increment=50, 
                   textvariable=self.max_repos_var, width=10).pack(side='left', padx=10)
        
        # Concurrent requests
        concurrent_frame = ttk.Frame(limits_frame)
        concurrent_frame.pack(fill='x', pady=5)
        ttk.Label(concurrent_frame, text="⚡ Concurrent Requests:").pack(side='left')
        self.concurrent_var = tk.IntVar(value=10)
        ttk.Spinbox(concurrent_frame, from_=1, to=50, 
                   textvariable=self.concurrent_var, width=10).pack(side='left', padx=10)
        
        # Discovery Controls
        controls_frame = ttk.Frame(scrollable_frame)
        controls_frame.pack(fill='x', padx=10, pady=20)
        
        self.discover_btn = ttk.Button(controls_frame, text="🚀 Start Discovery", 
                                      command=self.start_discovery, style='Action.TButton')
        self.discover_btn.pack(side='left')
        
        self.stop_discovery_btn = ttk.Button(controls_frame, text="⏹️ Stop Discovery", 
                                           command=self.stop_discovery, style='Action.TButton',
                                           state='disabled')
        self.stop_discovery_btn.pack(side='left', padx=10)
        
        # Progress
        self.discovery_progress = ttk.Progressbar(controls_frame, mode='indeterminate')
        self.discovery_progress.pack(side='left', padx=10, fill='x', expand=True)
        
        # Status
        self.discovery_status_var = tk.StringVar(value="Ready to discover repositories")
        ttk.Label(scrollable_frame, textvariable=self.discovery_status_var, 
                 foreground='blue').pack(pady=10)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_selection_tab(self):
        """Create the repository selection tab."""
        selection_frame = ttk.Frame(self.notebook)
        self.notebook.add(selection_frame, text="📋 Selection")
        
        # Top controls
        controls_frame = ttk.Frame(selection_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        # Repository count and stats
        self.repo_count_var = tk.StringVar(value="No repositories discovered")
        ttk.Label(controls_frame, textvariable=self.repo_count_var, 
                 font=('Arial', 12, 'bold')).pack(side='left')
        
        # Selection buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(side='right')
        
        ttk.Button(button_frame, text="✅ Select All", 
                  command=self.select_all_repos).pack(side='left', padx=2)
        ttk.Button(button_frame, text="❌ Deselect All", 
                  command=self.deselect_all_repos).pack(side='left', padx=2)
        ttk.Button(button_frame, text="💾 Save List", 
                  command=self.save_repo_list).pack(side='left', padx=2)
        ttk.Button(button_frame, text="📁 Load List", 
                  command=self.load_repo_list).pack(side='left', padx=2)
        
        # Repository list with treeview
        list_frame = ttk.Frame(selection_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ('name', 'owner', 'language', 'stars', 'forks', 'private', 'provider')
        self.repo_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.repo_tree.heading('#0', text='✓')
        self.repo_tree.heading('name', text='Repository')
        self.repo_tree.heading('owner', text='Owner')
        self.repo_tree.heading('language', text='Language')
        self.repo_tree.heading('stars', text='⭐ Stars')
        self.repo_tree.heading('forks', text='🍴 Forks')
        self.repo_tree.heading('private', text='🔒 Private')
        self.repo_tree.heading('provider', text='Provider')
        
        # Column widths
        self.repo_tree.column('#0', width=50, minwidth=50)
        self.repo_tree.column('name', width=200, minwidth=150)
        self.repo_tree.column('owner', width=120, minwidth=100)
        self.repo_tree.column('language', width=100, minwidth=80)
        self.repo_tree.column('stars', width=80, minwidth=60)
        self.repo_tree.column('forks', width=80, minwidth=60)
        self.repo_tree.column('private', width=80, minwidth=60)
        self.repo_tree.column('provider', width=100, minwidth=80)
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.repo_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.repo_tree.xview)
        self.repo_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.repo_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.repo_tree.bind('<Button-1>', self.on_repo_click)
        self.repo_tree.bind('<Double-1>', self.on_repo_double_click)
        
        # Repository details panel
        details_frame = ttk.LabelFrame(selection_frame, text="📄 Repository Details")
        details_frame.pack(fill='x', padx=10, pady=10)
        
        self.repo_details_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD)
        self.repo_details_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_analysis_tab(self):
        """Create the bulk analysis tab."""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="⚙️ Analysis")
        
        # Analysis configuration
        config_frame = ttk.LabelFrame(analysis_frame, text="📊 Analysis Configuration", padding=15)
        config_frame.pack(fill='x', padx=10, pady=10)
        
        # Template selection
        template_frame = ttk.Frame(config_frame)
        template_frame.pack(fill='x', pady=5)
        
        ttk.Label(template_frame, text="📝 README Template:", font=('Arial', 10, 'bold')).pack(side='left')
        self.bulk_template_var = tk.StringVar(value="modern")
        template_combo = ttk.Combobox(template_frame, textvariable=self.bulk_template_var,
                                     values=self.template_engine.get_available_templates(),
                                     state='readonly', width=20)
        template_combo.pack(side='left', padx=10)
        
        # Analysis options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill='x', pady=10)
        
        self.bulk_include_badges_var = tk.BooleanVar(value=True)
        self.bulk_include_toc_var = tk.BooleanVar(value=True)
        self.bulk_include_contributing_var = tk.BooleanVar(value=True)
        self.bulk_generate_readmes_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(options_frame, text="🏷️ Include Badges", 
                       variable=self.bulk_include_badges_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="📑 Include Table of Contents", 
                       variable=self.bulk_include_toc_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="🤝 Include Contributing Section", 
                       variable=self.bulk_include_contributing_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="📄 Generate README Files", 
                       variable=self.bulk_generate_readmes_var).pack(anchor='w')
        
        # Output directory
        output_frame = ttk.Frame(config_frame)
        output_frame.pack(fill='x', pady=5)
        
        ttk.Label(output_frame, text="📁 Output Directory:").pack(side='left')
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "reporeadme_bulk_output"))
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=40).pack(side='left', padx=10, fill='x', expand=True)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir).pack(side='right')
        
        # Analysis controls
        controls_frame = ttk.Frame(analysis_frame)
        controls_frame.pack(fill='x', padx=10, pady=20)
        
        self.analyze_btn = ttk.Button(controls_frame, text="🔍 Start Analysis", 
                                     command=self.start_bulk_analysis, style='Action.TButton')
        self.analyze_btn.pack(side='left')
        
        self.stop_analysis_btn = ttk.Button(controls_frame, text="⏹️ Stop Analysis", 
                                          command=self.stop_analysis, style='Action.TButton',
                                          state='disabled')
        self.stop_analysis_btn.pack(side='left', padx=10)
        
        # Progress
        progress_frame = ttk.Frame(analysis_frame)
        progress_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(progress_frame, text="Progress:").pack(anchor='w')
        self.analysis_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.analysis_progress.pack(fill='x', pady=5)
        
        self.analysis_status_var = tk.StringVar(value="Ready to analyze repositories")
        ttk.Label(progress_frame, textvariable=self.analysis_status_var).pack(anchor='w')
        
        # Real-time results
        results_frame = ttk.LabelFrame(analysis_frame, text="📊 Analysis Progress")
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.analysis_log = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.analysis_log.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_results_tab(self):
        """Create the results and export tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📊 Results")
        
        # Summary statistics
        stats_frame = ttk.LabelFrame(results_frame, text="📈 Analysis Summary", padding=15)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, state='disabled')
        self.stats_text.pack(fill='x', pady=5)
        
        # Export options
        export_frame = ttk.LabelFrame(results_frame, text="💾 Export Results", padding=15)
        export_frame.pack(fill='x', padx=10, pady=10)
        
        # Export and commit options (organized in rows)
        export_buttons_top = ttk.Frame(export_frame)
        export_buttons_top.pack(fill='x', pady=(0, 5))
        
        ttk.Button(export_buttons_top, text="💾 Export All READMEs", 
                  command=self.export_all_readmes).pack(side='left', padx=5)
        ttk.Button(export_buttons_top, text="📤 Commit All READMEs", 
                  command=self.commit_all_readmes).pack(side='left', padx=5)
        ttk.Button(export_buttons_top, text="📁 Open Output Folder", 
                  command=self.open_output_folder).pack(side='left', padx=5)
        
        export_buttons_bottom = ttk.Frame(export_frame)
        export_buttons_bottom.pack(fill='x')
        
        ttk.Button(export_buttons_bottom, text="📄 Export Analysis Report", 
                  command=self.export_analysis_report).pack(side='left', padx=5)
        ttk.Button(export_buttons_bottom, text="📊 Export Repository Data", 
                  command=self.export_repository_data).pack(side='left', padx=5)
        ttk.Button(export_buttons_bottom, text="🎨 Open Template Builder", 
                  command=self.open_template_builder).pack(side='left', padx=5)
        
        # Generated files and repository actions
        files_frame = ttk.LabelFrame(results_frame, text="📁 Generated READMEs & Actions")
        files_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Repository results tree with actions
        tree_frame = ttk.Frame(files_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.results_tree = ttk.Treeview(tree_frame, columns=('status', 'size', 'actions'), show='tree headings', height=12)
        self.results_tree.heading('#0', text='Repository', anchor='w')
        self.results_tree.heading('status', text='Status', anchor='center')
        self.results_tree.heading('size', text='Size', anchor='center') 
        self.results_tree.heading('actions', text='Actions', anchor='center')
        
        self.results_tree.column('#0', width=200)
        self.results_tree.column('status', width=100)
        self.results_tree.column('size', width=80)
        self.results_tree.column('actions', width=120)
        
        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side='left', fill='both', expand=True)
        results_scrollbar.pack(side='right', fill='y')
        
        # Individual repository actions
        actions_frame = ttk.Frame(files_frame)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(actions_frame, text="Individual Repository Actions:", font=('Arial', 9, 'bold')).pack(side='left')
        ttk.Button(actions_frame, text="👁️ Preview README", 
                  command=self.preview_selected_readme).pack(side='right', padx=2)
        ttk.Button(actions_frame, text="💾 Export README", 
                  command=self.export_selected_readme).pack(side='right', padx=2)
        ttk.Button(actions_frame, text="📤 Commit README", 
                  command=self.commit_selected_readme).pack(side='right', padx=2)
        
        # Bind double-click to preview
        self.results_tree.bind('<Double-1>', lambda e: self.preview_selected_readme())
    
    def create_bottom_buttons(self):
        """Create bottom control buttons."""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="❌ Close", command=self.close_dialog).pack(side='right')
        ttk.Button(button_frame, text="💾 Save Settings", command=self.save_settings).pack(side='right', padx=10)
    
    # Event handlers and methods continue in next part...
    
    def test_github_connection(self):
        """Test GitHub API connection."""
        token = self.github_token_var.get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a GitHub token to test the connection.")
            return
        
        try:
            from github import Github
            github = Github(token)
            user = github.get_user()
            messagebox.showinfo("Connection Success", f"✅ Connected to GitHub as: {user.login}")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"❌ Failed to connect to GitHub:\n{str(e)}")
    
    def test_gitlab_connection(self):
        """Test GitLab API connection."""
        token = self.gitlab_token_var.get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a GitLab token to test the connection.")
            return
        
        try:
            from gitlab import Gitlab
            gitlab = Gitlab("https://gitlab.com", private_token=token)
            gitlab.auth()
            user = gitlab.user
            messagebox.showinfo("Connection Success", f"✅ Connected to GitLab as: {user.username}")
        except Exception as e:
            messagebox.showerror("Connection Failed", f"❌ Failed to connect to GitLab:\n{str(e)}")
    
    def browse_ssh_key(self):
        """Browse for SSH key file."""
        file_path = filedialog.askopenfilename(
            title="Select SSH Private Key",
            initialdir=str(Path.home() / '.ssh'),
            filetypes=[("SSH Keys", "id_*"), ("All files", "*.*")]
        )
        if file_path:
            self.ssh_key_var.set(file_path)
    
    def start_discovery(self):
        """Start repository discovery in background thread."""
        if self.is_discovering:
            return
        
        # Validate settings
        if not self.github_enabled_var.get() and not self.gitlab_enabled_var.get():
            messagebox.showwarning("No Providers", "Please enable at least one Git provider.")
            return
        
        if self.github_enabled_var.get() and not self.github_token_var.get().strip():
            messagebox.showwarning("Missing Token", "GitHub token is required for repository discovery.")
            return
        
        if self.gitlab_enabled_var.get() and not self.gitlab_token_var.get().strip():
            messagebox.showwarning("Missing Token", "GitLab token is required for repository discovery.")
            return
        
        self.is_discovering = True
        self.discover_btn.config(state='disabled')
        self.stop_discovery_btn.config(state='normal')
        self.discovery_progress.start()
        
        # Start discovery in background thread
        self.discovery_task = threading.Thread(target=self._discovery_worker)
        self.discovery_task.daemon = True
        self.discovery_task.start()
    
    def _discovery_worker(self):
        """Worker thread for repository discovery."""
        try:
            # Create discovery configuration
            languages = [lang.strip() for lang in self.languages_var.get().split(',') if lang.strip()] or None
            exclude_patterns = [pattern.strip() for pattern in self.exclude_patterns_var.get().split(',') if pattern.strip()] or None
            
            config = DiscoveryConfig(
                include_github=self.github_enabled_var.get(),
                include_gitlab=self.gitlab_enabled_var.get(),
                github_token=self.github_token_var.get().strip() or None,
                gitlab_token=self.gitlab_token_var.get().strip() or None,
                ssh_key_path=self.ssh_key_var.get().strip() or None,
                include_private=self.include_private_var.get(),
                include_forks=self.include_forks_var.get(),
                include_archived=self.include_archived_var.get(),
                min_stars=self.min_stars_var.get(),
                languages=languages,
                exclude_patterns=exclude_patterns,
                max_repos_per_provider=self.max_repos_var.get(),
                concurrent_requests=self.concurrent_var.get()
            )
            
            # Create discovery engine
            discovery = RepositoryDiscovery(config)
            
            # Progress callback
            def progress_callback(message, count):
                self.dialog.after(0, lambda: self.discovery_status_var.set(f"{message} (Total: {count})"))
            
            # Run discovery
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            repos = loop.run_until_complete(
                discovery.discover_all_repositories(progress_callback)
            )
            
            loop.close()
            
            # Update UI in main thread
            self.dialog.after(0, lambda: self._discovery_completed(repos, discovery.get_statistics()))
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
            self.dialog.after(0, lambda: self._discovery_failed(str(e)))
    
    def _discovery_completed(self, repos: List[RepositoryInfo], stats: Dict):
        """Handle discovery completion."""
        self.discovered_repos = repos
        self.is_discovering = False
        
        # Update UI
        self.discover_btn.config(state='normal')
        self.stop_discovery_btn.config(state='disabled')
        self.discovery_progress.stop()
        
        # Update repository list
        self._update_repository_list()
        
        # Update status
        self.discovery_status_var.set(f"✅ Discovery completed! Found {len(repos)} repositories")
        
        # Show summary
        messagebox.showinfo("Discovery Complete", 
                          f"🎉 Repository discovery completed!\n\n"
                          f"Total repositories: {stats.get('total_discovered', 0)}\n"
                          f"GitHub: {stats.get('github_repos', 0)}\n"
                          f"GitLab: {stats.get('gitlab_repos', 0)}\n"
                          f"Private: {stats.get('private_repos', 0)}\n"
                          f"Public: {stats.get('public_repos', 0)}")
        
        # Switch to selection tab
        self.notebook.select(1)
    
    def _discovery_failed(self, error_message: str):
        """Handle discovery failure."""
        self.is_discovering = False
        self.discover_btn.config(state='normal')
        self.stop_discovery_btn.config(state='disabled')
        self.discovery_progress.stop()
        self.discovery_status_var.set("❌ Discovery failed")
        
        messagebox.showerror("Discovery Failed", f"Repository discovery failed:\n{error_message}")
    
    def stop_discovery(self):
        """Stop the discovery process."""
        if self.discovery_task and self.discovery_task.is_alive():
            # Note: This is a simple stop - in production you'd want proper cancellation
            self.is_discovering = False
            self.discovery_status_var.set("⏹️ Stopping discovery...")
    
    def _update_repository_list(self):
        """Update the repository list in the selection tab."""
        # Clear existing items
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        # Add repositories
        for repo in self.discovered_repos:
            self.repo_tree.insert('', 'end', iid=repo.full_name, text='☐',
                                 values=(repo.name, repo.owner, repo.language, 
                                        repo.stars, repo.forks, 
                                        '🔒' if repo.is_private else '🌍',
                                        repo.provider))
        
        # Update count
        self.repo_count_var.set(f"📊 {len(self.discovered_repos)} repositories discovered")
    
    def on_repo_click(self, event):
        """Handle repository list click."""
        item = self.repo_tree.selection()[0] if self.repo_tree.selection() else None
        if not item:
            return
        
        # Toggle selection
        current_text = self.repo_tree.item(item, 'text')
        if current_text == '☐':
            self.repo_tree.item(item, text='✅')
        else:
            self.repo_tree.item(item, text='☐')
    
    def on_repo_double_click(self, event):
        """Handle repository list double-click."""
        item = self.repo_tree.selection()[0] if self.repo_tree.selection() else None
        if not item:
            return
        
        # Find repository and show details
        repo = next((r for r in self.discovered_repos if r.full_name == item), None)
        if repo:
            self._show_repository_details(repo)
    
    def _show_repository_details(self, repo: RepositoryInfo):
        """Show detailed repository information."""
        details = f"""Repository: {repo.name}
Owner: {repo.owner}
Full Name: {repo.full_name}
Description: {repo.description}

Language: {repo.language}
Stars: {repo.stars}
Forks: {repo.forks}
Private: {'Yes' if repo.is_private else 'No'}
Fork: {'Yes' if repo.is_fork else 'No'}
Provider: {repo.provider.title()}

Created: {repo.created_at}
Updated: {repo.updated_at}
Size: {repo.size_kb} KB
Default Branch: {repo.default_branch}
Has README: {'Yes' if repo.has_readme else 'No'}
License: {repo.license or 'None'}

Topics: {', '.join(repo.topics) if repo.topics else 'None'}

URLs:
- Repository: {repo.url}
- Clone (HTTPS): {repo.clone_url}
- Clone (SSH): {repo.ssh_url}
"""
        
        self.repo_details_text.delete('1.0', tk.END)
        self.repo_details_text.insert('1.0', details)
    
    def select_all_repos(self):
        """Select all repositories."""
        for item in self.repo_tree.get_children():
            self.repo_tree.item(item, text='✅')
    
    def deselect_all_repos(self):
        """Deselect all repositories."""
        for item in self.repo_tree.get_children():
            self.repo_tree.item(item, text='☐')
    
    def get_selected_repositories(self) -> List[RepositoryInfo]:
        """Get list of selected repositories."""
        selected = []
        for item in self.repo_tree.get_children():
            if self.repo_tree.item(item, 'text') == '✅':
                repo = next((r for r in self.discovered_repos if r.full_name == item), None)
                if repo:
                    selected.append(repo)
        return selected
    
    def start_bulk_analysis(self):
        """Start bulk analysis of selected repositories."""
        selected_repos = self.get_selected_repositories()
        if not selected_repos:
            messagebox.showwarning("No Selection", "Please select repositories to analyze.")
            return
        
        if self.is_analyzing:
            return
        
        self.is_analyzing = True
        self.analyze_btn.config(state='disabled')
        self.stop_analysis_btn.config(state='normal')
        self.analysis_progress.config(maximum=len(selected_repos))
        self.analysis_progress['value'] = 0
        
        # Clear analysis log
        self.analysis_log.delete('1.0', tk.END)
        
        # Start analysis in background thread
        self.analysis_task = threading.Thread(target=self._analysis_worker, args=(selected_repos,))
        self.analysis_task.daemon = True
        self.analysis_task.start()
    
    def _analysis_worker(self, repositories: List[RepositoryInfo]):
        """Worker thread for bulk analysis."""
        try:
            output_dir = Path(self.output_dir_var.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cloner = BulkRepositoryCloner(self.ssh_key_var.get().strip() or None)
            
            completed = 0
            for repo in repositories:
                if not self.is_analyzing:  # Check for cancellation
                    break
                
                try:
                    # Update status
                    self.dialog.after(0, lambda r=repo: self.analysis_status_var.set(f"Analyzing {r.name}..."))
                    self.dialog.after(0, lambda msg=f"🔍 Starting analysis of {repo.name}": self._log_analysis(msg))
                    
                    # Clone repository synchronously
                    repo_path = self._clone_repository_sync(cloner, repo)
                    if not repo_path:
                        self.dialog.after(0, lambda msg=f"❌ Failed to clone {repo.name}": self._log_analysis(msg))
                        continue
                    
                    # Analyze repository
                    metadata = self.repository_analyzer.analyze_repository(repo_path)
                    if not metadata:
                        self.dialog.after(0, lambda msg=f"❌ Failed to analyze {repo.name}": self._log_analysis(msg))
                        continue
                    
                    # Update metadata with repository info
                    metadata.name = repo.name
                    metadata.repository_url = repo.url
                    
                    # Track completed repository data
                    repo_data = {
                        'repository_info': repo,
                        'metadata': metadata
                    }
                    
                    # Generate README if requested
                    if self.bulk_generate_readmes_var.get():
                        config = TemplateConfig(
                            template_name=self.bulk_template_var.get(),
                            include_badges=self.bulk_include_badges_var.get(),
                            include_toc=self.bulk_include_toc_var.get(),
                            include_contributing=self.bulk_include_contributing_var.get()
                        )
                        
                        readme_content = self.template_engine.generate_readme(metadata, config)
                        repo_data['readme_content'] = readme_content
                        
                        # Save README
                        readme_file = output_dir / f"{repo.name}_README.md"
                        readme_file.write_text(readme_content, encoding='utf-8')
                        
                        self.dialog.after(0, lambda msg=f"📄 Generated README for {repo.name}": self._log_analysis(msg))
                    
                    # Store completed repository data
                    self.completed_repos[repo.full_name] = repo_data
                    
                    # Update results tree
                    readme_size = len(repo_data.get('readme_content', ''))
                    size_text = f"{readme_size:,} chars" if readme_size > 0 else "Not generated"
                    status_text = "✅ Complete" if 'readme_content' in repo_data else "📊 Analyzed"
                    
                    self.dialog.after(0, lambda r=repo, st=status_text, sz=size_text: 
                                    self._add_to_results_tree(r.full_name, st, sz))
                    
                    # Save metadata
                    metadata_file = output_dir / f"{repo.name}_metadata.json"
                    with metadata_file.open('w', encoding='utf-8') as f:
                        json.dump(metadata.__dict__, f, indent=2, default=str)
                    
                    completed += 1
                    self.dialog.after(0, lambda: self._update_analysis_progress(completed))
                    self.dialog.after(0, lambda msg=f"✅ Completed analysis of {repo.name}": self._log_analysis(msg))
                    
                except Exception as e:
                    self.logger.error(f"Analysis failed for {repo.name}: {e}")
                    self.dialog.after(0, lambda msg=f"❌ Error analyzing {repo.name}: {str(e)}": self._log_analysis(msg))
            
            # Cleanup
            cloner.cleanup_temp_dirs()
            
            # Complete
            self.dialog.after(0, lambda: self._analysis_completed(completed, len(repositories)))
            
        except Exception as e:
            self.logger.error(f"Bulk analysis failed: {e}")
            self.dialog.after(0, lambda: self._analysis_failed(str(e)))
    
    def _clone_repository_sync(self, cloner, repo) -> Optional[str]:
        """Synchronously clone a repository for analysis."""
        import tempfile
        import subprocess
        import os
        import shutil
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"reporeadme_{repo.name.replace('/', '_')}_")
            clone_path = os.path.join(temp_dir, repo.name.split('/')[-1])
            
            # Prepare git command
            if cloner.ssh_key_path and hasattr(repo, 'ssh_url') and repo.ssh_url:
                # Use SSH URL with specific key
                git_ssh_command = f"ssh -i {cloner.ssh_key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
                env = os.environ.copy()
                env['GIT_SSH_COMMAND'] = git_ssh_command
                clone_url = repo.ssh_url
            else:
                # Use HTTPS URL (works for public repos)
                env = os.environ.copy()
                clone_url = repo.clone_url
            
            # Execute git clone with timeout
            result = subprocess.run([
                'git', 'clone', '--depth', '1', clone_url, clone_path
            ], capture_output=True, text=True, timeout=120, env=env)
            
            if result.returncode == 0 and os.path.exists(clone_path):
                return clone_path
            else:
                # Cleanup on failure
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                return None
                
        except Exception as e:
            # Cleanup on exception
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    def _log_analysis(self, message: str):
        """Add message to analysis log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.analysis_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.analysis_log.see(tk.END)
    
    def _update_analysis_progress(self, completed: int):
        """Update analysis progress."""
        self.analysis_progress['value'] = completed
    
    def _add_to_results_tree(self, repo_name: str, status: str, size: str):
        """Add repository to results tree."""
        try:
            # Add to results tree
            self.results_tree.insert('', 'end', iid=repo_name, text=f"📁 {repo_name}", 
                                   values=(status, size, "Available"))
        except tk.TclError:
            # Item might already exist, update it instead
            try:
                self.results_tree.set(repo_name, 'status', status)
                self.results_tree.set(repo_name, 'size', size)
                self.results_tree.set(repo_name, 'actions', "Available")
            except:
                pass  # Ignore if still fails
    
    def _analysis_completed(self, completed: int, total: int):
        """Handle analysis completion."""
        self.is_analyzing = False
        self.analyze_btn.config(state='normal')
        self.stop_analysis_btn.config(state='disabled')
        self.analysis_status_var.set(f"✅ Analysis completed: {completed}/{total}")
        
        messagebox.showinfo("Analysis Complete", 
                          f"🎉 Bulk analysis completed!\n\n"
                          f"Processed: {completed}/{total} repositories\n"
                          f"Output directory: {self.output_dir_var.get()}")
        
        # Switch to results tab
        self.notebook.select(3)
        self._update_results_display()
    
    def _analysis_failed(self, error_message: str):
        """Handle analysis failure."""
        self.is_analyzing = False
        self.analyze_btn.config(state='normal')
        self.stop_analysis_btn.config(state='disabled')
        self.analysis_status_var.set("❌ Analysis failed")
        
        messagebox.showerror("Analysis Failed", f"Bulk analysis failed:\n{error_message}")
    
    def stop_analysis(self):
        """Stop the analysis process."""
        if self.analysis_task and self.analysis_task.is_alive():
            self.is_analyzing = False
            self.analysis_status_var.set("⏹️ Stopping analysis...")
    
    def _update_results_display(self):
        """Update the results display."""
        # Update stats
        output_dir = Path(self.output_dir_var.get())
        if output_dir.exists():
            readme_files = list(output_dir.glob("*_README.md"))
            metadata_files = list(output_dir.glob("*_metadata.json"))
            
            stats_text = f"""Analysis Results Summary
========================

Generated README Files: {len(readme_files)}
Generated Metadata Files: {len(metadata_files)}
Output Directory: {output_dir}

Files by Type:
- README files: {len(readme_files)}
- Metadata files: {len(metadata_files)}
- Total files: {len(list(output_dir.glob("*")))}
"""
            
            self.stats_text.config(state='normal')
            self.stats_text.delete('1.0', tk.END)
            self.stats_text.insert('1.0', stats_text)
            self.stats_text.config(state='disabled')
            
            # Update results tree (if not already populated)
            if hasattr(self, 'results_tree'):
                # Clear existing results
                for item in self.results_tree.get_children():
                    self.results_tree.delete(item)
                
                # Add completed repositories to results tree
                for repo_name, repo_data in self.completed_repos.items():
                    readme_size = len(repo_data.get('readme_content', ''))
                    size_text = f"{readme_size:,} chars" if readme_size > 0 else "Not generated"
                    status_text = "✅ Complete" if 'readme_content' in repo_data else "📊 Analyzed"
                    
                    self.results_tree.insert('', 'end', iid=repo_name, text=f"📁 {repo_name}", 
                                           values=(status_text, size_text, "Available"))
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def save_repo_list(self):
        """Save discovered repositories to file."""
        if not self.discovered_repos:
            messagebox.showwarning("No Data", "No repositories to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Repository List",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="discovered_repositories.json"
        )
        
        if file_path:
            try:
                discovery = RepositoryDiscovery(DiscoveryConfig())
                discovery.discovered_repos = self.discovered_repos
                discovery.save_discovered_repos(file_path)
                messagebox.showinfo("Saved", f"Repository list saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save repository list:\n{str(e)}")
    
    def load_repo_list(self):
        """Load discovered repositories from file."""
        file_path = filedialog.askopenfilename(
            title="Load Repository List",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                discovery = RepositoryDiscovery(DiscoveryConfig())
                if discovery.load_discovered_repos(file_path):
                    self.discovered_repos = discovery.discovered_repos
                    self._update_repository_list()
                    messagebox.showinfo("Loaded", f"Repository list loaded from:\n{file_path}")
                else:
                    messagebox.showerror("Load Error", "Failed to load repository list.")
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load repository list:\n{str(e)}")
    
    # Enhanced Export and Commit Methods
    
    def export_all_readmes(self):
        """Export all generated README files to a folder."""
        if not hasattr(self, 'completed_repos') or not self.completed_repos:
            messagebox.showwarning("No READMEs", "No README files have been generated yet.")
            return
        
        # Choose export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        try:
            success_count = 0
            for repo_name, repo_data in self.completed_repos.items():
                if 'readme_content' in repo_data:
                    file_path = os.path.join(export_dir, f"{repo_name.replace('/', '_')}_README.md")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(repo_data['readme_content'])
                    success_count += 1
            
            messagebox.showinfo("Export Complete", 
                              f"Successfully exported {success_count} README files to:\n{export_dir}")
            self._log_analysis(f"✅ Exported {success_count} README files to {export_dir}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export README files: {str(e)}")
            self.logger.error(f"Bulk README export failed: {e}", "BULK_EXPORT")
    
    def commit_all_readmes(self):
        """Commit all generated README files to their respective repositories."""
        if not hasattr(self, 'completed_repos') or not self.completed_repos:
            messagebox.showwarning("No READMEs", "No README files have been generated yet.")
            return
        
        # Show bulk commit dialog
        bulk_commit_dialog = BulkCommitDialog(self.dialog, self.completed_repos, self.logger)
        
        if bulk_commit_dialog.success:
            self._log_analysis(f"✅ Bulk commit completed: {bulk_commit_dialog.success_count} repositories")
            messagebox.showinfo("Bulk Commit Complete", 
                              f"Successfully committed READMEs to {bulk_commit_dialog.success_count} repositories!")
    
    def open_template_builder(self):
        """Open the template builder dialog."""
        try:
            # Import the template builder from the main GUI module
            from template_builder import create_custom_template_builder
            result = create_custom_template_builder(self.dialog)
            
            if result:
                # Update template dropdown if a new template was created
                custom_name = f"custom_{result.name.lower().replace(' ', '_')}"
                current_values = list(self.bulk_template_var.get())
                if hasattr(self, 'template_combo') and custom_name not in current_values:
                    self.template_combo['values'] = current_values + [custom_name]
                
                messagebox.showinfo("Success", f"Custom template '{result.name}' created successfully!")
                
        except Exception as e:
            messagebox.showerror("Template Builder Error", f"Failed to open template builder: {str(e)}")
    
    # Individual Repository Actions
    
    def preview_selected_readme(self):
        """Preview the README for the selected repository."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a repository to preview.")
            return
        
        repo_name = selection[0]
        if not hasattr(self, 'completed_repos') or repo_name not in self.completed_repos:
            messagebox.showwarning("No README", "No README generated for this repository yet.")
            return
        
        readme_content = self.completed_repos[repo_name].get('readme_content', '')
        if not readme_content:
            messagebox.showwarning("No Content", "README content not available.")
            return
        
        # Create preview dialog
        preview_dialog = ReadmePreviewDialog(self.dialog, repo_name, readme_content)
    
    def export_selected_readme(self):
        """Export the README for the selected repository."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a repository to export.")
            return
        
        repo_name = selection[0]
        if not hasattr(self, 'completed_repos') or repo_name not in self.completed_repos:
            messagebox.showwarning("No README", "No README generated for this repository yet.")
            return
        
        readme_content = self.completed_repos[repo_name].get('readme_content', '')
        if not readme_content:
            messagebox.showwarning("No Content", "README content not available.")
            return
        
        # Save file dialog
        safe_name = re.sub(r'[^\w\-_.]', '_', repo_name.replace('/', '_'))
        default_name = f"{safe_name}_README.md"
        
        file_path = filedialog.asksaveasfilename(
            title=f"Save README for {repo_name}",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                
                messagebox.showinfo("Success", f"README exported successfully!\n\n📁 Location: {file_path}")
                self._log_analysis(f"✅ Exported README for {repo_name} to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export README: {str(e)}")
    
    def commit_selected_readme(self):
        """Commit the README for the selected repository."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a repository to commit.")
            return
        
        repo_name = selection[0]
        if not hasattr(self, 'completed_repos') or repo_name not in self.completed_repos:
            messagebox.showwarning("No README", "No README generated for this repository yet.")
            return
        
        repo_data = self.completed_repos[repo_name]
        readme_content = repo_data.get('readme_content', '')
        if not readme_content:
            messagebox.showwarning("No Content", "README content not available.")
            return
        
        # Create a repository item for the commit dialog
        repo_info = repo_data.get('repository_info')
        if repo_info:
            # Import from gui module
            from gui import CommitReadmeDialog, RepositoryItem
            
            repo_item = RepositoryItem(
                name=repo_info.full_name,
                path="",  # No local path for discovered repos
                url=repo_info.url,
                repo_type="github"  # Assuming GitHub for bulk discovered repos
            )
            
            commit_dialog = CommitReadmeDialog(self.dialog, repo_item, readme_content, self.logger)
            
            if commit_dialog.success:
                self._log_analysis(f"✅ README committed for {repo_name}")
                messagebox.showinfo("Success", f"README successfully committed to {repo_name}!")
                
                # Update results tree status
                self.results_tree.set(repo_name, 'status', '📤 Committed')
        else:
            messagebox.showerror("Error", "Repository information not available for commit.")
    
    # Original Export Methods (Enhanced)
    
    def export_analysis_report(self):
        """Export comprehensive analysis report."""
        if not hasattr(self, 'completed_repos') or not self.completed_repos:
            messagebox.showwarning("No Data", "No analysis data available to export.")
            return
        
        # Choose save location
        file_path = filedialog.asksaveasfilename(
            title="Save Analysis Report",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"bulk_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        
        if file_path:
            try:
                # Generate comprehensive HTML report
                report_html = self._generate_analysis_report_html()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_html)
                
                messagebox.showinfo("Success", f"Analysis report exported!\n\n📁 Location: {file_path}")
                self._log_analysis(f"✅ Analysis report exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export analysis report: {str(e)}")
    
    def export_repository_data(self):
        """Export repository data in CSV format."""
        if not hasattr(self, 'completed_repos') or not self.completed_repos:
            messagebox.showwarning("No Data", "No repository data available to export.")
            return
        
        # Choose save location
        file_path = filedialog.asksaveasfilename(
            title="Save Repository Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"repository_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write headers
                    writer.writerow([
                        'Repository', 'Language', 'Stars', 'Forks', 'Size (KB)',
                        'Has README', 'Analysis Status', 'Generated README Size'
                    ])
                    
                    # Write data
                    for repo_name, repo_data in self.completed_repos.items():
                        repo_info = repo_data.get('repository_info')
                        readme_size = len(repo_data.get('readme_content', '')) if 'readme_content' in repo_data else 0
                        
                        writer.writerow([
                            repo_name,
                            repo_info.language if repo_info else 'Unknown',
                            repo_info.stars if repo_info else 0,
                            repo_info.forks if repo_info else 0,
                            repo_info.size_kb if repo_info else 0,
                            repo_info.has_readme if repo_info else False,
                            'Completed',
                            readme_size
                        ])
                
                messagebox.showinfo("Success", f"Repository data exported!\n\n📁 Location: {file_path}")
                self._log_analysis(f"✅ Repository data exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export repository data: {str(e)}")
    
    def _generate_analysis_report_html(self):
        """Generate comprehensive HTML analysis report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RepoReadme Bulk Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
        .header {{ background: #0969da; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: #f6f8fa; padding: 15px; border-radius: 6px; border-left: 4px solid #0969da; }}
        .repositories {{ background: white; border: 1px solid #d0d7de; border-radius: 6px; }}
        .repo-item {{ padding: 15px; border-bottom: 1px solid #d0d7de; }}
        .repo-item:last-child {{ border-bottom: none; }}
        .repo-name {{ font-weight: bold; color: #0969da; }}
        .repo-stats {{ font-size: 14px; color: #656d76; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #d0d7de; }}
        th {{ background: #f6f8fa; font-weight: 600; }}
        .success {{ color: #1a7f37; }}
        .error {{ color: #cf222e; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 RepoReadme Bulk Analysis Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>📊 Total Repositories</h3>
            <p style="font-size: 24px; margin: 0;">{len(self.completed_repos)}</p>
        </div>
        <div class="stat-card">
            <h3>✅ READMEs Generated</h3>
            <p style="font-size: 24px; margin: 0;">{len([r for r in self.completed_repos.values() if 'readme_content' in r])}</p>
        </div>
        <div class="stat-card">
            <h3>📝 Total README Size</h3>
            <p style="font-size: 24px; margin: 0;">{sum(len(r.get('readme_content', '')) for r in self.completed_repos.values()):,} chars</p>
        </div>
    </div>
    
    <h2>📁 Repository Details</h2>
    <table>
        <thead>
            <tr>
                <th>Repository</th>
                <th>Language</th>
                <th>Stars</th>
                <th>Size (KB)</th>
                <th>README Generated</th>
                <th>README Size</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for repo_name, repo_data in self.completed_repos.items():
            repo_info = repo_data.get('repository_info')
            readme_size = len(repo_data.get('readme_content', ''))
            has_readme = 'readme_content' in repo_data
            
            html += f"""
            <tr>
                <td class="repo-name">{repo_name}</td>
                <td>{repo_info.language if repo_info else 'Unknown'}</td>
                <td>{repo_info.stars if repo_info else 0:,}</td>
                <td>{repo_info.size_kb if repo_info else 0:,}</td>
                <td class="{'success' if has_readme else 'error'}">{'✅ Yes' if has_readme else '❌ No'}</td>
                <td>{readme_size:,} chars</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <div style="margin-top: 40px; padding: 20px; background: #f6f8fa; border-radius: 6px;">
        <h3>📋 Report Summary</h3>
        <p>This report was generated by RepoReadme's Bulk Analyzer, which provides comprehensive repository discovery, analysis, and README generation capabilities.</p>
        <p>For more information, visit the RepoReadme project on GitHub.</p>
    </div>
</body>
</html>
"""
        return html
    
    def open_output_folder(self):
        """Open the output folder in file manager."""
        output_dir = Path(self.output_dir_var.get())
        if output_dir.exists():
            import subprocess
            import platform
            
            try:
                if platform.system() == "Windows":
                    os.startfile(str(output_dir))
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", str(output_dir)])
                else:  # Linux
                    subprocess.call(["xdg-open", str(output_dir)])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open folder:\n{str(e)}")
        else:
            messagebox.showwarning("Not Found", "Output directory does not exist yet.")
    
    def load_settings(self):
        """Load saved settings."""
        try:
            settings_file = Path.home() / '.reporeadme' / 'bulk_analyzer_settings.json'
            if settings_file.exists():
                with settings_file.open('r') as f:
                    settings = json.load(f)
                
                # Load authentication
                self.github_token_var.set(settings.get('github_token', ''))
                self.gitlab_token_var.set(settings.get('gitlab_token', ''))
                self.ssh_key_var.set(settings.get('ssh_key_path', get_ssh_key_path() or ''))
                
                # Load filters
                self.include_private_var.set(settings.get('include_private', True))
                self.include_forks_var.set(settings.get('include_forks', False))
                self.include_archived_var.set(settings.get('include_archived', False))
                self.min_stars_var.set(settings.get('min_stars', 0))
                self.languages_var.set(settings.get('languages', ''))
                self.exclude_patterns_var.set(settings.get('exclude_patterns', 'test,demo,backup,archive'))
                
                # Load limits
                self.max_repos_var.set(settings.get('max_repos', 500))
                self.concurrent_var.set(settings.get('concurrent_requests', 10))
                
                # Load analysis settings
                self.bulk_template_var.set(settings.get('template', 'modern'))
                self.output_dir_var.set(settings.get('output_dir', str(Path.home() / "reporeadme_bulk_output")))
                
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save current settings."""
        try:
            settings_dir = Path.home() / '.reporeadme'
            settings_dir.mkdir(exist_ok=True)
            
            settings = {
                'github_token': self.github_token_var.get(),
                'gitlab_token': self.gitlab_token_var.get(),
                'ssh_key_path': self.ssh_key_var.get(),
                'include_private': self.include_private_var.get(),
                'include_forks': self.include_forks_var.get(),
                'include_archived': self.include_archived_var.get(),
                'min_stars': self.min_stars_var.get(),
                'languages': self.languages_var.get(),
                'exclude_patterns': self.exclude_patterns_var.get(),
                'max_repos': self.max_repos_var.get(),
                'concurrent_requests': self.concurrent_var.get(),
                'template': self.bulk_template_var.get(),
                'output_dir': self.output_dir_var.get()
            }
            
            settings_file = settings_dir / 'bulk_analyzer_settings.json'
            with settings_file.open('w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{str(e)}")
    
    def close_dialog(self):
        """Close the dialog."""
        if self.is_discovering or self.is_analyzing:
            if messagebox.askyesno("Confirm Close", "Operations are still running. Do you want to stop them and close?"):
                self.is_discovering = False
                self.is_analyzing = False
                self.dialog.destroy()
        else:
            self.dialog.destroy()


class BulkCommitDialog:
    """Dialog for bulk committing README files to repositories."""
    
    def __init__(self, parent, completed_repos, logger):
        self.success = False
        self.success_count = 0
        self.completed_repos = completed_repos
        self.logger = logger
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📤 Bulk Commit READMEs")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 350
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 250
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        
        # Wait for dialog
        parent.wait_window(self.dialog)
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(header_frame, text=f"📤 Bulk Commit {len(self.completed_repos)} READMEs", 
                 font=('Arial', 12, 'bold')).pack()
        
        # Commit options
        options_frame = ttk.LabelFrame(self.dialog, text="Commit Options", padding=10)
        options_frame.pack(fill='x', padx=20, pady=10)
        
        # Global commit message
        ttk.Label(options_frame, text="Commit Message:").pack(anchor='w')
        self.commit_msg_var = tk.StringVar(value="📝 Add/Update README.md via RepoReadme Bulk Analyzer")
        commit_entry = ttk.Entry(options_frame, textvariable=self.commit_msg_var, width=80)
        commit_entry.pack(fill='x', pady=5)
        
        # Options
        self.overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Overwrite existing README.md files", 
                       variable=self.overwrite_var).pack(anchor='w', pady=2)
        
        self.skip_errors_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Continue on errors (skip failed commits)", 
                       variable=self.skip_errors_var).pack(anchor='w', pady=2)
        
        # Repository list
        repos_frame = ttk.LabelFrame(self.dialog, text="Repositories to Commit", padding=10)
        repos_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Repository tree
        self.commit_tree = ttk.Treeview(repos_frame, columns=('status',), show='tree headings', height=10)
        self.commit_tree.heading('#0', text='Repository', anchor='w')
        self.commit_tree.heading('status', text='Status', anchor='center')
        
        self.commit_tree.column('#0', width=300)
        self.commit_tree.column('status', width=150)
        
        # Add repositories
        for repo_name in self.completed_repos.keys():
            self.commit_tree.insert('', 'end', iid=repo_name, text=f"📁 {repo_name}", 
                                   values=('Ready',))
        
        # Scrollbar
        commit_scrollbar = ttk.Scrollbar(repos_frame, orient='vertical', command=self.commit_tree.yview)
        self.commit_tree.configure(yscrollcommand=commit_scrollbar.set)
        
        self.commit_tree.pack(side='left', fill='both', expand=True)
        commit_scrollbar.pack(side='right', fill='y')
        
        # Progress
        progress_frame = ttk.Frame(self.dialog)
        progress_frame.pack(fill='x', padx=20, pady=10)
        
        self.progress_var = tk.StringVar(value="Ready to commit")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(side='left')
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(side='right', fill='x', expand=True, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="📤 Start Bulk Commit", 
                  command=self.start_bulk_commit).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side='right')
    
    def start_bulk_commit(self):
        """Start the bulk commit process."""
        commit_msg = self.commit_msg_var.get().strip()
        if not commit_msg:
            messagebox.showerror("Invalid Input", "Please enter a commit message.")
            return
        
        self.progress_bar.config(maximum=len(self.completed_repos))
        self.progress_bar['value'] = 0
        
        success_count = 0
        total_count = len(self.completed_repos)
        
        for i, (repo_name, repo_data) in enumerate(self.completed_repos.items()):
            self.progress_var.set(f"Committing {repo_name}...")
            self.progress_bar['value'] = i
            self.dialog.update()
            
            try:
                # Update tree status
                self.commit_tree.set(repo_name, 'status', '🔄 Committing...')
                self.dialog.update()
                
                # Simulate commit (in real implementation, this would use the actual commit logic)
                result = self._commit_single_repo(repo_name, repo_data, commit_msg)
                
                if result:
                    self.commit_tree.set(repo_name, 'status', '✅ Committed')
                    success_count += 1
                else:
                    self.commit_tree.set(repo_name, 'status', '❌ Failed')
                
            except Exception as e:
                self.commit_tree.set(repo_name, 'status', '❌ Error')
                if not self.skip_errors_var.get():
                    messagebox.showerror("Commit Error", f"Failed to commit {repo_name}: {str(e)}")
                    break
        
        self.progress_bar['value'] = total_count
        self.progress_var.set(f"Completed: {success_count}/{total_count} repositories")
        
        self.success = success_count > 0
        self.success_count = success_count
        
        # Auto-close after showing results
        self.dialog.after(2000, self.dialog.destroy)
    
    def _commit_single_repo(self, repo_name, repo_data, commit_msg):
        """Commit README for a single repository."""
        try:
            # Get repository info and README content
            repo_info = repo_data.get('repository_info')
            readme_content = repo_data.get('readme_content', '')
            
            if not repo_info or not readme_content:
                return False
            
            # For now, use direct GitHub API commit (requires authentication)
            return self._commit_to_github_direct(repo_info, readme_content, commit_msg)
            
        except Exception as e:
            self.logger.error(f"Bulk commit failed for {repo_name}: {e}")
            return False
    
    def _commit_to_github_direct(self, repo_info, readme_content, commit_msg):
        """Direct commit to GitHub repository using API."""
        try:
            # Get GitHub token
            github_token = self._get_github_token()
            if not github_token:
                return False
            
            from github import Github
            
            # Initialize GitHub client
            github_client = Github(github_token)
            repo = github_client.get_repo(repo_info.full_name)
            
            # Check if README.md already exists
            try:
                existing_file = repo.get_contents("README.md", ref="main")
                # Update existing file
                repo.update_file(
                    path="README.md",
                    message=commit_msg,
                    content=readme_content,
                    sha=existing_file.sha,
                    branch="main"
                )
            except:
                # Create new file
                repo.create_file(
                    path="README.md",
                    message=commit_msg,
                    content=readme_content,
                    branch="main"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"GitHub commit failed for {repo_info.full_name}: {e}")
            return False
    
    def _get_github_token(self):
        """Get GitHub token from config or prompt user."""
        try:
            # Try to get from saved config
            config_path = os.path.expanduser("~/.reporeadme/github_token.txt")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        return token
        except:
            pass
        
        # If no token available, show warning
        messagebox.showwarning("Authentication Required", 
                             "GitHub token required for commits. Please set up authentication in the main GUI first.")
        return None
    
    def cancel(self):
        """Cancel the bulk commit dialog."""
        self.dialog.destroy()


class ReadmePreviewDialog:
    """Dialog for previewing README content with syntax highlighting."""
    
    def __init__(self, parent, repo_name, readme_content):
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"👁️ README Preview: {repo_name}")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 450
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 350
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets(repo_name, readme_content)
    
    def create_widgets(self, repo_name, readme_content):
        """Create preview widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(header_frame, text=f"📄 README Preview: {repo_name}", 
                 font=('Arial', 12, 'bold')).pack(side='left')
        
        # Stats
        stats_frame = ttk.Frame(header_frame)
        stats_frame.pack(side='right')
        
        char_count = len(readme_content)
        line_count = readme_content.count('\n') + 1
        ttk.Label(stats_frame, text=f"Lines: {line_count} | Characters: {char_count:,}",
                 font=('Arial', 9)).pack()
        
        # Actions
        actions_frame = ttk.Frame(self.dialog)
        actions_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        ttk.Button(actions_frame, text="📋 Copy to Clipboard", 
                  command=lambda: self.copy_to_clipboard(readme_content)).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="💾 Save As...", 
                  command=lambda: self.save_as(repo_name, readme_content)).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="❌ Close", 
                  command=self.dialog.destroy).pack(side='right')
        
        # Preview area with enhanced styling
        preview_frame = ttk.Frame(self.dialog)
        preview_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            font=('Consolas', 10),
            wrap=tk.WORD,
            bg='#f8f9fa',
            fg='#24292f',
            insertbackground='#24292f',
            selectbackground='#0969da',
            selectforeground='white'
        )
        self.preview_text.pack(fill='both', expand=True)
        
        # Insert content with basic syntax highlighting
        self.preview_text.insert('1.0', readme_content)
        self._apply_basic_highlighting()
        
        # Make read-only
        self.preview_text.config(state='disabled')
    
    def _apply_basic_highlighting(self):
        """Apply basic markdown syntax highlighting."""
        content = self.preview_text.get('1.0', tk.END)
        
        # Configure tags
        self.preview_text.tag_configure("h1", font=('Consolas', 14, 'bold'), foreground='#1f2328')
        self.preview_text.tag_configure("h2", font=('Consolas', 12, 'bold'), foreground='#1f2328')
        self.preview_text.tag_configure("bold", font=('Consolas', 10, 'bold'))
        self.preview_text.tag_configure("code", font=('Consolas', 9), background='#f6f8fa', foreground='#d73a49')
        self.preview_text.tag_configure("link", foreground='#0969da', underline=True)
        
        # Apply highlighting (basic implementation)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line_start = f"{i}.0"
            line_end = f"{i}.end"
            
            if line.strip().startswith('# '):
                self.preview_text.tag_add("h1", line_start, line_end)
            elif line.strip().startswith('## '):
                self.preview_text.tag_add("h2", line_start, line_end)
    
    def copy_to_clipboard(self, content):
        """Copy README content to clipboard."""
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(content)
        self.dialog.update()
        messagebox.showinfo("Copied", "README content copied to clipboard!")
    
    def save_as(self, repo_name, content):
        """Save README content to file."""
        safe_name = re.sub(r'[^\w\-_.]', '_', repo_name.replace('/', '_'))
        file_path = filedialog.asksaveasfilename(
            title="Save README As",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")],
            initialfile=f"{safe_name}_README.md"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"README saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")


def create_bulk_analyzer(parent):
    """Create and show the bulk analyzer dialog."""
    return BulkAnalyzerDialog(parent)