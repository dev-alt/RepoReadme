#!/usr/bin/env python3
"""
Unified RepoReadme GUI

Centralized tab-based interface that integrates all features:
- GitHub data fetching and management
- README generation
- CV creation
- LinkedIn optimization
- Profile building
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import asyncio
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from .github_data_manager import GitHubDataManager, GitHubUserData
    from .analyzers.repository_analyzer import RepositoryAnalyzer
    from .templates.readme_templates import ReadmeTemplateEngine
    from .cv_generator import CVGenerator, CVConfig
    from .linkedin_generator import LinkedInGenerator, LinkedInConfig
    from .utils.logger import get_logger
    from .config.settings import SettingsManager
except ImportError:
    from github_data_manager import GitHubDataManager, GitHubUserData
    from analyzers.repository_analyzer import RepositoryAnalyzer
    from templates.readme_templates import ReadmeTemplateEngine
    from cv_generator import CVGenerator, CVConfig
    from linkedin_generator import LinkedInGenerator, LinkedInConfig
    from utils.logger import get_logger
    from config.settings import SettingsManager


class UnifiedRepoReadmeGUI:
    """Unified GUI application combining all RepoReadme features."""
    
    def __init__(self):
        """Initialize the unified GUI."""
        self.root = tk.Tk()
        self.root.title("RepoReadme - Professional Developer Suite")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Initialize components
        self.logger = get_logger()
        self.github_manager = GitHubDataManager()
        self.analyzer = RepositoryAnalyzer()
        self.template_engine = ReadmeTemplateEngine()
        self.settings_manager = SettingsManager()
        
        # State variables
        self.current_user_data: Optional[GitHubUserData] = None
        self.is_fetching_data = False
        self.current_task_thread: Optional[threading.Thread] = None
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.load_settings()
        
        # Set up progress callback
        self.github_manager.set_progress_callback(self.update_progress)
        
        self.logger.info("Unified RepoReadme GUI initialized")
    
    def setup_styles(self):
        """Configure GUI styles."""
        style = ttk.Style()
        
        # Main styles
        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'), foreground='#2c3e50')
        style.configure('Subheader.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#34495e')
        style.configure('Action.TButton', font=('Segoe UI', 10))
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))
        
        # Tab styles
        style.configure('Tab.TNotebook', tabposition='n')
        style.configure('Tab.TNotebook.Tab', padding=[20, 10])
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header section
        self.create_header(main_frame)
        
        # Main notebook for tabs
        self.notebook = ttk.Notebook(main_frame, style='Tab.TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Create all tabs
        self.create_connect_tab()
        self.create_scan_tab()
        self.create_readme_tab()
        self.create_cv_tab()
        self.create_linkedin_tab()
        self.create_export_tab()
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """Create the application header."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Title and description
        title_label = ttk.Label(header_frame, text="RepoReadme Professional Suite", 
                               style='Header.TLabel')
        title_label.pack(anchor='w')
        
        desc_label = ttk.Label(header_frame, 
                              text="Unified platform for GitHub analysis, README generation, CV creation, and LinkedIn optimization")
        desc_label.pack(anchor='w', pady=(2, 0))
        
        # Connection status
        self.connection_status_var = tk.StringVar(value="Not connected to GitHub")
        status_label = ttk.Label(header_frame, textvariable=self.connection_status_var,
                                foreground='#7f8c8d', font=('Segoe UI', 9))
        status_label.pack(anchor='w', pady=(5, 0))
    
    def create_connect_tab(self):
        """Create the GitHub connection and data fetching tab."""
        connect_frame = ttk.Frame(self.notebook)
        self.notebook.add(connect_frame, text="🔗 Connect")
        
        # Connection section
        conn_frame = ttk.LabelFrame(connect_frame, text="GitHub Connection", padding=20)
        conn_frame.pack(fill='x', padx=20, pady=20)
        
        # Username input
        username_frame = ttk.Frame(conn_frame)
        username_frame.pack(fill='x', pady=10)
        
        ttk.Label(username_frame, text="GitHub Username:", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(username_frame, textvariable=self.username_var, font=('Segoe UI', 11))
        username_entry.pack(fill='x', pady=(5, 0))
        
        # Token input (optional)
        token_frame = ttk.Frame(conn_frame)
        token_frame.pack(fill='x', pady=10)
        
        ttk.Label(token_frame, text="GitHub Token (optional - for private repos):", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(token_frame, textvariable=self.token_var, show='*', font=('Segoe UI', 11))
        token_entry.pack(fill='x', pady=(5, 0))
        
        # Test connection button
        test_button = ttk.Button(conn_frame, text="🔍 Test Connection", 
                               command=self.test_github_connection, style='Action.TButton')
        test_button.pack(pady=10)
        
        # Data scope selection
        scope_frame = ttk.LabelFrame(connect_frame, text="Data Scope", padding=20)
        scope_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.scope_var = tk.StringVar(value="public")
        scope_options = [
            ("public", "Public Repositories Only", "Analyze all public repositories"),
            ("all", "All Repositories", "Analyze all repositories (requires token)"),
            ("single", "README Analysis Only", "Quick analysis for README generation")
        ]
        
        for value, text, description in scope_options:
            frame = ttk.Frame(scope_frame)
            frame.pack(fill='x', pady=5)
            
            radio = ttk.Radiobutton(frame, text=text, variable=self.scope_var, value=value)
            radio.pack(anchor='w')
            
            desc_label = ttk.Label(frame, text=description, foreground='#7f8c8d', font=('Segoe UI', 9))
            desc_label.pack(anchor='w', padx=(25, 0))
        
        # Download options
        download_frame = ttk.LabelFrame(connect_frame, text="Download Options", padding=20)
        download_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.download_files_var = tk.BooleanVar(value=False)
        download_check = ttk.Checkbutton(download_frame, text="Download repository files locally", 
                                       variable=self.download_files_var)
        download_check.pack(anchor='w')
        
        download_desc = ttk.Label(download_frame, 
                                 text="Downloads all repository files for offline analysis (slower but more comprehensive)",
                                 foreground='#7f8c8d', font=('Segoe UI', 9), wraplength=600)
        download_desc.pack(anchor='w', padx=(25, 0), pady=(2, 0))
        
        # Fetch data button
        self.fetch_button = ttk.Button(connect_frame, text="🚀 Fetch GitHub Data", 
                                     command=self.fetch_github_data, style='Primary.TButton')
        self.fetch_button.pack(pady=20)
        
        # Progress section
        progress_frame = ttk.LabelFrame(connect_frame, text="Progress")
        progress_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.progress_var = tk.StringVar(value="Ready to fetch GitHub data")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill='x', padx=10, pady=(0, 5))
        
        # Detailed progress log
        progress_log_frame = ttk.Frame(progress_frame)
        progress_log_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        
        self.progress_log = scrolledtext.ScrolledText(progress_log_frame, height=8, width=70,
                                                     font=('Consolas', 9), state='disabled')
        self.progress_log.pack(fill='both', expand=True)
    
    def create_scan_tab(self):
        """Create the repository scanning and analysis tab."""
        scan_frame = ttk.Frame(self.notebook)
        self.notebook.add(scan_frame, text="📊 Analyze")
        
        # User info section
        user_info_frame = ttk.LabelFrame(scan_frame, text="User Information", padding=20)
        user_info_frame.pack(fill='x', padx=20, pady=20)
        
        self.user_info_text = tk.Text(user_info_frame, height=6, wrap=tk.WORD, 
                                     font=('Consolas', 10), state='disabled')
        self.user_info_text.pack(fill='x')
        
        # Repository overview
        repos_frame = ttk.LabelFrame(scan_frame, text="Repository Overview", padding=20)
        repos_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Repository list with details
        columns = ('name', 'language', 'stars', 'forks', 'size', 'updated')
        self.repo_tree = ttk.Treeview(repos_frame, columns=columns, show='tree headings', height=15)
        
        # Define column headings
        self.repo_tree.heading('#0', text='Repository')
        self.repo_tree.heading('name', text='Name')
        self.repo_tree.heading('language', text='Language') 
        self.repo_tree.heading('stars', text='Stars')
        self.repo_tree.heading('forks', text='Forks')
        self.repo_tree.heading('size', text='Size (KB)')
        self.repo_tree.heading('updated', text='Updated')
        
        # Column widths
        self.repo_tree.column('#0', width=50)
        self.repo_tree.column('name', width=200)
        self.repo_tree.column('language', width=100)
        self.repo_tree.column('stars', width=80)
        self.repo_tree.column('forks', width=80)
        self.repo_tree.column('size', width=100)
        self.repo_tree.column('updated', width=120)
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(repos_frame, orient='vertical', command=self.repo_tree.yview)
        self.repo_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Pack tree and scrollbar
        tree_frame = ttk.Frame(repos_frame)
        tree_frame.pack(fill='both', expand=True)
        
        self.repo_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Repository details
        details_frame = ttk.LabelFrame(scan_frame, text="Repository Details")
        details_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.repo_details_text = tk.Text(details_frame, height=8, wrap=tk.WORD,
                                        font=('Consolas', 9), state='disabled')
        self.repo_details_text.pack(fill='x', padx=10, pady=10)
        
        # Bind tree selection
        self.repo_tree.bind('<<TreeviewSelect>>', self.on_repo_select)
    
    def create_readme_tab(self):
        """Create the README generation tab."""
        readme_frame = ttk.Frame(self.notebook)
        self.notebook.add(readme_frame, text="📝 README")
        
        # Repository selection for README
        selection_frame = ttk.LabelFrame(readme_frame, text="Repository Selection", padding=15)
        selection_frame.pack(fill='x', padx=20, pady=20)
        
        self.readme_repo_var = tk.StringVar()
        self.readme_repo_combo = ttk.Combobox(selection_frame, textvariable=self.readme_repo_var,
                                             state='readonly', width=50)
        self.readme_repo_combo.pack(fill='x')
        
        # Template selection
        template_frame = ttk.LabelFrame(readme_frame, text="Template Configuration", padding=15)
        template_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        template_row = ttk.Frame(template_frame)
        template_row.pack(fill='x', pady=10)
        
        ttk.Label(template_row, text="Template:").pack(side='left')
        self.template_var = tk.StringVar(value="modern")
        template_combo = ttk.Combobox(template_row, textvariable=self.template_var,
                                     values=['modern', 'classic', 'minimalist', 'developer', 'academic', 'corporate'],
                                     state='readonly', width=20)
        template_combo.pack(side='left', padx=10)
        
        # Generate README button
        generate_readme_btn = ttk.Button(template_frame, text="📝 Generate README",
                                        command=self.generate_readme, style='Primary.TButton')
        generate_readme_btn.pack(pady=10)
        
        # README preview
        preview_frame = ttk.LabelFrame(readme_frame, text="README Preview")
        preview_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.readme_preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD,
                                                       font=('Consolas', 10))
        self.readme_preview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # README actions
        readme_actions = ttk.Frame(readme_frame)
        readme_actions.pack(fill='x', padx=20, pady=(0, 20))
        
        ttk.Button(readme_actions, text="💾 Save README", 
                  command=self.save_readme).pack(side='left', padx=5)
        ttk.Button(readme_actions, text="📋 Copy to Clipboard", 
                  command=self.copy_readme).pack(side='left', padx=5)
        ttk.Button(readme_actions, text="🔄 Regenerate", 
                  command=self.generate_readme).pack(side='right', padx=5)
    
    def create_cv_tab(self):
        """Create the CV generation tab."""
        cv_frame = ttk.Frame(self.notebook)
        self.notebook.add(cv_frame, text="📄 CV")
        
        # CV configuration
        config_frame = ttk.LabelFrame(cv_frame, text="CV Configuration", padding=15)
        config_frame.pack(fill='x', padx=20, pady=20)
        
        # CV style selection
        style_row = ttk.Frame(config_frame)
        style_row.pack(fill='x', pady=5)
        
        ttk.Label(style_row, text="CV Style:").pack(side='left')
        self.cv_style_var = tk.StringVar(value="modern")
        cv_style_combo = ttk.Combobox(style_row, textvariable=self.cv_style_var,
                                     values=['modern', 'classic', 'minimal', 'technical', 'creative'],
                                     state='readonly', width=15)
        cv_style_combo.pack(side='left', padx=10)
        
        # Target role
        role_row = ttk.Frame(config_frame)
        role_row.pack(fill='x', pady=5)
        
        ttk.Label(role_row, text="Target Role:").pack(side='left')
        self.cv_target_role_var = tk.StringVar()
        role_entry = ttk.Entry(role_row, textvariable=self.cv_target_role_var, width=25)
        role_entry.pack(side='left', padx=10)
        
        # Generate CV button
        generate_cv_btn = ttk.Button(config_frame, text="📄 Generate CV",
                                    command=self.generate_cv, style='Primary.TButton')
        generate_cv_btn.pack(pady=10)
        
        # CV preview
        cv_preview_frame = ttk.LabelFrame(cv_frame, text="CV Preview")
        cv_preview_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.cv_preview = scrolledtext.ScrolledText(cv_preview_frame, wrap=tk.WORD,
                                                   font=('Arial', 10))
        self.cv_preview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # CV actions
        cv_actions = ttk.Frame(cv_frame)
        cv_actions.pack(fill='x', padx=20, pady=(0, 20))
        
        ttk.Button(cv_actions, text="💾 Export HTML", 
                  command=self.export_cv_html).pack(side='left', padx=5)
        ttk.Button(cv_actions, text="📄 Export PDF", 
                  command=self.export_cv_pdf).pack(side='left', padx=5)
        ttk.Button(cv_actions, text="🌐 Preview in Browser", 
                  command=self.preview_cv).pack(side='right', padx=5)
    
    def create_linkedin_tab(self):
        """Create the LinkedIn optimization tab."""
        linkedin_frame = ttk.Frame(self.notebook)
        self.notebook.add(linkedin_frame, text="💼 LinkedIn")
        
        # LinkedIn configuration
        config_frame = ttk.LabelFrame(linkedin_frame, text="LinkedIn Configuration", padding=15)
        config_frame.pack(fill='x', padx=20, pady=20)
        
        # Tone and length
        tone_row = ttk.Frame(config_frame)
        tone_row.pack(fill='x', pady=5)
        
        ttk.Label(tone_row, text="Tone:").pack(side='left')
        self.linkedin_tone_var = tk.StringVar(value="professional")
        tone_combo = ttk.Combobox(tone_row, textvariable=self.linkedin_tone_var,
                                 values=['professional', 'approachable', 'authoritative', 'creative'],
                                 state='readonly', width=15)
        tone_combo.pack(side='left', padx=10)
        
        ttk.Label(tone_row, text="Length:").pack(side='left', padx=(20, 0))
        self.linkedin_length_var = tk.StringVar(value="medium")
        length_combo = ttk.Combobox(tone_row, textvariable=self.linkedin_length_var,
                                   values=['short', 'medium', 'long'],
                                   state='readonly', width=10)
        length_combo.pack(side='left', padx=10)
        
        # Target role
        target_row = ttk.Frame(config_frame)
        target_row.pack(fill='x', pady=5)
        
        ttk.Label(target_row, text="Target Role:").pack(side='left')
        self.linkedin_target_role_var = tk.StringVar()
        target_entry = ttk.Entry(target_row, textvariable=self.linkedin_target_role_var, width=25)
        
        # Initialize portfolio variables
        self.portfolio_style_var = tk.StringVar(value="modern")
        self.portfolio_dark_mode_var = tk.BooleanVar(value=False)
        target_entry.pack(side='left', padx=10)
        
        # Generate LinkedIn content button
        generate_linkedin_btn = ttk.Button(config_frame, text="💼 Generate LinkedIn Content",
                                          command=self.generate_linkedin, style='Primary.TButton')
        generate_linkedin_btn.pack(pady=10)
        
        # LinkedIn content notebook
        self.linkedin_notebook = ttk.Notebook(linkedin_frame)
        self.linkedin_notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Headline tab
        headline_frame = ttk.Frame(self.linkedin_notebook)
        self.linkedin_notebook.add(headline_frame, text="📢 Headline")
        
        self.headline_text = scrolledtext.ScrolledText(headline_frame, height=4, wrap=tk.WORD,
                                                      font=('Arial', 11, 'bold'))
        self.headline_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Summary tab
        summary_frame = ttk.Frame(self.linkedin_notebook)
        self.linkedin_notebook.add(summary_frame, text="📄 Summary")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD,
                                                     font=('Arial', 10))
        self.summary_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Content ideas tab
        ideas_frame = ttk.Frame(self.linkedin_notebook)
        self.linkedin_notebook.add(ideas_frame, text="💡 Content Ideas")
        
        self.ideas_text = scrolledtext.ScrolledText(ideas_frame, wrap=tk.WORD,
                                                   font=('Arial', 10))
        self.ideas_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Preview tab
        preview_frame = ttk.Frame(self.linkedin_notebook)
        self.linkedin_notebook.add(preview_frame, text="👁️ Preview")
        
        self.linkedin_preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD,
                                                         font=('Consolas', 9))
        self.linkedin_preview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # LinkedIn actions
        linkedin_actions = ttk.Frame(linkedin_frame)
        linkedin_actions.pack(fill='x', padx=20, pady=(0, 20))
        
        ttk.Button(linkedin_actions, text="💾 Export Guide", 
                  command=self.export_linkedin_guide).pack(side='left', padx=5)
        ttk.Button(linkedin_actions, text="📋 Copy Current Tab", 
                  command=self.copy_linkedin_content).pack(side='left', padx=5)
    
    def create_export_tab(self):
        """Create the export and portfolio tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="💾 Export")
        
        # Portfolio generation
        portfolio_frame = ttk.LabelFrame(export_frame, text="GitHub Portfolio", padding=20)
        portfolio_frame.pack(fill='x', padx=20, pady=20)
        
        portfolio_desc = ttk.Label(portfolio_frame, 
                                  text="Generate a comprehensive HTML portfolio showcasing all your GitHub projects",
                                  font=('Segoe UI', 10))
        portfolio_desc.pack(anchor='w', pady=(0, 10))
        
        portfolio_btn_frame = ttk.Frame(portfolio_frame)
        portfolio_btn_frame.pack(fill='x', pady=5)
        
        generate_portfolio_btn = ttk.Button(portfolio_btn_frame, text="🚀 Generate Portfolio",
                                           command=self.generate_portfolio, style='Primary.TButton')
        generate_portfolio_btn.pack(side='left', padx=(0, 10))
        
        export_portfolio_btn = ttk.Button(portfolio_btn_frame, text="📥 Export Portfolio",
                                         command=self.export_portfolio, style='Action.TButton')
        export_portfolio_btn.pack(side='left')
        
        # Bulk export options
        bulk_frame = ttk.LabelFrame(export_frame, text="Bulk Export", padding=20)
        bulk_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        export_options = [
            ("All README files", self.export_all_readmes),
            ("Complete CV package", self.export_cv_package),
            ("LinkedIn optimization guide", self.export_linkedin_package),
            ("Full project archive", self.export_full_archive)
        ]
        
        for text, command in export_options:
            btn = ttk.Button(bulk_frame, text=text, command=command, style='Action.TButton')
            btn.pack(fill='x', pady=2)
        
        # Export status
        status_frame = ttk.LabelFrame(export_frame, text="Export Log")
        status_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.export_log = scrolledtext.ScrolledText(status_frame, height=10, wrap=tk.WORD,
                                                   font=('Consolas', 9))
        self.export_log.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_status_bar(self, parent):
        """Create status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                relief='sunken', anchor='w')
        status_label.pack(fill='x', side='left')
        
        # Connection indicator
        self.connection_indicator = ttk.Label(status_frame, text="●", foreground='red')
        self.connection_indicator.pack(side='right', padx=(0, 5))
    
    def test_github_connection(self):
        """Test GitHub connection."""
        username = self.username_var.get().strip()
        token = self.token_var.get().strip()
        
        if not username:
            messagebox.showwarning("Missing Username", "Please enter a GitHub username.")
            return
        
        try:
            if token:
                self.github_manager.set_github_token(token)
            else:
                self.github_manager.set_username_only(username)
            
            self.connection_status_var.set(f"✅ Connected to GitHub - {username}")
            self.connection_indicator.configure(foreground='green')
            messagebox.showinfo("Connection Success", f"Successfully connected to GitHub for user: {username}")
            
            # Auto-save connection details
            self.save_settings()
            
        except Exception as e:
            self.connection_status_var.set("❌ Connection failed")
            self.connection_indicator.configure(foreground='red')
            messagebox.showerror("Connection Failed", f"Failed to connect to GitHub:\n{str(e)}")
    
    def fetch_github_data(self):
        """Fetch GitHub data in background thread."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Missing Username", "Please enter a GitHub username.")
            return
        
        if self.is_fetching_data:
            return
        
        # Check for cached data first
        cached_data = self.github_manager.get_cached_user_data(username)
        if cached_data:
            response = messagebox.askyesnocancel(
                "Cached Data Found", 
                f"Found cached data for {username} from {cached_data.updated_at[:10]}.\n\n"
                f"• Repositories: {len(cached_data.repositories)}\n"
                f"• Profile: {cached_data.name or 'Available'}\n\n"
                f"Use cached data (Yes) or refresh from GitHub (No)?"
            )
            
            if response is True:  # Use cached data
                self.current_user_data = cached_data
                
                # Rebuild profile data if missing (needed for CV/LinkedIn generation)
                if not cached_data.profile_data:
                    try:
                        self.progress_log.config(state='normal')
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.progress_log.insert(tk.END, f"[{timestamp}] 🔄 Rebuilding profile data for CV/LinkedIn generation...\n")
                        self.progress_log.see(tk.END)
                        self.progress_log.config(state='disabled')
                        self.root.update_idletasks()
                        
                        # Import GitHubProfile for profile building
                        from profile_builder import GitHubProfile
                        
                        # Create basic profile from cached user data
                        profile = GitHubProfile()
                        profile.username = cached_data.username
                        profile.name = cached_data.name
                        profile.email = cached_data.email
                        profile.bio = cached_data.bio
                        profile.location = cached_data.location
                        profile.website = cached_data.website
                        profile.avatar_url = cached_data.avatar_url
                        profile.total_repositories = len(cached_data.repositories)
                        profile.total_stars_received = cached_data.total_stars
                        profile.followers = cached_data.followers
                        profile.following = cached_data.following
                        
                        # Basic language analysis from repositories
                        languages = {}
                        for repo in cached_data.repositories:
                            if repo.languages:
                                for lang, bytes_count in repo.languages.items():
                                    languages[lang] = languages.get(lang, 0) + bytes_count
                        
                        # Convert to percentages
                        if languages:
                            total_bytes = sum(languages.values())
                            profile.languages_used = {lang: (bytes_count / total_bytes) * 100 
                                                    for lang, bytes_count in languages.items()}
                            profile.primary_languages = sorted(profile.languages_used.keys(), 
                                                             key=lambda x: profile.languages_used[x], reverse=True)[:5]
                        
                        # Basic project analysis
                        profile.has_web_projects = any('web' in repo.topics or 'html' in str(repo.languages).lower() 
                                                      for repo in cached_data.repositories)
                        profile.has_apis = any('api' in repo.topics or 'rest' in repo.topics 
                                             for repo in cached_data.repositories)
                        profile.has_data_projects = any('data' in repo.topics or 'python' in str(repo.languages).lower()
                                                       for repo in cached_data.repositories)
                        
                        cached_data.profile_data = profile
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to rebuild profile data: {e}")
                
                self._update_scan_tab()
                self._update_readme_combo()  # Update README tab repository list
                self.status_var.set("✅ Loaded cached GitHub data")
                messagebox.showinfo("Cache Loaded", "Cached data loaded successfully! All tabs are now ready to use.")
                return
            elif response is None:  # Cancel
                return
            # If response is False, continue with fresh fetch
        
        # Disable fetch button
        self.fetch_button.configure(state='disabled', text="🔄 Fetching...")
        self.is_fetching_data = True
        
        # Start background thread
        self.current_task_thread = threading.Thread(
            target=self._fetch_data_worker,
            args=(username, self.scope_var.get(), self.download_files_var.get())
        )
        self.current_task_thread.daemon = True
        self.current_task_thread.start()
    
    def _fetch_data_worker(self, username: str, scope: str, include_files: bool):
        """Worker thread for fetching GitHub data."""
        try:
            # Set up GitHub manager
            token = self.token_var.get().strip()
            if token:
                self.github_manager.set_github_token(token)
            else:
                self.github_manager.set_username_only(username)
            
            # Fetch data
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            user_data = loop.run_until_complete(
                self.github_manager.fetch_user_data(username, scope, include_files)
            )
            
            loop.close()
            
            # Update UI in main thread
            self.root.after(0, lambda: self._fetch_completed(user_data))
            
        except Exception as e:
            self.root.after(0, lambda: self._fetch_failed(str(e)))
    
    def _fetch_completed(self, user_data: GitHubUserData):
        """Handle successful data fetch."""
        self.current_user_data = user_data
        self.is_fetching_data = False
        
        # Update UI
        self.fetch_button.configure(state='normal', text="🚀 Fetch GitHub Data")
        self.connection_indicator.configure(foreground='green')
        self.status_var.set(f"✅ Fetched data for {user_data.username} - {len(user_data.repositories)} repositories")
        
        # Update scan tab
        self._update_scan_tab()
        
        # Update README combo
        self._update_readme_combo()
        
        # Switch to scan tab
        self.notebook.select(1)
        
        messagebox.showinfo("Fetch Complete", 
                           f"Successfully fetched data for {user_data.username}\n"
                           f"Repositories: {len(user_data.repositories)}\n"
                           f"Total stars: {user_data.total_stars}\n"
                           f"Languages: {len(user_data.languages_used)}")
    
    def _fetch_failed(self, error_message: str):
        """Handle failed data fetch."""
        self.is_fetching_data = False
        self.fetch_button.configure(state='normal', text="🚀 Fetch GitHub Data")
        self.connection_indicator.configure(foreground='red')
        self.status_var.set("❌ Fetch failed")
        
        messagebox.showerror("Fetch Failed", f"Failed to fetch GitHub data:\n{error_message}")
    
    def update_progress(self, message: str, progress: int):
        """Update progress display."""
        self.progress_var.set(message)
        self.progress_bar['value'] = progress
        
        # Add to detailed progress log
        self.progress_log.config(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.progress_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.progress_log.see(tk.END)
        self.progress_log.config(state='disabled')
        
        self.root.update_idletasks()
    
    def _update_scan_tab(self):
        """Update the scan tab with fetched data."""
        if not self.current_user_data:
            return
        
        user_data = self.current_user_data
        
        # Update user info
        user_info = f"""GitHub User: {user_data.username}
