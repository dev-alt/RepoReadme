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
    from .readme_to_template_converter import ReadmeToTemplateConverter
    from .utils.logger import get_logger
    from .config.settings import SettingsManager
except ImportError:
    from github_data_manager import GitHubDataManager, GitHubUserData
    from analyzers.repository_analyzer import RepositoryAnalyzer
    from templates.readme_templates import ReadmeTemplateEngine
    from cv_generator import CVGenerator, CVConfig
    from linkedin_generator import LinkedInGenerator, LinkedInConfig
    from ai_linkedin_bio_generator import AILinkedInBioGenerator, AIBioConfig, AIGeneratedBio
    from openrouter_service import OpenRouterAIService, OpenRouterConfig, EnhancementRequest
    from readme_to_template_converter import ReadmeToTemplateConverter
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
        self.template_converter = ReadmeToTemplateConverter()
        self.settings_manager = SettingsManager()
        
        # State variables
        self.current_user_data: Optional[GitHubUserData] = None
        self.is_fetching_data = False
        self.current_task_thread: Optional[threading.Thread] = None
        
        # Sorting state for analyze tab
        self.sort_column = None
        self.sort_reverse = False
        
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
        self.create_ai_bio_tab()
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
        
        # Username entry with save button
        username_input_frame = ttk.Frame(username_frame)
        username_input_frame.pack(fill='x', pady=(5, 0))
        
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(username_input_frame, textvariable=self.username_var, font=('Segoe UI', 11))
        username_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(username_input_frame, text="💾 Save", command=self.save_github_username, 
                  style='Accent.TButton').pack(side='right')
        
        # Token input (optional)
        token_frame = ttk.Frame(conn_frame)
        token_frame.pack(fill='x', pady=10)
        
        ttk.Label(token_frame, text="GitHub Token (optional - for private repos):", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        
        # Token entry with save button
        token_input_frame = ttk.Frame(token_frame)
        token_input_frame.pack(fill='x', pady=(5, 0))
        
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(token_input_frame, textvariable=self.token_var, show='*', font=('Segoe UI', 11))
        token_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(token_input_frame, text="💾 Save", command=self.save_github_token, 
                  style='Accent.TButton').pack(side='right')
        
        # Test connection button
        test_button = ttk.Button(conn_frame, text="🔍 Test Connection", 
                               command=self.test_github_connection, style='Action.TButton')
        test_button.pack(pady=10)
        
        # Credentials status
        creds_status_frame = ttk.Frame(conn_frame)
        creds_status_frame.pack(fill='x', pady=(5, 0))
        
        # Create status labels
        self.username_status_var = tk.StringVar()
        self.token_status_var = tk.StringVar()
        
        status_info_frame = ttk.Frame(creds_status_frame)
        status_info_frame.pack(fill='x')
        
        ttk.Label(status_info_frame, text="💾 Saved Credentials:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        username_status_frame = ttk.Frame(status_info_frame)
        username_status_frame.pack(fill='x', pady=(2, 0))
        
        ttk.Label(username_status_frame, text="Username:", font=('Segoe UI', 8)).pack(side='left')
        self.username_status_label = ttk.Label(username_status_frame, textvariable=self.username_status_var, 
                                              font=('Segoe UI', 8))
        self.username_status_label.pack(side='left', padx=(5, 0))
        
        token_status_frame = ttk.Frame(status_info_frame)
        token_status_frame.pack(fill='x', pady=(1, 0))
        
        ttk.Label(token_status_frame, text="Token:", font=('Segoe UI', 8)).pack(side='left')
        self.token_status_label = ttk.Label(token_status_frame, textvariable=self.token_status_var, 
                                           font=('Segoe UI', 8))
        self.token_status_label.pack(side='left', padx=(5, 0))
        
        # Quick settings links
        quick_links_frame = ttk.LabelFrame(connect_frame, text="Quick Settings", padding=15)
        quick_links_frame.pack(fill='x', padx=20, pady=(10, 0))
        
        links_info = ttk.Label(quick_links_frame, text="💡 Need to configure OpenRouter AI for bio enhancement?", 
                              font=('Segoe UI', 9, 'bold'))
        links_info.pack(anchor='w')
        
        links_desc = ttk.Label(quick_links_frame, 
                              text="Go to the '💼 LinkedIn' tab → OpenRouter AI settings to save your API key",
                              font=('Segoe UI', 9), foreground='#7f8c8d')
        links_desc.pack(anchor='w', pady=(2, 0))
        
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
        
        # Define column headings with sort commands
        self.repo_tree.heading('#0', text='Repository')
        self.repo_tree.heading('name', text='Name ↕', command=lambda: self.sort_repositories('name'))
        self.repo_tree.heading('language', text='Language ↕', command=lambda: self.sort_repositories('language')) 
        self.repo_tree.heading('stars', text='Stars ↕', command=lambda: self.sort_repositories('stars'))
        self.repo_tree.heading('forks', text='Forks ↕', command=lambda: self.sort_repositories('forks'))
        self.repo_tree.heading('size', text='Size (KB) ↕', command=lambda: self.sort_repositories('size'))
        self.repo_tree.heading('updated', text='Updated ↕', command=lambda: self.sort_repositories('updated'))
        
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
    
    def sort_repositories(self, column):
        """Sort repositories by the specified column."""
        if not self.current_user_data or not self.current_user_data.repositories:
            return
        
        # Toggle sort direction if same column, otherwise start with ascending
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Update column headers to show sort direction
        self._update_sort_headers()
        
        # Sort repositories
        repos = self.current_user_data.repositories.copy()
        
        if column == 'name':
            repos.sort(key=lambda r: r.name.lower(), reverse=self.sort_reverse)
        elif column == 'language':
            repos.sort(key=lambda r: (r.language or '').lower(), reverse=self.sort_reverse)
        elif column == 'stars':
            repos.sort(key=lambda r: r.stars or 0, reverse=self.sort_reverse)
        elif column == 'forks':
            repos.sort(key=lambda r: r.forks or 0, reverse=self.sort_reverse)
        elif column == 'size':
            repos.sort(key=lambda r: r.size or 0, reverse=self.sort_reverse)
        elif column == 'updated':
            repos.sort(key=lambda r: r.updated_at or '', reverse=self.sort_reverse)
        
        # Clear and repopulate tree with sorted data
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        for i, repo in enumerate(repos):
            updated_date = repo.updated_at[:10] if repo.updated_at else 'Unknown'
            self.repo_tree.insert('', 'end', iid=str(i), text=str(i+1),
                                 values=(repo.name, repo.language, repo.stars, 
                                        repo.forks, repo.size, updated_date))
        
        # Store sorted repositories for selection handling
        self.current_user_data.repositories = repos
    
    def _update_sort_headers(self):
        """Update column headers to show current sort direction."""
        # Base headers without sort indicators
        headers = {
            'name': 'Name',
            'language': 'Language',
            'stars': 'Stars', 
            'forks': 'Forks',
            'size': 'Size (KB)',
            'updated': 'Updated'
        }
        
        # Update each header
        for col, base_text in headers.items():
            if col == self.sort_column:
                arrow = ' ↓' if self.sort_reverse else ' ↑'
                self.repo_tree.heading(col, text=base_text + arrow)
            else:
                self.repo_tree.heading(col, text=base_text + ' ↕')
    
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
        ttk.Button(readme_actions, text="🎯 Convert to Template", 
                  command=self.convert_to_project_template).pack(side='left', padx=5)
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
    
    def create_ai_bio_tab(self):
        """Create the AI-powered LinkedIn bio generation tab."""
        ai_bio_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_bio_frame, text="🤖 AI Bio")
        
        # Header
        header_frame = ttk.Frame(ai_bio_frame)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        ttk.Label(header_frame, text="🤖 AI LinkedIn Bio Generator",
                 style='Header.TLabel').pack(anchor='w')
        ttk.Label(header_frame, 
                 text="Generate compelling LinkedIn bios using AI analysis of all your repositories",
                 font=('Segoe UI', 10)).pack(anchor='w', pady=(5, 0))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(ai_bio_frame, text="AI Bio Configuration", padding=15)
        config_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Configuration options
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill='x')
        
        # Bio style
        ttk.Label(config_grid, text="Bio Style:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.ai_bio_style = ttk.Combobox(config_grid, width=15, state='readonly')
        self.ai_bio_style['values'] = ('professional', 'creative', 'technical', 'executive', 'startup')
        self.ai_bio_style.set('professional')
        self.ai_bio_style.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        # Tone
        ttk.Label(config_grid, text="Tone:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.ai_bio_tone = ttk.Combobox(config_grid, width=15, state='readonly')
        self.ai_bio_tone['values'] = ('confident', 'humble', 'enthusiastic', 'analytical', 'visionary')
        self.ai_bio_tone.set('confident')
        self.ai_bio_tone.grid(row=0, column=3, sticky='w')
        
        # Length
        ttk.Label(config_grid, text="Length:").grid(row=1, column=0, sticky='w', padx=(0, 10), pady=(10, 0))
        self.ai_bio_length = ttk.Combobox(config_grid, width=15, state='readonly')
        self.ai_bio_length['values'] = ('short', 'medium', 'long')
        self.ai_bio_length.set('medium')
        self.ai_bio_length.grid(row=1, column=1, sticky='w', padx=(0, 20), pady=(10, 0))
        
        # Target role
        ttk.Label(config_grid, text="Target Role:").grid(row=1, column=2, sticky='w', padx=(0, 10), pady=(10, 0))
        self.ai_target_role = ttk.Entry(config_grid, width=20)
        self.ai_target_role.insert(0, "Software Engineer")
        self.ai_target_role.grid(row=1, column=3, sticky='w', pady=(10, 0))
        
        # Experience level (NEW)
        ttk.Label(config_grid, text="Experience Level:").grid(row=2, column=0, sticky='w', padx=(0, 10), pady=(10, 0))
        self.ai_experience_level = ttk.Combobox(config_grid, width=15, state='readonly')
        self.ai_experience_level['values'] = ('recent_graduate', 'junior', 'mid_level', 'senior', 'lead', 'executive')
        self.ai_experience_level.set('recent_graduate')
        self.ai_experience_level.grid(row=2, column=1, sticky='w', padx=(0, 20), pady=(10, 0))
        
        # Years of experience (NEW)
        ttk.Label(config_grid, text="Years Experience:").grid(row=2, column=2, sticky='w', padx=(0, 10), pady=(10, 0))
        self.ai_years_experience = ttk.Spinbox(config_grid, from_=0, to=30, width=10)
        self.ai_years_experience.set("0")
        self.ai_years_experience.grid(row=2, column=3, sticky='w', pady=(10, 0))
        
        # Advanced options
        advanced_frame = ttk.LabelFrame(ai_bio_frame, text="Advanced Options", padding=15)
        advanced_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Checkboxes for advanced features
        self.ai_use_metrics = tk.BooleanVar(value=True)
        self.ai_include_passion = tk.BooleanVar(value=True)
        self.ai_include_cta = tk.BooleanVar(value=True)
        self.ai_emphasize_collaboration = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(advanced_frame, text="Include quantified metrics", 
                       variable=self.ai_use_metrics).pack(anchor='w')
        ttk.Checkbutton(advanced_frame, text="Include passion statement", 
                       variable=self.ai_include_passion).pack(anchor='w')
        ttk.Checkbutton(advanced_frame, text="Include call-to-action", 
                       variable=self.ai_include_cta).pack(anchor='w')
        ttk.Checkbutton(advanced_frame, text="Emphasize collaboration", 
                       variable=self.ai_emphasize_collaboration).pack(anchor='w')
        
        # Add learning mindset option for recent graduates
        self.ai_show_learning_mindset = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Show learning mindset (important for recent graduates)", 
                       variable=self.ai_show_learning_mindset).pack(anchor='w')
        
        # OpenRouter AI Enhancement
        openrouter_frame = ttk.LabelFrame(ai_bio_frame, text="🤖 OpenRouter AI Enhancement", padding=15)
        openrouter_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # OpenRouter configuration
        openrouter_config_frame = ttk.Frame(openrouter_frame)
        openrouter_config_frame.pack(fill='x', pady=(0, 10))
        
        # Enable OpenRouter
        self.openrouter_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(openrouter_config_frame, text="🚀 Enable OpenRouter AI Enhancement", 
                       variable=self.openrouter_enabled, command=self.toggle_openrouter_config).pack(anchor='w')
        
        # OpenRouter settings frame (initially hidden)
        self.openrouter_settings_frame = ttk.Frame(openrouter_frame)
        
        # API Key
        api_key_frame = ttk.Frame(self.openrouter_settings_frame)
        api_key_frame.pack(fill='x', pady=(10, 5))
        
        ttk.Label(api_key_frame, text="API Key:").pack(side='left')
        self.openrouter_api_key = ttk.Entry(api_key_frame, width=40, show="*")
        self.openrouter_api_key.pack(side='left', padx=(10, 5))
        
        ttk.Button(api_key_frame, text="💾 Save", command=self.save_openrouter_key, 
                  style='Action.TButton').pack(side='left', padx=(5, 0))
        ttk.Button(api_key_frame, text="🧪 Test", command=self.test_openrouter_connection, 
                  style='Action.TButton').pack(side='left', padx=(5, 0))
        
        # Model selection
        model_frame = ttk.Frame(self.openrouter_settings_frame)
        model_frame.pack(fill='x', pady=5)
        
        ttk.Label(model_frame, text="Model:").pack(side='left')
        self.openrouter_model = ttk.Combobox(model_frame, width=30, state='readonly')
        self.openrouter_model['values'] = (
            'openai/gpt-3.5-turbo',
            'openai/gpt-4',
            'openai/gpt-4-turbo',
            'anthropic/claude-3-haiku',
            'anthropic/claude-3-sonnet', 
            'anthropic/claude-3-opus',
            'anthropic/claude-sonnet-4.5',
            'meta-llama/llama-3-8b-instruct',
            'meta-llama/llama-3-70b-instruct',
            'deepseek/deepseek-v3.2-exp',
            'google/gemini-2.5-flash'
        )
        self.openrouter_model.set('openai/gpt-3.5-turbo')
        self.openrouter_model.pack(side='left', padx=(10, 10))
        self.openrouter_model.bind('<<ComboboxSelected>>', self.update_model_pricing_display)
        
        # Model info and pricing button
        ttk.Button(model_frame, text="💰 Pricing Info", command=self.show_model_pricing, 
                  style='Action.TButton').pack(side='left', padx=(5, 10))
        
        # Cost estimate display
        self.cost_estimate_label = ttk.Label(model_frame, text="Est: $0.002", foreground='#2c3e50', font=('Segoe UI', 9))
        self.cost_estimate_label.pack(side='left')
        
        ttk.Label(model_frame, text="Temperature:").pack(side='left')
        self.openrouter_temperature = ttk.Scale(model_frame, from_=0.0, to=1.0, orient='horizontal', length=100)
        self.openrouter_temperature.set(0.7)
        self.openrouter_temperature.pack(side='left', padx=(10, 5))
        
        self.temperature_label = ttk.Label(model_frame, text="0.7")
        self.temperature_label.pack(side='left')
        self.openrouter_temperature.configure(command=self.update_temperature_label)
        
        # Enhancement options
        enhancement_frame = ttk.Frame(self.openrouter_settings_frame)
        enhancement_frame.pack(fill='x', pady=5)
        
        self.openrouter_enhance_creativity = tk.BooleanVar(value=True)
        self.openrouter_improve_readability = tk.BooleanVar(value=True)
        self.openrouter_optimize_keywords = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(enhancement_frame, text="🎨 Enhance creativity", 
                       variable=self.openrouter_enhance_creativity).pack(side='left', padx=(0, 10))
        ttk.Checkbutton(enhancement_frame, text="📖 Improve readability", 
                       variable=self.openrouter_improve_readability).pack(side='left', padx=(0, 10))
        ttk.Checkbutton(enhancement_frame, text="🎯 Optimize keywords", 
                       variable=self.openrouter_optimize_keywords).pack(side='left')
        
        # Load OpenRouter settings
        self.load_openrouter_settings()
        
        # Initialize pricing display
        self.update_model_pricing_display()
        
        # Generate button
        generate_frame = ttk.Frame(ai_bio_frame)
        generate_frame.pack(fill='x', padx=20, pady=10)
        
        self.generate_ai_bio_btn = ttk.Button(generate_frame, text="🚀 Generate AI Bio",
                                             command=self.generate_ai_bio, style='Primary.TButton')
        self.generate_ai_bio_btn.pack(side='left', padx=(0, 10))
        
        ttk.Button(generate_frame, text="🔄 Regenerate Alternatives",
                  command=self.regenerate_ai_bio_alternatives, style='Action.TButton').pack(side='left', padx=(0, 10))
        
        self.enhance_with_openrouter_btn = ttk.Button(generate_frame, text="✨ Enhance with AI",
                                                     command=self.enhance_bio_with_openrouter, style='Action.TButton')
        self.enhance_with_openrouter_btn.pack(side='left')
        
        # Results frame
        results_frame = ttk.LabelFrame(ai_bio_frame, text="Generated AI Bio")
        results_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Bio notebook for multiple versions
        self.ai_bio_notebook = ttk.Notebook(results_frame)
        self.ai_bio_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Primary bio tab
        primary_frame = ttk.Frame(self.ai_bio_notebook)
        self.ai_bio_notebook.add(primary_frame, text="🎯 Primary Bio")
        
        self.ai_primary_bio_text = scrolledtext.ScrolledText(primary_frame, height=8, wrap=tk.WORD,
                                                            font=('Segoe UI', 11))
        self.ai_primary_bio_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Alternative versions tabs
        self.ai_alt_bio_frames = []
        for i in range(3):
            alt_frame = ttk.Frame(self.ai_bio_notebook)
            self.ai_bio_notebook.add(alt_frame, text=f"✨ Alternative {i+1}")
            
            alt_text = scrolledtext.ScrolledText(alt_frame, height=8, wrap=tk.WORD,
                                               font=('Segoe UI', 11))
            alt_text.pack(fill='both', expand=True, padx=5, pady=5)
            self.ai_alt_bio_frames.append(alt_text)
        
        # Analysis tab
        analysis_frame = ttk.Frame(self.ai_bio_notebook)
        self.ai_bio_notebook.add(analysis_frame, text="📊 Analysis")
        
        self.ai_analysis_text = scrolledtext.ScrolledText(analysis_frame, height=8, wrap=tk.WORD,
                                                         font=('Consolas', 9))
        self.ai_analysis_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bio actions
        ai_bio_actions = ttk.Frame(ai_bio_frame)
        ai_bio_actions.pack(fill='x', padx=20, pady=(0, 20))
        
        ttk.Button(ai_bio_actions, text="📋 Copy Primary Bio", 
                  command=self.copy_ai_primary_bio).pack(side='left', padx=5)
        ttk.Button(ai_bio_actions, text="💾 Save All Versions", 
                  command=self.save_ai_bio_versions).pack(side='left', padx=5)
        ttk.Button(ai_bio_actions, text="📧 Export LinkedIn Guide", 
                  command=self.export_ai_bio_guide).pack(side='left', padx=5)
    
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
            
            # Update credentials status display
            self.update_credentials_status()
            
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
            error_message = str(e)
            self.root.after(0, lambda: self._fetch_failed(error_message))
    
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
        
        # Apply current sort if one exists
        repos = user_data.repositories.copy()
        if self.sort_column:
            if self.sort_column == 'name':
                repos.sort(key=lambda r: r.name.lower(), reverse=self.sort_reverse)
            elif self.sort_column == 'language':
                repos.sort(key=lambda r: (r.language or '').lower(), reverse=self.sort_reverse)
            elif self.sort_column == 'stars':
                repos.sort(key=lambda r: r.stars or 0, reverse=self.sort_reverse)
            elif self.sort_column == 'forks':
                repos.sort(key=lambda r: r.forks or 0, reverse=self.sort_reverse)
            elif self.sort_column == 'size':
                repos.sort(key=lambda r: r.size or 0, reverse=self.sort_reverse)
            elif self.sort_column == 'updated':
                repos.sort(key=lambda r: r.updated_at or '', reverse=self.sort_reverse)
            # Update the original data with sorted order
            user_data.repositories = repos
            # Update headers to show sort direction
            self._update_sort_headers()
        
        # Populate repository tree
        for i, repo in enumerate(repos):
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
    
    def convert_to_project_template(self):
        """Convert the current README to a project template JSON file."""
        # Check if we have a README to convert
        readme_content = self.readme_preview.get('1.0', tk.END).strip()
        if not readme_content:
            messagebox.showwarning("No Content", "Please generate a README first.")
            return
        
        # Get selected repository
        selected_repo = self.readme_repo_var.get()
        if not selected_repo:
            messagebox.showwarning("No Repository", "Please select a repository first.")
            return
        
        # Find repository data
        repo_data = None
        if self.current_user_data and self.current_user_data.repositories:
            for repo in self.current_user_data.repositories:
                if f"{repo.name} ({repo.language})" == selected_repo:
                    repo_data = repo
                    break
        
        if not repo_data:
            messagebox.showwarning("Repository Not Found", "Could not find repository data.")
            return
        
        # Create conversion dialog to get additional info
        dialog_result = self.show_template_conversion_dialog(repo_data)
        if not dialog_result:
            return
        
        try:
            # Convert repository data to ProjectMetadata format
            try:
                from .analyzers.repository_analyzer import ProjectMetadata
            except ImportError:
                from analyzers.repository_analyzer import ProjectMetadata
            metadata = ProjectMetadata()
            metadata.name = repo_data.name
            metadata.description = repo_data.description or f"A {repo_data.language} project"
            metadata.primary_language = repo_data.language
            metadata.frameworks = []  # Would need to be analyzed from repository
            metadata.dependencies = []
            metadata.features = []
            metadata.total_files = 0  # Would need actual analysis
            metadata.code_lines = 0
            
            # Convert README to template
            template, saved_path = self.template_converter.convert_and_save(
                readme_content=readme_content,
                metadata=metadata,
                repo_url=repo_data.html_url,
                demo_url=dialog_result.get('demo_url'),
                output_path=dialog_result.get('output_path')
            )
            
            if template and saved_path:
                messagebox.showinfo(
                    "Conversion Successful", 
                    f"README converted to project template!\n\n"
                    f"📋 Template: {template.title}\n"
                    f"📁 Saved to: {saved_path}\n\n"
                    f"You can now use this template to create portfolio projects."
                )
                
                self.status_var.set(f"README converted to template: {Path(saved_path).name}")
                self.logger.info(f"README converted to template: {saved_path}")
            else:
                messagebox.showerror("Conversion Failed", "Failed to convert README to template.")
        
        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert README:\n{str(e)}")
            self.logger.error(f"Template conversion failed: {e}")
    
    def show_template_conversion_dialog(self, repo_data):
        """Show dialog to collect additional information for template conversion."""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎯 Convert to Project Template")
        dialog.geometry("500x350")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        result = {}
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="📋 Project Template Information", 
                               style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = ("This will convert your README into a JSON template that can be used "
                    "in your portfolio projects. Please provide additional information:")
        ttk.Label(main_frame, text=desc_text, wraplength=450).pack(pady=(0, 15))
        
        # Form fields
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill='x', pady=(0, 20))
        
        # Demo URL (Repository URL is already from GitHub)
        ttk.Label(fields_frame, text="Demo URL (optional):").grid(row=0, column=0, sticky='w', pady=10)
        demo_url_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=demo_url_var, width=50).grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=10)
        
        # Output path
        ttk.Label(fields_frame, text="Save Location:").grid(row=1, column=0, sticky='w', pady=10)
        path_frame = ttk.Frame(fields_frame)
        path_frame.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=10)
        
        output_path_var = tk.StringVar()
        # Default to project-templates directory
        default_path = str(Path(__file__).parent.parent / "project-templates" / f"{repo_data.name.lower().replace(' ', '-')}.json")
        output_path_var.set(default_path)
        
        ttk.Entry(path_frame, textvariable=output_path_var, width=35).pack(side='left', fill='x', expand=True)
        
        def browse_path():
            file_path = filedialog.asksaveasfilename(
                title="Save Template As",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"{repo_data.name.lower().replace(' ', '-')}.json"
            )
            if file_path:
                output_path_var.set(file_path)
        
        ttk.Button(path_frame, text="Browse", command=browse_path).pack(side='right', padx=(5, 0))
        
        fields_frame.columnconfigure(1, weight=1)
        path_frame.columnconfigure(0, weight=1)
        
        # Preview info
        preview_frame = ttk.LabelFrame(main_frame, text="Template Preview", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        preview_info = f"Project: {repo_data.name}\n"
        preview_info += f"Language: {repo_data.language or 'Unknown'}\n"
        preview_info += f"Description: {repo_data.description or 'No description'}\n"
        preview_info += f"Repository: {repo_data.html_url}"
        
        ttk.Label(preview_frame, text=preview_info, justify='left').pack(anchor='w')
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        def on_convert():
            result['demo_url'] = demo_url_var.get().strip() or None  
            result['output_path'] = output_path_var.get().strip() or None
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side='left')
        ttk.Button(button_frame, text="🎯 Convert to Template", 
                  command=on_convert, style='Primary.TButton').pack(side='right')
        
        # Wait for dialog
        dialog.wait_window()
        
        return result if result else None
    
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
    
    def generate_ai_bio(self):
        """Generate AI-powered LinkedIn bio with loading indicator."""
        if not self.current_user_data or not self.current_user_data.profile_data:
            messagebox.showwarning("No Profile Data", "Please fetch GitHub data first.")
            return
        
        # Start AI bio generation in a separate thread
        self._start_ai_bio_generation()
    
    def _start_ai_bio_generation(self):
        """Start AI bio generation in background thread."""
        import threading
        
        # Show loading indicator
        self.status_var.set("🤖 Generating AI-powered LinkedIn bio...")
        self.generate_ai_bio_btn.config(state='disabled')
        
        # Start progress animation
        self._start_loading_animation("Generating AI bio")
        
        # Run in background thread
        thread = threading.Thread(target=self._generate_ai_bio_thread, daemon=True)
        thread.start()
    
    def _generate_ai_bio_thread(self):
        """Background thread for AI bio generation."""
        try:
            # Create AI bio configuration
            config = AIBioConfig(
                bio_style=self.ai_bio_style.get(),
                tone=self.ai_bio_tone.get(),
                length=self.ai_bio_length.get(),
                target_role=self.ai_target_role.get(),
                experience_level=self.ai_experience_level.get(),
                years_experience=int(self.ai_years_experience.get() or 0),
                use_metrics=self.ai_use_metrics.get(),
                include_passion_statement=self.ai_include_passion.get(),
                include_call_to_action=self.ai_include_cta.get(),
                emphasize_collaboration=self.ai_emphasize_collaboration.get(),
                show_learning_mindset=self.ai_show_learning_mindset.get()
            )
            
            # Get technology stack from GUI
            config.programming_languages = [lang.strip() for lang in self.ai_programming_languages.get('1.0', tk.END).strip().split(',') if lang.strip()]
            config.frameworks_libraries = [fw.strip() for fw in self.ai_frameworks_libraries.get('1.0', tk.END).strip().split(',') if fw.strip()]
            config.tools_platforms = [tool.strip() for tool in self.ai_tools_platforms.get('1.0', tk.END).strip().split(',') if tool.strip()]
            
            # Initialize AI bio generator
            ai_bio_generator = AILinkedInBioGenerator(config)
            
            # Generate bio using GitHub profile data
            ai_bio_result = ai_bio_generator.generate_ai_bio(self.current_user_data.profile_data, config)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._ai_bio_generation_completed(ai_bio_result))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._ai_bio_generation_failed(error_msg))
    
    def _ai_bio_generation_completed(self, ai_bio_result):
        """Handle successful AI bio generation."""
        try:
            # Stop loading animation
            self._stop_loading_animation()
            
            # Display primary bio
            self.ai_primary_bio_text.delete('1.0', tk.END)
            self.ai_primary_bio_text.insert('1.0', ai_bio_result.primary_bio)
            
            # Display alternative versions
            for i, alt_text_widget in enumerate(self.ai_alt_bio_frames):
                alt_text_widget.delete('1.0', tk.END)
                if i < len(ai_bio_result.alternative_versions):
                    alt_text_widget.insert('1.0', ai_bio_result.alternative_versions[i])
                else:
                    alt_text_widget.insert('1.0', "Alternative version not available.")
            
            # Display analysis
            analysis_text = self._format_ai_bio_analysis(ai_bio_result)
            self.ai_analysis_text.delete('1.0', tk.END)
            self.ai_analysis_text.insert('1.0', analysis_text)
            
            # Store result for later use
            self.current_ai_bio_result = ai_bio_result
            
            self.status_var.set("✅ AI bio generation complete!")
            self.logger.info("AI LinkedIn bio generated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to display AI bio results: {e}")
        finally:
            self.generate_ai_bio_btn.config(state='normal')
    
    def _ai_bio_generation_failed(self, error_message):
        """Handle AI bio generation failure."""
        self._stop_loading_animation()
        self.status_var.set("❌ AI bio generation failed")
        self.generate_ai_bio_btn.config(state='normal')
        messagebox.showerror("AI Bio Generation Error", f"Failed to generate AI bio:\n{error_message}")
        self.logger.error(f"AI bio generation failed: {error_message}")
    
    def regenerate_ai_bio_alternatives(self):
        """Regenerate alternative AI bio versions."""
        if not hasattr(self, 'current_ai_bio_result'):
            messagebox.showwarning("No Bio Generated", "Please generate an AI bio first.")
            return
        
        try:
            self.status_var.set("Regenerating alternative bio versions...")
            
            # Create new configuration with different styles
            alternative_styles = ['creative', 'technical', 'professional']
            alternative_results = []
            
            for style in alternative_styles:
                if style != self.ai_bio_style.get():
                    config = AIBioConfig(
                        bio_style=style,
                        tone=self.ai_bio_tone.get(),
                        length=self.ai_bio_length.get(),
                        target_role=self.ai_target_role.get(),
                        use_metrics=self.ai_use_metrics.get(),
                        include_passion_statement=self.ai_include_passion.get(),
                        include_call_to_action=self.ai_include_cta.get(),
                        emphasize_collaboration=self.ai_emphasize_collaboration.get()
                    )
                    
                    ai_bio_generator = AILinkedInBioGenerator(config)
                    result = ai_bio_generator.generate_ai_bio(self.current_user_data.profile_data, config)
                    alternative_results.append(result.primary_bio)
            
            # Update alternative version displays
            for i, alt_text_widget in enumerate(self.ai_alt_bio_frames):
                alt_text_widget.delete('1.0', tk.END)
                if i < len(alternative_results):
                    alt_text_widget.insert('1.0', alternative_results[i])
                else:
                    alt_text_widget.insert('1.0', "Alternative version not available.")
            
            self.status_var.set("Alternative bio versions regenerated!")
            
        except Exception as e:
            messagebox.showerror("Regeneration Error", f"Failed to regenerate alternatives:\n{str(e)}")
    
    def _format_ai_bio_analysis(self, ai_bio_result: AIGeneratedBio) -> str:
        """Format AI bio analysis for display."""
        analysis_parts = []
        
        analysis_parts.append("🤖 AI BIO ANALYSIS REPORT")
        analysis_parts.append("=" * 50)
        analysis_parts.append("")
        
        # Bio quality metrics
        analysis_parts.append("📊 BIO QUALITY METRICS")
        analysis_parts.append(f"• Readability Score: {ai_bio_result.readability_score:.1f}/100")
        analysis_parts.append(f"• Engagement Potential: {ai_bio_result.engagement_potential.upper()}")
        analysis_parts.append(f"• SEO Optimization: {ai_bio_result.search_optimization_score:.1f}/100")
        analysis_parts.append(f"• Uniqueness Score: {ai_bio_result.uniqueness_score:.1f}/100")
        analysis_parts.append("")
        
        # Keywords analysis
        if ai_bio_result.primary_keywords_used:
            analysis_parts.append("🎯 KEYWORDS USED")
            analysis_parts.append(f"• Primary: {', '.join(ai_bio_result.primary_keywords_used)}")
        
        if ai_bio_result.industry_keywords_used:
            analysis_parts.append(f"• Industry: {', '.join(ai_bio_result.industry_keywords_used)}")
        analysis_parts.append("")
        
        # Authenticity indicators
        if ai_bio_result.authenticity_indicators:
            analysis_parts.append("✨ AUTHENTICITY INDICATORS")
            for indicator in ai_bio_result.authenticity_indicators:
                analysis_parts.append(f"• {indicator}")
            analysis_parts.append("")
        
        # Bio components breakdown
        analysis_parts.append("🏗️ BIO COMPONENTS")
        analysis_parts.append(f"• Opening Hook: {len(ai_bio_result.opening_hook)} chars")
        analysis_parts.append(f"• Expertise Statement: {len(ai_bio_result.expertise_statement)} chars")
        analysis_parts.append(f"• Achievement Highlights: {len(ai_bio_result.achievement_highlights)} chars")
        analysis_parts.append(f"• Value Proposition: {len(ai_bio_result.value_proposition)} chars")
        
        if ai_bio_result.passion_statement:
            analysis_parts.append(f"• Passion Statement: {len(ai_bio_result.passion_statement)} chars")
        
        if ai_bio_result.call_to_action:
            analysis_parts.append(f"• Call to Action: {len(ai_bio_result.call_to_action)} chars")
        
        analysis_parts.append("")
        analysis_parts.append(f"📏 Total Length: {len(ai_bio_result.primary_bio)} characters")
        analysis_parts.append(f"📝 Word Count: {len(ai_bio_result.primary_bio.split())} words")
        
        return "\n".join(analysis_parts)
    
    def copy_ai_primary_bio(self):
        """Copy primary AI bio to clipboard."""
        content = self.ai_primary_bio_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("No Bio", "Please generate an AI bio first.")
            return
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()
            messagebox.showinfo("Copied", "AI bio copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy AI bio:\n{str(e)}")
    
    def save_ai_bio_versions(self):
        """Save all AI bio versions to files."""
        if not hasattr(self, 'current_ai_bio_result'):
            messagebox.showwarning("No Bio Generated", "Please generate an AI bio first.")
            return
        
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = self.current_user_data.username if self.current_user_data else "user"
            
            # Save primary bio
            primary_file = output_dir / f"AI_LinkedIn_Bio_{username}_{timestamp}.txt"
            with open(primary_file, 'w', encoding='utf-8') as f:
                f.write("🤖 AI-Generated LinkedIn Bio (Primary)\n")
                f.write("=" * 50 + "\n\n")
                f.write(self.current_ai_bio_result.primary_bio)
                f.write("\n\n")
                
                # Add alternatives
                f.write("✨ Alternative Versions\n")
                f.write("=" * 30 + "\n\n")
                for i, alt in enumerate(self.current_ai_bio_result.alternative_versions, 1):
                    f.write(f"Alternative {i}:\n")
                    f.write("-" * 15 + "\n")
                    f.write(alt + "\n\n")
                
                # Add analysis
                f.write(self._format_ai_bio_analysis(self.current_ai_bio_result))
            
            # Save JSON version
            json_file = output_dir / f"AI_LinkedIn_Bio_{username}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                bio_dict = {
                    'primary_bio': self.current_ai_bio_result.primary_bio,
                    'alternative_versions': self.current_ai_bio_result.alternative_versions,
                    'bio_components': {
                        'opening_hook': self.current_ai_bio_result.opening_hook,
                        'expertise_statement': self.current_ai_bio_result.expertise_statement,
                        'achievement_highlights': self.current_ai_bio_result.achievement_highlights,
                        'value_proposition': self.current_ai_bio_result.value_proposition,
                        'passion_statement': self.current_ai_bio_result.passion_statement,
                        'call_to_action': self.current_ai_bio_result.call_to_action
                    },
                    'analysis': {
                        'readability_score': self.current_ai_bio_result.readability_score,
                        'engagement_potential': self.current_ai_bio_result.engagement_potential,
                        'search_optimization_score': self.current_ai_bio_result.search_optimization_score,
                        'uniqueness_score': self.current_ai_bio_result.uniqueness_score,
                        'keywords_used': self.current_ai_bio_result.primary_keywords_used,
                        'authenticity_indicators': self.current_ai_bio_result.authenticity_indicators
                    },
                    'generated_at': timestamp,
                    'username': username
                }
                json.dump(bio_dict, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Saved", f"AI bio versions saved to:\n{primary_file.name}\n{json_file.name}")
            self.logger.info(f"✅ AI bio versions saved to output directory")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save AI bio versions:\n{str(e)}")
    
    def export_ai_bio_guide(self):
        """Export comprehensive AI bio implementation guide."""
        if not hasattr(self, 'current_ai_bio_result'):
            messagebox.showwarning("No Bio Generated", "Please generate an AI bio first.")
            return
        
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = self.current_user_data.username if self.current_user_data else "user"
            guide_file = output_dir / f"AI_LinkedIn_Bio_Guide_{username}_{timestamp}.md"
            
            guide_content = self._generate_ai_bio_guide_content()
            
            with open(guide_file, 'w', encoding='utf-8') as f:
                f.write(guide_content)
            
            messagebox.showinfo("Exported", f"AI bio implementation guide exported to:\n{guide_file.name}")
            self.logger.info(f"✅ AI bio guide exported to {guide_file.name}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export AI bio guide:\n{str(e)}")
    
    def _generate_ai_bio_guide_content(self) -> str:
        """Generate comprehensive AI bio implementation guide."""
        username = self.current_user_data.username if self.current_user_data else "Professional"
        
        guide_content = f"""# 🤖 AI LinkedIn Bio Implementation Guide
*Generated for {username} on {datetime.now().strftime('%B %d, %Y')}*

## 🎯 Your AI-Generated LinkedIn Bio

### Primary Bio (Recommended)
```
{self.current_ai_bio_result.primary_bio}
```

### Alternative Versions

#### Version 1: Creative Style
```
{self.current_ai_bio_result.alternative_versions[0] if self.current_ai_bio_result.alternative_versions else 'Not available'}
```

#### Version 2: Technical Focus
```
{self.current_ai_bio_result.alternative_versions[1] if len(self.current_ai_bio_result.alternative_versions) > 1 else 'Not available'}
```

## 📊 Bio Analysis & Optimization

### Quality Metrics
- **Readability Score**: {self.current_ai_bio_result.readability_score:.1f}/100
- **Engagement Potential**: {self.current_ai_bio_result.engagement_potential.title()}
- **SEO Optimization**: {self.current_ai_bio_result.search_optimization_score:.1f}/100
- **Uniqueness Score**: {self.current_ai_bio_result.uniqueness_score:.1f}/100

### Keywords Successfully Integrated
{chr(10).join(f"- {keyword}" for keyword in self.current_ai_bio_result.primary_keywords_used) if self.current_ai_bio_result.primary_keywords_used else "- No specific keywords detected"}

### Authenticity Indicators
{chr(10).join(f"- {indicator}" for indicator in self.current_ai_bio_result.authenticity_indicators) if self.current_ai_bio_result.authenticity_indicators else "- Standard authenticity markers"}

## 🚀 Implementation Strategy

### Step 1: Choose Your Bio
1. **Primary Bio**: Best overall balance of professionalism and personality
2. **Alternative 1**: More creative and engaging
3. **Alternative 2**: Technical focus for engineering roles

### Step 2: Optimize for Your Goals
- **Job Seeking**: Use primary bio with technical keywords
- **Networking**: Consider the creative alternative
- **Thought Leadership**: Emphasize innovation and expertise

### Step 3: LinkedIn Best Practices
1. **Profile Photo**: Professional headshot
2. **Headline**: Complement your bio with role-specific keywords
3. **Experience**: Align job descriptions with bio messaging
4. **Skills**: Endorse skills mentioned in your bio
5. **Content**: Share posts that reflect your bio's value proposition

## 📈 Performance Tracking

### Metrics to Monitor
- Profile views (aim for 20% increase)
- Connection requests (quality over quantity)
- InMail responses (if applicable)
- Content engagement on posts

### A/B Testing
1. Use primary bio for 2 weeks
2. Switch to alternative version
3. Compare metrics
4. Optimize based on results

## 🎨 Customization Tips

### Personalization Options
- Add industry-specific achievements
- Include personal interests (if relevant)
- Adjust tone based on company culture
- Update with new projects and skills

### Seasonal Updates
- Quarterly review and refresh
- Add new certifications or projects
- Update with career progression
- Reflect current goals and interests

## 🔧 Bio Component Breakdown

### Opening Hook
"{self.current_ai_bio_result.opening_hook}"
*Purpose: Immediately communicates your value and expertise*

### Expertise Statement  
"{self.current_ai_bio_result.expertise_statement}"
*Purpose: Establishes credibility and technical competence*

### Achievement Highlights
"{self.current_ai_bio_result.achievement_highlights}"
*Purpose: Provides concrete evidence of your impact*

### Value Proposition
"{self.current_ai_bio_result.value_proposition}"
*Purpose: Explains what makes you unique and valuable*

{f'''### Passion Statement
"{self.current_ai_bio_result.passion_statement}"
*Purpose: Shows personality and genuine interest*''' if self.current_ai_bio_result.passion_statement else ''}

{f'''### Call to Action
"{self.current_ai_bio_result.call_to_action}"
*Purpose: Encourages meaningful connections and opportunities*''' if self.current_ai_bio_result.call_to_action else ''}

## 💡 Next Steps

1. **Implement** your chosen bio on LinkedIn
2. **Update** other sections to align with bio messaging
3. **Share** content that reinforces your value proposition
4. **Monitor** performance and engagement metrics
5. **Iterate** based on results and career changes

---

*This guide was generated using AI analysis of your GitHub repositories to create authentic, data-driven LinkedIn content that represents your actual skills and achievements.*

**Generated by RepoReadme AI Bio Generator**
"""
        
        return guide_content
    
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
    
    def toggle_openrouter_config(self):
        """Toggle OpenRouter configuration visibility."""
        if self.openrouter_enabled.get():
            self.openrouter_settings_frame.pack(fill='x', pady=(10, 0))
        else:
            self.openrouter_settings_frame.pack_forget()
    
    def update_temperature_label(self, value):
        """Update temperature label."""
        self.temperature_label.config(text=f"{float(value):.1f}")
    
    def update_model_pricing_display(self, event=None):
        """Update cost estimate display when model changes."""
        try:
            from openrouter_service import OpenRouterAIService
            service = OpenRouterAIService()
            pricing = service.get_model_pricing(self.openrouter_model.get())
            
            if pricing:
                cost = pricing.estimate_bio_cost()
                self.cost_estimate_label.config(text=f"Est: ${cost:.4f}")
            else:
                self.cost_estimate_label.config(text="Est: N/A")
                
        except Exception as e:
            self.cost_estimate_label.config(text="Est: N/A")
    
    def show_model_pricing(self):
        """Show detailed model pricing information."""
        try:
            from openrouter_service import OpenRouterAIService
            service = OpenRouterAIService()
            models_info = service.get_all_models_with_pricing()
            
            # Create pricing window
            pricing_window = tk.Toplevel(self.root)
            pricing_window.title("OpenRouter Model Pricing")
            pricing_window.geometry("800x600")
            pricing_window.resizable(True, True)
            
            # Create main frame with scrollbar
            main_frame = ttk.Frame(pricing_window)
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Header
            header_label = ttk.Label(main_frame, text="🤖 OpenRouter Model Pricing & Performance", 
                                   font=('Segoe UI', 14, 'bold'))
            header_label.pack(pady=(0, 10))
            
            # Info label
            info_label = ttk.Label(main_frame, 
                                 text="Cost estimates for typical bio enhancement (500 input + 300 output tokens)",
                                 font=('Segoe UI', 9), foreground='#666')
            info_label.pack(pady=(0, 10))
            
            # Create treeview for model data
            columns = ('Model', 'Description', 'Cost/Bio', 'Provider', 'Latency')
            tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
            
            # Configure columns
            tree.heading('Model', text='Model')
            tree.heading('Description', text='Description')
            tree.heading('Cost/Bio', text='Cost per Bio')
            tree.heading('Provider', text='Provider')
            tree.heading('Latency', text='Avg Latency')
            
            tree.column('Model', width=200)
            tree.column('Description', width=300)
            tree.column('Cost/Bio', width=100)
            tree.column('Provider', width=100)
            tree.column('Latency', width=100)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack treeview and scrollbar
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill='both', expand=True)
            
            tree.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Populate with model data
            for model_id, model_name, description, cost, provider, latency in models_info:
                tree.insert('', 'end', values=(model_name, description, cost, provider, latency))
            
            # Bottom info frame
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill='x', pady=(10, 0))
            
            ttk.Label(info_frame, text="💡 Recommendations:", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text="• Budget: Llama-3-8b or DeepSeek V3.2", font=('Segoe UI', 9)).pack(anchor='w')
            ttk.Label(info_frame, text="• Balanced: GPT-3.5-turbo or Claude-3-haiku", font=('Segoe UI', 9)).pack(anchor='w')
            ttk.Label(info_frame, text="• Premium: Claude Sonnet 4.5 or GPT-4", font=('Segoe UI', 9)).pack(anchor='w')
            ttk.Label(info_frame, text="• Speed: Gemini 2.5 Flash (0.4s latency)", font=('Segoe UI', 9)).pack(anchor='w')
            
            # Double-click to select model
            def on_model_select(event):
                selection = tree.selection()[0]
                model_name = tree.item(selection, 'values')[0]
                # Find model ID by name
                for model_id, pricing in service.model_pricing.items():
                    if pricing.model_name == model_name:
                        self.openrouter_model.set(model_id)
                        self.update_model_pricing_display()
                        pricing_window.destroy()
                        break
            
            tree.bind('<Double-1>', on_model_select)
            
            # Instructions
            ttk.Label(info_frame, text="💡 Double-click a model to select it", 
                     font=('Segoe UI', 9, 'italic'), foreground='#666').pack(anchor='w', pady=(5, 0))
            
        except Exception as e:
            messagebox.showerror("Pricing Error", f"Failed to show pricing information:\n{str(e)}")
    
    def load_openrouter_settings(self):
        """Load OpenRouter settings from configuration."""
        try:
            # Use get_setting() for consistency with other settings
            api_key = self.settings_manager.get_setting('openrouter_api_key', '')
            model = self.settings_manager.get_setting('openrouter_model', 'openai/gpt-3.5-turbo')
            enabled = self.settings_manager.get_setting('openrouter_enabled', False)
            temperature = self.settings_manager.get_setting('openrouter_temperature', 0.7)
            
            if api_key:
                self.openrouter_api_key.delete(0, 'end')  # Clear first
                self.openrouter_api_key.insert(0, api_key)
            
            if model:
                self.openrouter_model.set(model)
            
            self.openrouter_enabled.set(enabled)
            self.toggle_openrouter_config()
            
            self.openrouter_temperature.set(temperature)
            self.update_temperature_label(temperature)
                
        except Exception as e:
            self.logger.debug(f"Could not load OpenRouter settings: {e}")
    
    def save_openrouter_key(self):
        """Save OpenRouter API key to settings."""
        api_key = self.openrouter_api_key.get().strip()
        
        if not api_key:
            messagebox.showwarning("Missing API Key", "Please enter your OpenRouter API key.")
            return
        
        try:
            # Save to settings (set_setting already saves automatically)
            self.settings_manager.set_setting('openrouter_api_key', api_key)
            self.settings_manager.set_setting('openrouter_model', self.openrouter_model.get())
            self.settings_manager.set_setting('openrouter_enabled', self.openrouter_enabled.get())
            self.settings_manager.set_setting('openrouter_temperature', self.openrouter_temperature.get())
            
            messagebox.showinfo("Saved", "OpenRouter API key saved successfully!")
            self.logger.info("OpenRouter API key saved to settings")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save OpenRouter settings:\n{str(e)}")
    
    def save_github_username(self):
        """Save GitHub username to settings."""
        username = self.username_var.get().strip()
        
        if not username:
            messagebox.showwarning("Missing Username", "Please enter your GitHub username.")
            return
        
        try:
            self.settings_manager.set_setting('github_username', username)
            
            # Update status display
            self.update_credentials_status()
            
            messagebox.showinfo("Saved", "GitHub username saved successfully!")
            self.logger.info("GitHub username saved to settings")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save GitHub username:\n{str(e)}")
    
    def save_github_token(self):
        """Save GitHub token to settings."""
        token = self.token_var.get().strip()  # Strip whitespace
        
        if not token:
            messagebox.showwarning("Missing Token", "Please enter your GitHub token.")
            return
        
        try:
            self.settings_manager.set_setting('github_token', token)
            
            # Update status display
            self.update_credentials_status()
            
            messagebox.showinfo("Saved", "GitHub token saved successfully!")
            self.logger.info("GitHub token saved to settings")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save GitHub token:\n{str(e)}")
    
    def test_openrouter_connection(self):
        """Test OpenRouter API connection."""
        api_key = self.openrouter_api_key.get().strip()
        
        if not api_key:
            messagebox.showwarning("Missing API Key", "Please enter your OpenRouter API key first.")
            return
        
        try:
            self.status_var.set("Testing OpenRouter connection...")
            
            # Create OpenRouter config and service
            config = OpenRouterConfig(
                api_key=api_key,
                model=self.openrouter_model.get(),
                temperature=self.openrouter_temperature.get()
            )
            
            service = OpenRouterAIService(config)
            result = service.test_connection()
            
            if result["success"]:
                messagebox.showinfo("Connection Success", 
                                   f"✅ OpenRouter API connection successful!\n\n"
                                   f"Model: {result['model']}\n"
                                   f"Response: {result['response']}\n"
                                   f"Tokens used: {result['tokens_used']}")
                self.logger.info("OpenRouter API connection test successful")
            else:
                messagebox.showerror("Connection Failed", 
                                   f"❌ OpenRouter API connection failed:\n\n"
                                   f"Error: {result['error']}\n"
                                   f"Details: {result.get('details', 'No details available')}")
                self.logger.error(f"OpenRouter API connection test failed: {result['error']}")
            
            self.status_var.set("Ready")
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Failed to test OpenRouter connection:\n{str(e)}")
            self.status_var.set("Ready")
    
    def enhance_bio_with_openrouter(self):
        """Enhance current bio using OpenRouter AI."""
        if not hasattr(self, 'current_ai_bio_result') or not self.current_ai_bio_result:
            messagebox.showwarning("No Bio Generated", "Please generate an AI bio first.")
            return
        
        api_key = self.openrouter_api_key.get().strip()
        if not api_key:
            messagebox.showwarning("OpenRouter Not Configured", 
                                 "Please configure your OpenRouter API key first.")
            return
        
        if not self.openrouter_enabled.get():
            messagebox.showwarning("OpenRouter Disabled", 
                                 "Please enable OpenRouter AI Enhancement first.")
            return
        
        try:
            self.status_var.set("Enhancing bio with OpenRouter AI...")
            self.enhance_with_openrouter_btn.config(state='disabled')
            
            # Get cost estimate first
            service = OpenRouterAIService()
            cost_info = service.estimate_enhancement_cost(
                self.current_ai_bio_result.primary_bio, 
                self.openrouter_model.get()
            )
            
            # Show cost confirmation
            if "error" not in cost_info:
                cost_msg = (f"Enhancement Cost Estimate:\n\n"
                           f"Model: {cost_info['model']}\n"
                           f"Provider: {cost_info['provider']}\n"
                           f"Estimated Cost: {cost_info['cost_formatted']}\n"
                           f"Input Tokens: ~{cost_info['estimated_input_tokens']}\n"
                           f"Output Tokens: ~{cost_info['estimated_output_tokens']}\n\n"
                           f"Proceed with enhancement?")
                
                if not messagebox.askyesno("Confirm Enhancement", cost_msg):
                    return
            
            # Create enhancement request
            enhancement_request = EnhancementRequest(
                original_bio=self.current_ai_bio_result.primary_bio,
                target_style=self.ai_bio_style.get(),
                target_role=self.ai_target_role.get(),
                target_industry="technology",
                enhancement_type="improve",
                include_metrics=self.ai_use_metrics.get(),
                github_username=self.current_user_data.username if self.current_user_data else "",
                primary_languages=list(self.current_user_data.profile_data.primary_languages[:5]) if self.current_user_data and self.current_user_data.profile_data else [],
                project_highlights=[p['name'] for p in self.current_user_data.profile_data.featured_projects[:3]] if self.current_user_data and self.current_user_data.profile_data else []
            )
            
            # Create OpenRouter service
            config = OpenRouterConfig(
                api_key=api_key,
                model=self.openrouter_model.get(),
                temperature=self.openrouter_temperature.get(),
                enhance_creativity=self.openrouter_enhance_creativity.get(),
                improve_readability=self.openrouter_improve_readability.get(),
                optimize_keywords=self.openrouter_optimize_keywords.get()
            )
            
            service = OpenRouterAIService(config)
            enhancement_result = service.enhance_linkedin_bio(enhancement_request)
            
            # Update the primary bio with enhanced version
            self.ai_primary_bio_text.delete('1.0', tk.END)
            self.ai_primary_bio_text.insert('1.0', enhancement_result.enhanced_bio)
            
            # Generate new alternatives using OpenRouter
            alternatives = service.generate_bio_alternatives(enhancement_result.enhanced_bio, 3)
            for i, alt_text_widget in enumerate(self.ai_alt_bio_frames):
                alt_text_widget.delete('1.0', tk.END)
                if i < len(alternatives):
                    alt_text_widget.insert('1.0', alternatives[i])
            
            # Update analysis with enhancement info
            cost_display = ""
            if hasattr(enhancement_result, 'actual_cost') and enhancement_result.actual_cost is not None:
                cost_display = f"💰 Actual Cost: ${enhancement_result.actual_cost:.6f}"
                if hasattr(enhancement_result, 'prompt_tokens') and hasattr(enhancement_result, 'completion_tokens'):
                    cost_display += f" ({enhancement_result.prompt_tokens} + {enhancement_result.completion_tokens} tokens)"
            else:
                # Fallback to estimated cost
                estimated_cost = enhancement_result.tokens_used * 0.001 if enhancement_result.tokens_used else 0
                cost_display = f"💰 Estimated Cost: ${estimated_cost:.6f}"
            
            generation_info = ""
            if hasattr(enhancement_result, 'generation_id') and enhancement_result.generation_id:
                generation_info = f"🔍 Generation ID: {enhancement_result.generation_id}\n"
            
            enhancement_analysis = f"""🚀 OPENROUTER AI ENHANCEMENT RESULTS
{chr(61) * 60}

✨ Enhancement Score: {enhancement_result.enhancement_score:.1f}/100
🤖 Model Used: {enhancement_result.model_used}
⚡ Processing Time: {enhancement_result.processing_time:.2f}s
🎯 Tokens Used: {enhancement_result.tokens_used}
{cost_display}
{generation_info}
📈 IMPROVEMENTS MADE:
{chr(10).join(f"• {improvement}" for improvement in enhancement_result.improvements_made)}

💡 SUGGESTIONS:
{chr(10).join(f"• {suggestion}" for suggestion in enhancement_result.suggestions)}

📊 QUALITY IMPROVEMENTS:
• Readability: {enhancement_result.readability_improvement:+.1f}%
• Engagement: {enhancement_result.engagement_improvement:+.1f}%
• Keywords: {enhancement_result.keyword_optimization:+.1f}%

{chr(61) * 60}

""" + self.ai_analysis_text.get('1.0', tk.END)
            
            self.ai_analysis_text.delete('1.0', tk.END)
            self.ai_analysis_text.insert('1.0', enhancement_analysis)
            
            # Update stored result
            self.current_ai_bio_result.primary_bio = enhancement_result.enhanced_bio
            self.current_ai_bio_result.alternative_versions = alternatives
            
            self.status_var.set("Bio enhancement complete!")
            
            # Show completion message with cost info
            cost_info = ""
            if hasattr(enhancement_result, 'actual_cost') and enhancement_result.actual_cost is not None:
                cost_info = f"\nActual Cost: ${enhancement_result.actual_cost:.6f}"
            else:
                estimated_cost = enhancement_result.tokens_used * 0.001 if enhancement_result.tokens_used else 0
                cost_info = f"\nEstimated Cost: ${estimated_cost:.6f}"
            
            messagebox.showinfo("Enhancement Complete", 
                               f"✅ Bio enhanced successfully!\n\n"
                               f"Enhancement Score: {enhancement_result.enhancement_score:.1f}/100\n"
                               f"Improvements: {len(enhancement_result.improvements_made)}\n"
                               f"Processing Time: {enhancement_result.processing_time:.2f}s{cost_info}")
            
        except Exception as e:
            self.logger.error(f"OpenRouter bio enhancement failed: {e}")
            messagebox.showerror("Enhancement Error", f"Failed to enhance bio with OpenRouter:\n{str(e)}")
            
        finally:
            self.enhance_with_openrouter_btn.config(state='normal')
    
    def load_settings(self):
        """Load application settings."""
        try:
            # Load individual settings
            username = self.settings_manager.get_setting('github_username', '')
            token = self.settings_manager.get_setting('github_token', '').strip()  # Strip whitespace
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
            
            # Update credentials status
            self.update_credentials_status()
                
            self.logger.info("Settings loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
    
    def update_credentials_status(self):
        """Update the credentials status display."""
        try:
            username = self.settings_manager.get_setting('github_username', '')
            token = self.settings_manager.get_setting('github_token', '').strip()  # Strip whitespace
            
            # Update username status
            if username:
                self.username_status_var.set(f"✅ {username}")
                self.username_status_label.configure(foreground='green')
            else:
                self.username_status_var.set("❌ Not saved")
                self.username_status_label.configure(foreground='red')
            
            # Update token status
            if token:
                masked_token = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
                self.token_status_var.set(f"✅ {masked_token}")
                self.token_status_label.configure(foreground='green')
            else:
                self.token_status_var.set("❌ Not saved")
                self.token_status_label.configure(foreground='red')
                
        except Exception as e:
            self.logger.warning(f"Failed to update credentials status: {e}")
    
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
    
    def _start_loading_animation(self, operation_name="Processing"):
        """Start animated loading indicator."""
        self.loading_active = True
        self.loading_operation = operation_name
        self.loading_frame = 0
        self.loading_symbols = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._animate_loading()
    
    def _animate_loading(self):
        """Animate the loading indicator."""
        if not getattr(self, 'loading_active', False):
            return
        
        # Update status with animated symbol
        symbol = self.loading_symbols[self.loading_frame % len(self.loading_symbols)]
        self.status_var.set(f"{symbol} {self.loading_operation}...")
        
        # Schedule next frame
        self.loading_frame += 1
        self.root.after(100, self._animate_loading)  # Update every 100ms
    
    def _stop_loading_animation(self):
        """Stop the loading animation."""
        self.loading_active = False
    
    def add_quick_tech(self, category):
        """Add predefined technology stacks for common categories."""
        quick_stacks = {
            'frontend': {
                'languages': 'JavaScript, TypeScript, HTML, CSS',
                'frameworks': 'React, NextJS, Vue.js, Angular, Tailwind CSS',
                'tools': 'VS Code, Vite, Webpack, npm, Vercel, Netlify'
            },
            'backend': {
                'languages': 'Python, Node.js, Java, C#, Go',
                'frameworks': 'Django, Flask, Express, Spring Boot, .NET Core',
                'tools': 'Docker, PostgreSQL, MongoDB, Redis, AWS, Git'
            },
            'fullstack': {
                'languages': 'JavaScript, TypeScript, Python, HTML, CSS',
                'frameworks': 'React, NextJS, Django, Express, Tailwind CSS',
                'tools': 'VS Code, Docker, PostgreSQL, Git, AWS, Vercel'
            },
            'mobile': {
                'languages': 'JavaScript, TypeScript, Swift, Kotlin, Dart',
                'frameworks': 'React Native, Flutter, Avalonia, Xamarin',
                'tools': 'Xcode, Android Studio, Expo, Firebase, VS Code'
            }
        }
        
        if category in quick_stacks:
            stack = quick_stacks[category]
            
            # Clear existing content
            self.ai_programming_languages.delete('1.0', tk.END)
            self.ai_frameworks_libraries.delete('1.0', tk.END)
            self.ai_tools_platforms.delete('1.0', tk.END)
            
            # Insert new content
            self.ai_programming_languages.insert('1.0', stack['languages'])
            self.ai_frameworks_libraries.insert('1.0', stack['frameworks'])
            self.ai_tools_platforms.insert('1.0', stack['tools'])
    
    def clear_tech_fields(self):
        """Clear all technology stack fields."""
        self.ai_programming_languages.delete('1.0', tk.END)
        self.ai_frameworks_libraries.delete('1.0', tk.END)
        self.ai_tools_platforms.delete('1.0', tk.END)
    
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