Name: {user_data.name or 'Not specified'}
Location: {user_data.location or 'Not specified'}
Public Repositories: {user_data.public_repos}
Followers: {user_data.followers} | Following: {user_data.following}
Total Stars Received: {user_data.total_stars}
Account Created: {user_data.created_at[:10]}

Bio: {user_data.bio or 'No bio available'}"""
        
        self.user_info_text.configure(state='normal')
        self.user_info_text.delete('1.0', tk.END)
        self.user_info_text.insert('1.0', user_info)
        self.user_info_text.configure(state='disabled')
        
        # Clear existing tree items
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        # Populate repository tree
        for i, repo in enumerate(user_data.repositories):
            updated_date = repo.updated_at[:10] if repo.updated_at else 'Unknown'
            
            self.repo_tree.insert('', 'end', iid=str(i), text=str(i+1),
                                 values=(repo.name, repo.language, repo.stars, 
                                        repo.forks, repo.size, updated_date))
    
    def _update_readme_combo(self):
        """Update README repository combo box."""
        if not self.current_user_data:
            return
        
        repo_names = [repo.name for repo in self.current_user_data.repositories if not repo.is_fork]
        self.readme_repo_combo.configure(values=repo_names)
        if repo_names:
            self.readme_repo_combo.set(repo_names[0])
    
    def on_repo_select(self, event):
        """Handle repository selection in tree."""
        selection = self.repo_tree.selection()
        if not selection or not self.current_user_data:
            return
        
        repo_index = int(selection[0])
        repo = self.current_user_data.repositories[repo_index]
        
        # Update repository details
        details = f"""Repository: {repo.name}
Description: {repo.description or 'No description'}
Language: {repo.language}
Size: {repo.size} KB
Created: {repo.created_at[:10]}
Updated: {repo.updated_at[:10]}
Stars: {repo.stars} | Forks: {repo.forks} | Watchers: {repo.watchers}

Topics: {', '.join(repo.topics) if repo.topics else 'None'}
License: {repo.license_name or 'None'}

Repository Features:
• README: {'✅' if repo.has_readme else '❌'}
• License: {'✅' if repo.has_license else '❌'}
• Dockerfile: {'✅' if repo.has_dockerfile else '❌'}
• CI/CD: {'✅' if repo.has_ci else '❌'}
• Tests: {'✅' if repo.has_tests else '❌'}
• Private: {'✅' if repo.is_private else '❌'}
• Fork: {'✅' if repo.is_fork else '❌'}
• Archived: {'✅' if repo.is_archived else '❌'}

Languages Used:
{chr(10).join(f'• {lang}: {count:,} bytes' for lang, count in repo.languages.items()) if repo.languages else '• None detected'}

URLs:
• GitHub: {repo.url}
• Clone (HTTPS): {repo.clone_url}
• Clone (SSH): {repo.ssh_url}
"""
        
        if repo.local_path:
            details += f"\nLocal Files: {repo.local_path}"
        
        self.repo_details_text.configure(state='normal')
        self.repo_details_text.delete('1.0', tk.END)
        self.repo_details_text.insert('1.0', details)
        self.repo_details_text.configure(state='disabled')
    
    def generate_readme(self):
        """Generate README for selected repository."""
        if not self.current_user_data:
            messagebox.showwarning("No Data", "Please fetch GitHub data first.")
            return
        
        repo_name = self.readme_repo_var.get()
        if not repo_name:
            messagebox.showwarning("No Repository", "Please select a repository.")
            return
        
        # Find the selected repository
        selected_repo = None
        for repo in self.current_user_data.repositories:
            if repo.name == repo_name:
                selected_repo = repo
                break
        
        if not selected_repo:
            messagebox.showerror("Repository Error", "Selected repository not found.")
            return
        
        try:
            self.status_var.set(f"Generating README for {repo_name}...")
            
            # Create project metadata for the repository
            from analyzers.repository_analyzer import ProjectMetadata
            
            metadata = ProjectMetadata(
                name=selected_repo.name,
                description=selected_repo.description or "",
                primary_language=selected_repo.language or "",
                languages=selected_repo.languages or {},
                topics=selected_repo.topics or [],
                has_docker=selected_repo.has_dockerfile,
                has_ci=selected_repo.has_ci,
                has_tests=selected_repo.has_tests,
                repository_url=selected_repo.url,
                stars_count=selected_repo.stars,
                forks_count=selected_repo.forks,
                created_date=selected_repo.created_at,
                last_updated=selected_repo.updated_at
            )
            
            # Add user context
            metadata.author_name = self.current_user_data.name or self.current_user_data.username
            metadata.author_email = self.current_user_data.email
            
            # Generate README
            from templates.readme_templates import TemplateConfig
            
            template_config = TemplateConfig()
            template_config.template_name = self.template_var.get()
            readme_content = self.template_engine.generate_readme(metadata, template_config)
            
            # Display in preview
            self.readme_preview.delete('1.0', tk.END)
            self.readme_preview.insert('1.0', readme_content)
            
            self.status_var.set(f"✅ README generated for {repo_name}")
            
        except Exception as e:
            self.logger.error(f"README generation failed: {e}")
            messagebox.showerror("Generation Error", f"Failed to generate README:\n{str(e)}")
            self.status_var.set("❌ README generation failed")
    
    def save_readme(self):
        """Save generated README."""
        content = self.readme_preview.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please generate a README first.")
            return
        
        repo_name = self.readme_repo_var.get()
        filename = f"README_{repo_name}.md" if repo_name else "README.md"
        
        file_path = filedialog.asksaveasfilename(
            title="Save README",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.export_log.insert(tk.END, f"✅ README saved: {file_path}\n")
                self.export_log.see(tk.END)
                messagebox.showinfo("Saved", f"README saved successfully to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save README:\n{str(e)}")
    
    def copy_readme(self):
        """Copy README to clipboard."""
        content = self.readme_preview.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please generate a README first.")
            return
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()
            messagebox.showinfo("Copied", "README copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy README:\n{str(e)}")
    
    def generate_cv(self):
        """Generate CV from GitHub profile."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Profile Data", "Please fetch GitHub data first.")
            return
        
        try:
            self.status_var.set("Generating CV...")
            
            # Set up CV configuration
            cv_config = CVConfig()
            cv_config.cv_style = self.cv_style_var.get()
            cv_config.target_role = self.cv_target_role_var.get() or None
            cv_config.include_summary = True
            cv_config.include_skills = True
            cv_config.include_projects = True
            cv_config.include_achievements = True
            cv_config.use_professional_language = True
            
            # Prepare additional info
            additional_info = {
                'name': self.current_user_data.name,
                'email': self.current_user_data.email,
                'location': self.current_user_data.location,
                'website': self.current_user_data.website
            }
            
            # Generate CV
            cv_generator = CVGenerator(cv_config)
            self.current_cv_data = cv_generator.generate_cv_from_profile(
                self.current_user_data.profile_data, additional_info
            )
            
            # Create preview text
            preview_text = self._generate_cv_preview_text()
            
            # Display in preview
            self.cv_preview.delete('1.0', tk.END)
            self.cv_preview.insert('1.0', preview_text)
            
            self.status_var.set("✅ CV generated successfully")
            
        except Exception as e:
            self.logger.error(f"CV generation failed: {e}")
            messagebox.showerror("CV Generation Error", f"Failed to generate CV:\n{str(e)}")
            self.status_var.set("❌ CV generation failed")
    
    def _generate_cv_preview_text(self) -> str:
        """Generate text preview of CV data."""
        if not hasattr(self, 'current_cv_data') or not self.current_cv_data:
            return "No CV data available"
        
        cv = self.current_cv_data
        
        preview = f"""CV PREVIEW - {cv.personal_info.get('name', 'Professional')}
{'='*60}

CONTACT INFORMATION:
{chr(10).join(f'• {k.title()}: {v}' for k, v in cv.personal_info.items() if v)}

PROFESSIONAL SUMMARY:
{cv.professional_summary}

TECHNICAL SKILLS:
"""
        
        for category, skills in cv.technical_skills.items():
            preview += f"{category}:\n  {', '.join(skills[:8])}\n"
        
        preview += f"\nFEATURED PROJECTS ({len(cv.featured_projects)}):\n"
        for project in cv.featured_projects[:5]:
            preview += f"• {project['name']}: {project['description'][:100]}{'...' if len(project['description']) > 100 else ''}\n"
            preview += f"  Technologies: {', '.join(project.get('technologies', [])[:5])}\n"
            if project.get('stars', 0) > 0:
                preview += f"  ⭐ {project['stars']} stars\n"
            preview += "\n"
        
        if cv.work_experience:
            preview += f"WORK EXPERIENCE ({len(cv.work_experience)}):\n"
            for exp in cv.work_experience:
                preview += f"• {exp['title']} at {exp['company']} ({exp['start_date']} - {exp['end_date']})\n"
                preview += f"  {exp['description'][:150]}{'...' if len(exp['description']) > 150 else ''}\n\n"
        
        if cv.achievements:
            preview += f"ACHIEVEMENTS ({len(cv.achievements)}):\n"
            for achievement in cv.achievements[:5]:
                preview += f"• {achievement}\n"
        
        preview += f"\nCV STYLE: {cv.cv_style.title()}"
        if cv.target_role:
            preview += f"\nTARGET ROLE: {cv.target_role}"
        
        return preview
    
    def export_cv_html(self):
        """Export CV as HTML."""
        if not hasattr(self, 'current_cv_data') or not self.current_cv_data:
            messagebox.showwarning("No CV Data", "Please generate a CV first.")
            return
        
        filename = f"CV_{self.current_cv_data.personal_info.get('name', 'Professional').replace(' ', '_')}.html"
        
        file_path = filedialog.asksaveasfilename(
            title="Export CV as HTML",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if file_path:
            try:
                from cv_generator import CVExporter
                exporter = CVExporter(self.current_cv_data)
                exporter.export_to_html(file_path)
                
                self.export_log.insert(tk.END, f"✅ CV HTML exported: {file_path}\n")
                self.export_log.see(tk.END)
                messagebox.showinfo("Export Success", f"CV exported successfully to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export CV:\n{str(e)}")
    
    def export_cv_pdf(self):
        """Export CV as PDF."""
        if not hasattr(self, 'current_cv_data') or not self.current_cv_data:
            messagebox.showwarning("No CV Data", "Please generate a CV first.")
            return
        
        filename = f"CV_{self.current_cv_data.personal_info.get('name', 'Professional').replace(' ', '_')}.pdf"
        
        file_path = filedialog.asksaveasfilename(
            title="Export CV as PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if file_path:
            try:
                from cv_generator import CVExporter
                exporter = CVExporter(self.current_cv_data)
                exporter.export_to_pdf(file_path)
                
                self.export_log.insert(tk.END, f"✅ CV PDF exported: {file_path}\n")
                self.export_log.see(tk.END)
                messagebox.showinfo("Export Success", f"CV exported successfully to:\n{file_path}")
                
            except Exception as e:
                if "No PDF generation method available" in str(e):
                    messagebox.showerror("PDF Export Error", 
                        "PDF generation requires additional software.\n\n"
                        "Please install one of the following:\n"
                        "• WeasyPrint: pip install weasyprint\n"
                        "• Playwright: pip install playwright && playwright install chromium\n"
                        "• wkhtmltopdf: Download from https://wkhtmltopdf.org/\n"
                        "• Google Chrome or Chromium browser")
                else:
                    messagebox.showerror("Export Error", f"Failed to export CV as PDF:\n{str(e)}")
    
    def preview_cv(self):
        """Preview CV in browser."""
        if not hasattr(self, 'current_cv_data') or not self.current_cv_data:
            messagebox.showwarning("No CV Data", "Please generate a CV first.")
            return
        
        try:
            import tempfile
            import webbrowser
            from cv_generator import CVExporter
            
            # Generate HTML content
            exporter = CVExporter(self.current_cv_data)
            html_content = exporter._generate_cv_html()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_file_path = temp_file.name
            
            # Open in browser
            webbrowser.open(f"file://{temp_file_path}")
            
            self.export_log.insert(tk.END, f"✅ CV preview opened in browser\n")
            self.export_log.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview CV:\n{str(e)}")
    
    def generate_linkedin(self):
        """Generate LinkedIn content from GitHub profile."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Profile Data", "Please fetch GitHub data first.")
            return
        
        try:
            self.status_var.set("Generating LinkedIn content...")
            
            # Set up LinkedIn configuration
            linkedin_config = LinkedInConfig()
            linkedin_config.tone = self.linkedin_tone_var.get()
            linkedin_config.target_role = self.linkedin_target_role_var.get() or None
            linkedin_config.content_length = self.linkedin_length_var.get()
            linkedin_config.include_contact_info = True
            linkedin_config.include_skills = True
            linkedin_config.include_achievements = True
            linkedin_config.focus_area = "technology"
            linkedin_config.use_strategic_keywords = True
            
            # Prepare additional info
            additional_info = {
                'name': self.current_user_data.name,
                'email': self.current_user_data.email,
                'location': self.current_user_data.location,
                'website': self.current_user_data.website
            }
            
            # Generate LinkedIn content
            linkedin_generator = LinkedInGenerator(linkedin_config)
            self.current_linkedin_data = linkedin_generator.generate_linkedin_profile(
                self.current_user_data.profile_data, additional_info
            )
            
            # Create preview text
            preview_text = self._generate_linkedin_preview_text()
            
            # Display in preview
            self.linkedin_preview.delete('1.0', tk.END)
            self.linkedin_preview.insert('1.0', preview_text)
            
            self.status_var.set("✅ LinkedIn content generated successfully")
            
        except Exception as e:
            self.logger.error(f"LinkedIn generation failed: {e}")
            messagebox.showerror("LinkedIn Generation Error", f"Failed to generate LinkedIn content:\n{str(e)}")
            self.status_var.set("❌ LinkedIn generation failed")
    
    def _generate_linkedin_preview_text(self) -> str:
        """Generate text preview of LinkedIn data."""
        if not hasattr(self, 'current_linkedin_data') or not self.current_linkedin_data:
            return "No LinkedIn data available"
        
        linkedin = self.current_linkedin_data
        
        # Get name from current user data
        name = self.current_user_data.name if self.current_user_data and self.current_user_data.name else 'Professional'
        preview = f"""LINKEDIN PROFILE PREVIEW - {name}
{'='*60}

PROFESSIONAL HEADLINE:
{linkedin.headline}

ABOUT/SUMMARY:
{linkedin.summary}

SKILLS & EXPERTISE:
"""
        
        if linkedin.skill_categories:
            for category, skills in linkedin.skill_categories.items():
                preview += f"{category.title()}:\n  {', '.join(skills[:10])}\n"
        
        if linkedin.project_descriptions:
            preview += f"\nFEATURED PROJECTS ({len(linkedin.project_descriptions)}):\n"
            for project in linkedin.project_descriptions[:3]:
                preview += f"• {project.get('title', 'Project')}\n"
                preview += f"  {project.get('description', 'No description')[:120]}{'...' if len(project.get('description', '')) > 120 else ''}\n\n"
        
        if linkedin.post_ideas:
            preview += f"CONTENT STRATEGY IDEAS ({len(linkedin.post_ideas)}):\n"
            for idea in linkedin.post_ideas[:5]:
                preview += f"• {idea}\n"
        
        if linkedin.connection_targets:
            preview += f"\nNETWORKING TARGETS:\n"
            for target in linkedin.connection_targets[:3]:
                preview += f"• {target}\n"
        
        if linkedin.profile_improvement_tips:
            preview += f"\nOPTIMIZATION TIPS:\n"
            for tip in linkedin.profile_improvement_tips[:3]:
                preview += f"• {tip}\n"
        
        # Get configuration info if available
        if linkedin.config_used:
            preview += f"\nTONE: {linkedin.config_used.tone.title()}"
            preview += f"\nCONTENT LENGTH: {linkedin.config_used.content_length.title()}"
            if linkedin.config_used.target_role:
                preview += f"\nTARGET ROLE: {linkedin.config_used.target_role}"
        
        return preview
    
    def export_linkedin_guide(self):
        """Export LinkedIn optimization guide."""
        if not hasattr(self, 'current_linkedin_data') or not self.current_linkedin_data:
            messagebox.showwarning("No LinkedIn Data", "Please generate LinkedIn content first.")
            return
        
        name = self.current_user_data.name if self.current_user_data and self.current_user_data.name else 'Professional'
        filename = f"LinkedIn_Guide_{name.replace(' ', '_')}.txt"
        
        file_path = filedialog.asksaveasfilename(
            title="Export LinkedIn Guide",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if file_path:
            try:
                from linkedin_generator import LinkedInExporter
                exporter = LinkedInExporter(self.current_linkedin_data)
                
                # LinkedIn only supports text export
                exporter.export_to_text(file_path)
                
                self.export_log.insert(tk.END, f"✅ LinkedIn guide exported: {file_path}\n")
                self.export_log.see(tk.END)
                messagebox.showinfo("Export Success", f"LinkedIn guide exported successfully to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export LinkedIn guide:\n{str(e)}")
    
    def copy_linkedin_content(self):
        """Copy current LinkedIn content to clipboard."""
        content = self.linkedin_preview.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please generate LinkedIn content first.")
            return
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()
            messagebox.showinfo("Copied", "LinkedIn content copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy LinkedIn content:\n{str(e)}")
    
    def generate_portfolio(self):
        """Generate GitHub portfolio website."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Profile Data", "Please fetch GitHub data first.")
            return
        
        try:
            self.status_var.set("Generating portfolio website...")
            
            # Generate actual portfolio HTML
            portfolio_html = self._generate_portfolio_html()
            
            # Show success message
            messagebox.showinfo("Portfolio Generated", 
                               f"Portfolio generated successfully!\n\n"
                               f"Style: {self.portfolio_style_var.get()}\n"
                               f"Dark Mode: {'Yes' if self.portfolio_dark_mode_var.get() else 'No'}\n"
                               f"Repositories: {len(self.current_user_data.repositories)}\n"
                               f"Content Length: {len(portfolio_html)} characters\n\n"
                               f"Ready for export!")
            
            # Store for export
            self.current_portfolio_html = portfolio_html
            
            self.status_var.set("✅ Portfolio generated successfully")
            
        except Exception as e:
            self.logger.error(f"Portfolio generation failed: {e}")
            messagebox.showerror("Portfolio Generation Error", f"Failed to generate portfolio:\n{str(e)}")
            self.status_var.set("❌ Portfolio generation failed")
    
    def export_portfolio(self):
        """Export generated portfolio HTML to file."""
        if not hasattr(self, 'current_portfolio_html') or not self.current_portfolio_html:
            messagebox.showwarning("No Portfolio", 
                                 "Please generate a portfolio first using the 'Generate Portfolio' button.")
            return
        
        try:
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                title="Save Portfolio",
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
                initialfile=f"{self.current_user_data.username}_portfolio.html"
            )
            
            if filename:
                # Save portfolio HTML to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.current_portfolio_html)
                
                self.status_var.set("✅ Portfolio exported successfully")
                
                messagebox.showinfo("Portfolio Exported", 
                                   f"Portfolio saved successfully!\n\n"
                                   f"📁 Location: {filename}\n"
                                   f"📊 Size: {len(self.current_portfolio_html)} characters\n\n"
                                   f"Open the HTML file in your browser to view your portfolio!")
                
                self.logger.info(f"Portfolio exported to: {filename}")
                
        except Exception as e:
            self.logger.error(f"Portfolio export failed: {e}")
            messagebox.showerror("Export Error", f"Failed to export portfolio:\n{str(e)}")
            self.status_var.set("❌ Portfolio export failed")
    
    def _generate_portfolio_html(self) -> str:
        """Generate a complete HTML portfolio website."""
        user_data = self.current_user_data
        profile_data = user_data.profile_data
        
        # Sort repositories by stars and filter out forks
        repos = [r for r in user_data.repositories if not r.is_fork]
        repos.sort(key=lambda x: x.stars, reverse=True)
        featured_repos = repos[:12]  # Top 12 repositories
        
        # Get user's primary languages
        lang_stats = {}
        for repo in repos:
            if repo.languages:
                for lang, bytes_count in repo.languages.items():
                    lang_stats[lang] = lang_stats.get(lang, 0) + bytes_count
        
        # Convert to percentages and get top languages
        if lang_stats:
            total_bytes = sum(lang_stats.values())
            top_languages = sorted(
                [(lang, (bytes_count / total_bytes) * 100) for lang, bytes_count in lang_stats.items()],
                key=lambda x: x[1], reverse=True
            )[:6]
        else:
            top_languages = []
        
        # Portfolio style configuration
        style = self.portfolio_style_var.get()
        dark_mode = self.portfolio_dark_mode_var.get()
        
        # Color schemes
        if dark_mode:
            bg_color = "#1a1a1a"
            text_color = "#ffffff"
            card_bg = "#2d2d2d"
            accent_color = "#4a9eff"
            border_color = "#404040"
        else:
            bg_color = "#ffffff"
            text_color = "#333333"
            card_bg = "#f8f9fa"
            accent_color = "#007bff"
            border_color = "#dee2e6"
        
        # Generate HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{user_data.name or user_data.username} - Developer Portfolio</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            padding: 60px 0;
            background: linear-gradient(135deg, {accent_color}, #6c5ce7);
            color: white;
            margin-bottom: 40px;
        }}
        
        .profile-img {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            margin: 0 auto 20px;
            background: white;
            padding: 4px;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: {card_bg};
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid {border_color};
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {accent_color};
            display: block;
        }}
        
        .stat-label {{
            font-size: 1rem;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section h2 {{
            font-size: 2rem;
            margin-bottom: 30px;
            color: {accent_color};
            border-bottom: 2px solid {accent_color};
            padding-bottom: 10px;
        }}
        
        .languages {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }}
        
        .language-item {{
            background: {card_bg};
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid {border_color};
        }}
        
        .language-name {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .language-percent {{
            color: {accent_color};
            font-size: 0.9rem;
        }}
        
        .repositories {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
        }}
        
        .repo-card {{
            background: {card_bg};
            padding: 25px;
            border-radius: 10px;
            border: 1px solid {border_color};
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .repo-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .repo-name {{
            font-size: 1.3rem;
            font-weight: bold;
            color: {accent_color};
            text-decoration: none;
            display: block;
            margin-bottom: 10px;
        }}
        
        .repo-description {{
            margin-bottom: 15px;
            opacity: 0.8;
        }}
        
        .repo-stats {{
            display: flex;
            gap: 15px;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
        
        .repo-language {{
            background: {accent_color};
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 0;
            border-top: 1px solid {border_color};
            margin-top: 60px;
            opacity: 0.7;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2rem; }}
            .repositories {{ grid-template-columns: 1fr; }}
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="profile-img" style="background-image: url('{user_data.avatar_url}'); background-size: cover; background-position: center;"></div>
            <h1>{user_data.name or user_data.username}</h1>
            <p>{user_data.bio or "Software Developer"}</p>
            {f'<p>📍 {user_data.location}</p>' if user_data.location else ''}
        </div>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <span class="stat-number">{user_data.public_repos}</span>
                <div class="stat-label">Public Repositories</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{user_data.total_stars}</span>
                <div class="stat-label">Total Stars</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{user_data.followers}</span>
                <div class="stat-label">Followers</div>
            </div>
            <div class="stat-card">
                <span class="stat-number">{len(featured_repos)}</span>
                <div class="stat-label">Featured Projects</div>
            </div>
        </div>
        
        <div class="section">
            <h2>💻 Programming Languages</h2>
            <div class="languages">"""
        
        # Add languages
        for lang, percentage in top_languages:
            html_content += f"""
                <div class="language-item">
                    <div class="language-name">{lang}</div>
                    <div class="language-percent">{percentage:.1f}%</div>
                </div>"""
        
        html_content += """
            </div>
        </div>
        
        <div class="section">
            <h2>🚀 Featured Repositories</h2>
            <div class="repositories">"""
        
        # Add repositories
        for repo in featured_repos:
            repo_desc = repo.description or "No description available"
            if len(repo_desc) > 120:
                repo_desc = repo_desc[:120] + "..."
                
            html_content += f"""
                <div class="repo-card">
                    <a href="{repo.url}" class="repo-name" target="_blank">{repo.name}</a>
                    <div class="repo-description">{repo_desc}</div>
                    <div class="repo-stats">
                        <span>⭐ {repo.stars}</span>
                        <span>🍴 {repo.forks}</span>
                        <span>👁️ {repo.watchers}</span>
                        {f'<span class="repo-language">{repo.language}</span>' if repo.language else ''}
                    </div>
                </div>"""
        
        html_content += f"""
            </div>
        </div>
    </div>
    
    <div class="footer">
        <div class="container">
            <p>Generated with RepoReadme Professional Suite</p>
            <p>Last updated: {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
    def export_all_readmes(self):
        """Export all README files for repositories."""
        if not self.current_user_data or not self.current_user_data.repositories:
            messagebox.showwarning("No Data", "Please fetch GitHub data first.")
            return
        
        folder_path = filedialog.askdirectory(title="Select folder to export READMEs")
        if not folder_path:
            return
        
        try:
            from templates.readme_templates import TemplateConfig
            from analyzers.repository_analyzer import ProjectMetadata
            
            template_config = TemplateConfig()
            template_config.template_name = self.template_var.get()
            
            exported_count = 0
            total_repos = len([r for r in self.current_user_data.repositories if not r.is_fork])
            
            for repo in self.current_user_data.repositories:
                if repo.is_fork:  # Skip forks
                    continue
                
                try:
                    # Create metadata for repository
                    metadata = ProjectMetadata(
                        name=repo.name,
                        description=repo.description or "",
                        primary_language=repo.language or "",
                        languages=repo.languages or {},
                        topics=repo.topics or [],
                        has_docker=repo.has_dockerfile,
                        has_ci=repo.has_ci,
                        has_tests=repo.has_tests,
                        repository_url=repo.url,
                        stars_count=repo.stars,
                        forks_count=repo.forks,
                        created_date=repo.created_at,
                        last_updated=repo.updated_at
                    )
                    
                    # Add user context
                    metadata.author_name = self.current_user_data.name or self.current_user_data.username
                    metadata.author_email = self.current_user_data.email
                    
                    # Generate README
                    readme_content = self.template_engine.generate_readme(metadata, template_config)
                    
                    # Save to file
                    file_path = Path(folder_path) / f"{repo.name}_README.md"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(readme_content)
                    
                    exported_count += 1
                    
                    # Update progress
                    self.export_log.insert(tk.END, f"✅ Exported {repo.name}_README.md\n")
                    self.export_log.see(tk.END)
                    self.root.update_idletasks()
                    
                except Exception as e:
                    self.export_log.insert(tk.END, f"❌ Failed to export {repo.name}: {str(e)}\n")
                    self.export_log.see(tk.END)
            
            messagebox.showinfo("Export Complete", 
                               f"Exported {exported_count}/{total_repos} README files to:\n{folder_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export READMEs:\n{str(e)}")
    
    def export_cv_package(self):
        """Export complete CV package (all styles and formats)."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Data", "Please fetch GitHub data first.")
            return
        
        folder_path = filedialog.askdirectory(title="Select folder to export CV package")
        if not folder_path:
            return
        
        try:
            from cv_generator import CVGenerator, CVConfig, CVExporter
            
            cv_styles = ["modern", "classic", "minimal", "technical", "creative"]
            exported_files = []
            
            for style in cv_styles:
                try:
                    # Create CV config for each style
                    cv_config = CVConfig()
                    cv_config.cv_style = style
                    cv_config.target_role = self.cv_target_role_var.get() or None
                    cv_config.include_summary = True
                    cv_config.include_skills = True
                    cv_config.include_projects = True
                    cv_config.include_achievements = True
                    cv_config.use_professional_language = True
                    
                    # Prepare additional info
                    additional_info = {
                        'name': self.current_user_data.name,
                        'email': self.current_user_data.email,
                        'location': self.current_user_data.location,
                        'website': self.current_user_data.website
                    }
                    
                    # Generate CV
                    cv_generator = CVGenerator(cv_config)
                    cv_data = cv_generator.generate_cv_from_profile(
                        self.current_user_data.profile_data, additional_info
                    )
                    
                    # Export HTML
                    cv_exporter = CVExporter(cv_data)
                    html_file = Path(folder_path) / f"CV_{style.title()}_{self.current_user_data.username}.html"
                    cv_exporter.export_to_html(str(html_file))
                    exported_files.append(str(html_file))
                    
                    # Try to export PDF
                    try:
                        pdf_file = Path(folder_path) / f"CV_{style.title()}_{self.current_user_data.username}.pdf"
                        cv_exporter.export_to_pdf(str(pdf_file))
                        exported_files.append(str(pdf_file))
                    except Exception as pdf_error:
                        self.export_log.insert(tk.END, f"⚠️  PDF export failed for {style}: {str(pdf_error)}\n")
                    
                    self.export_log.insert(tk.END, f"✅ Exported CV {style.title()}\n")
                    self.export_log.see(tk.END)
                    self.root.update_idletasks()
                    
                except Exception as e:
                    self.export_log.insert(tk.END, f"❌ Failed to export {style} CV: {str(e)}\n")
                    self.export_log.see(tk.END)
            
            messagebox.showinfo("CV Package Export Complete", 
                               f"Exported {len(exported_files)} CV files to:\n{folder_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CV package:\n{str(e)}")
    
    def export_linkedin_package(self):
        """Export LinkedIn optimization package."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Data", "Please fetch GitHub data first.")
            return
        
        folder_path = filedialog.askdirectory(title="Select folder to export LinkedIn package")
        if not folder_path:
            return
        
        try:
            from linkedin_generator import LinkedInGenerator, LinkedInConfig, LinkedInExporter
            
            tones = ["professional", "casual", "enthusiastic"]
            lengths = ["short", "medium", "detailed"]
            exported_files = []
            
            for tone in tones:
                for length in lengths:
                    try:
                        # Create LinkedIn config for each combination
                        linkedin_config = LinkedInConfig()
                        linkedin_config.tone = tone
                        linkedin_config.content_length = length
                        linkedin_config.target_role = self.linkedin_target_role_var.get() or None
                        linkedin_config.include_contact_info = True
                        linkedin_config.include_skills = True
                        linkedin_config.include_achievements = True
                        linkedin_config.focus_area = "technology"
                        linkedin_config.use_strategic_keywords = True
                        
                        # Prepare additional info
                        additional_info = {
                            'name': self.current_user_data.name,
                            'email': self.current_user_data.email,
                            'location': self.current_user_data.location,
                            'website': self.current_user_data.website
                        }
                        
                        # Generate LinkedIn content
                        linkedin_generator = LinkedInGenerator(linkedin_config)
                        linkedin_data = linkedin_generator.generate_linkedin_profile(
                            self.current_user_data.profile_data, additional_info
                        )
                        
                        # Export files
                        linkedin_exporter = LinkedInExporter(linkedin_data)
                        
                        # Export text file
                        text_file = Path(folder_path) / f"LinkedIn_{tone.title()}_{length.title()}_{self.current_user_data.username}.txt"
                        linkedin_exporter.export_to_text(str(text_file))
                        exported_files.append(str(text_file))
                        
                        self.export_log.insert(tk.END, f"✅ Exported LinkedIn {tone.title()}-{length.title()}\n")
                        self.export_log.see(tk.END)
                        self.root.update_idletasks()
                        
                    except Exception as e:
                        self.export_log.insert(tk.END, f"❌ Failed to export {tone}-{length} LinkedIn: {str(e)}\n")
                        self.export_log.see(tk.END)
            
            messagebox.showinfo("LinkedIn Package Export Complete", 
                               f"Exported {len(exported_files)} LinkedIn files to:\n{folder_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export LinkedIn package:\n{str(e)}")
    
    def export_full_archive(self):
        """Export complete professional archive with all content."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Data", "Please fetch GitHub data first.")
            return
        
        folder_path = filedialog.askdirectory(title="Select folder to export complete archive")
        if not folder_path:
            return
        
        try:
            # Create timestamped archive folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_folder = Path(folder_path) / f"RepoReadme_Archive_{self.current_user_data.username}_{timestamp}"
            archive_folder.mkdir(exist_ok=True)
            
            total_files = 0
            
            # 1. Export README files
            readme_folder = archive_folder / "READMEs"
            readme_folder.mkdir(exist_ok=True)
            
            self.export_log.insert(tk.END, "📂 Exporting README files...\n")
            self.export_log.see(tk.END)
            self.root.update_idletasks()
            
            from templates.readme_templates import TemplateConfig
            from analyzers.repository_analyzer import ProjectMetadata
            
            template_config = TemplateConfig()
            template_config.template_name = self.template_var.get()
            
            for repo in self.current_user_data.repositories:
                if not repo.is_fork:
                    try:
                        metadata = ProjectMetadata(
                            name=repo.name,
                            description=repo.description or "",
                            primary_language=repo.language or "",
                            languages=repo.languages or {},
                            topics=repo.topics or [],
                            has_docker=repo.has_dockerfile,
                            has_ci=repo.has_ci,
                            has_tests=repo.has_tests,
                            repository_url=repo.url,
                            stars_count=repo.stars,
                            forks_count=repo.forks,
                            created_date=repo.created_at,
                            last_updated=repo.updated_at
                        )
                        
                        metadata.author_name = self.current_user_data.name or self.current_user_data.username
                        metadata.author_email = self.current_user_data.email
                        
                        readme_content = self.template_engine.generate_readme(metadata, template_config)
                        
                        readme_file = readme_folder / f"{repo.name}_README.md"
                        with open(readme_file, 'w', encoding='utf-8') as f:
                            f.write(readme_content)
                        
                        total_files += 1
                    except Exception as e:
                        self.export_log.insert(tk.END, f"⚠️  README export failed for {repo.name}: {str(e)}\n")
            
            # 2. Export CV package
            cv_folder = archive_folder / "CVs"
            cv_folder.mkdir(exist_ok=True)
            
            self.export_log.insert(tk.END, "💼 Exporting CV package...\n")
            self.export_log.see(tk.END)
            self.root.update_idletasks()
            
            try:
                from cv_generator import CVGenerator, CVConfig, CVExporter
                cv_styles = ["modern", "classic", "minimal", "technical", "creative"]
                
                for style in cv_styles:
                    cv_config = CVConfig()
                    cv_config.cv_style = style
                    cv_config.target_role = self.cv_target_role_var.get() or None
                    
                    additional_info = {
                        'name': self.current_user_data.name,
                        'email': self.current_user_data.email,
                        'location': self.current_user_data.location,
                        'website': self.current_user_data.website
                    }
                    
                    cv_generator = CVGenerator(cv_config)
                    cv_data = cv_generator.generate_cv_from_profile(
                        self.current_user_data.profile_data, additional_info
                    )
                    
                    cv_exporter = CVExporter(cv_data)
                    
                    # Export HTML
                    html_file = cv_folder / f"CV_{style.title()}.html"
                    cv_exporter.export_to_html(str(html_file))
                    total_files += 1
                    
                    # Try PDF
                    try:
                        pdf_file = cv_folder / f"CV_{style.title()}.pdf"
                        cv_exporter.export_to_pdf(str(pdf_file))
                        total_files += 1
                    except:
                        pass  # Skip PDF if not available
                        
            except Exception as e:
                self.export_log.insert(tk.END, f"⚠️  CV export failed: {str(e)}\n")
            
            # 3. Export LinkedIn package
            linkedin_folder = archive_folder / "LinkedIn"
            linkedin_folder.mkdir(exist_ok=True)
            
            self.export_log.insert(tk.END, "💼 Exporting LinkedIn package...\n")
            self.export_log.see(tk.END)
            self.root.update_idletasks()
            
            try:
                from linkedin_generator import LinkedInGenerator, LinkedInConfig, LinkedInExporter
                
                linkedin_config = LinkedInConfig()
                linkedin_config.tone = self.linkedin_tone_var.get()
                linkedin_config.content_length = self.linkedin_length_var.get()
                linkedin_config.target_role = self.linkedin_target_role_var.get() or None
                
                additional_info = {
                    'name': self.current_user_data.name,
                    'email': self.current_user_data.email,
                    'location': self.current_user_data.location,
                    'website': self.current_user_data.website
                }
                
                linkedin_generator = LinkedInGenerator(linkedin_config)
                linkedin_data = linkedin_generator.generate_linkedin_profile(
                    self.current_user_data.profile_data, additional_info
                )
                
                linkedin_exporter = LinkedInExporter(linkedin_data)
                
                # Export files
                text_file = linkedin_folder / "LinkedIn_Profile.txt"
                linkedin_exporter.export_to_text(str(text_file))
                total_files += 1
                
            except Exception as e:
                self.export_log.insert(tk.END, f"⚠️  LinkedIn export failed: {str(e)}\n")
            
            # 4. Export user data summary
            summary_file = archive_folder / "Profile_Summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"""GitHub Profile Archive - {self.current_user_data.username}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

USER INFORMATION:
Name: {self.current_user_data.name or 'Not specified'}
Location: {self.current_user_data.location or 'Not specified'}
Email: {self.current_user_data.email or 'Not specified'}
Website: {self.current_user_data.website or 'Not specified'}
Bio: {self.current_user_data.bio or 'No bio available'}

STATISTICS:
Public Repositories: {self.current_user_data.public_repos}
Total Stars Received: {self.current_user_data.total_stars}
Followers: {self.current_user_data.followers}
Following: {self.current_user_data.following}
Account Created: {self.current_user_data.created_at[:10]}

ARCHIVE CONTENTS:
- READMEs/ : README files for all repositories
- CVs/ : Professional CVs in multiple styles
- LinkedIn/ : LinkedIn optimization content
- Profile_Summary.txt : This summary file

Total Files: {total_files + 1}
""")
            total_files += 1
            
            self.export_log.insert(tk.END, f"✅ Archive complete! Total files: {total_files}\n")
            self.export_log.see(tk.END)
            
            messagebox.showinfo("Full Archive Export Complete", 
                               f"Complete professional archive exported!\n\n"
                               f"📁 Location: {archive_folder}\n"
                               f"📊 Total Files: {total_files}\n\n"
                               f"Contents:\n"
                               f"• README files for all repositories\n"
                               f"• CV package (5 styles, HTML/PDF)\n"
                               f"• LinkedIn optimization content\n"
                               f"• Profile summary and statistics")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export full archive:\n{str(e)}")
    
    def load_settings(self):
        """Load application settings."""
        try:
            # Load individual settings
            username = self.settings_manager.get_setting('github_username', '')
            token = self.settings_manager.get_setting('github_token', '')
            cv_style = self.settings_manager.get_setting('cv_style', 'modern')
            linkedin_tone = self.settings_manager.get_setting('linkedin_tone', 'professional')
            
            if username:
                self.username_var.set(username)
            if token:
                self.token_var.set(token)
            if hasattr(self, 'cv_style_var'):
                self.cv_style_var.set(cv_style)
            if hasattr(self, 'linkedin_tone_var'):
                self.linkedin_tone_var.set(linkedin_tone)
                
            self.logger.info("Settings loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save current settings."""
        try:
            settings = {
                'github_username': self.username_var.get(),
                'github_token': self.token_var.get(),
                'cv_style': self.cv_style_var.get(),
                'linkedin_tone': self.linkedin_tone_var.get(),
            }
            
            for key, value in settings.items():
                self.settings_manager.set_setting(key, value)
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
    
    def run(self):
        """Start the GUI application."""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        """Handle application closing."""
        self.save_settings()
        
        # Cancel any running operations
        if self.current_task_thread and self.current_task_thread.is_alive():
            self.is_fetching_data = False
        
        self.root.quit()
        self.root.destroy()


def main():
    """Main entry point for unified GUI."""
    app = UnifiedRepoReadmeGUI()
    app.run()


if __name__ == "__main__":
    main()