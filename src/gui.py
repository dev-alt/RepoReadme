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
import re
import threading
import time
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    from .analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata
    from .templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
    from .utils.logger import get_logger
    from .config.settings import SettingsManager
    from .template_builder import create_custom_template_builder
    from .bulk_analyzer_dialog import create_bulk_analyzer
    from .profile_builder_dialog import create_profile_builder
    from github import Github
except ImportError:
    from analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata  
    from templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
    from utils.logger import get_logger
    from config.settings import SettingsManager
    try:
        from template_builder import create_custom_template_builder
        from bulk_analyzer_dialog import create_bulk_analyzer
        from profile_builder_dialog import create_profile_builder
    except ImportError:
        # Fallback functions if features fail to import
        def create_custom_template_builder(parent):
            from tkinter import messagebox
            messagebox.showerror("Feature Unavailable", "Custom template builder is not available in this session.")
            return None
        
        def create_bulk_analyzer(parent):
            from tkinter import messagebox
            messagebox.showerror("Feature Unavailable", "Bulk analyzer is not available in this session.")
            return None
        
        def create_profile_builder(parent):
            from tkinter import messagebox
            messagebox.showerror("Feature Unavailable", "GitHub Profile Builder is not available in this session.")
            return None
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
        self.root.title("RepoReadme - Automatic README Generator")
        self.root.geometry("1500x950")
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
        """Configure clean GUI styles."""
        style = ttk.Style()
        
        # Simple, clean styling
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
        self.main_paned.pack(fill='both', expand=True, padx=10, pady=10)
        
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
        header_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header_frame, text="📁 Repository Manager", 
                 style='Header.TLabel').pack(side='left')
        
        # Repository list with actions
        list_frame = ttk.LabelFrame(self.left_frame, text="Repositories", padding=10)
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Action buttons
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill='x', pady=(0, 10))
        ttk.Button(button_frame, text="➕ Add Local Folder", 
                  command=self.add_local_repository, style='Action.TButton').pack(side='left', padx=2)
        ttk.Button(button_frame, text="🐙 Add GitHub Repo", 
                  command=self.add_github_repository, style='Action.TButton').pack(side='left', padx=2)
        ttk.Button(button_frame, text="🔍 Bulk Scanner", 
                  command=self.open_bulk_analyzer, style='Action.TButton').pack(side='left', padx=2)
        ttk.Button(button_frame, text="🚀 Profile Builder", 
                  command=self.open_profile_builder, style='Action.TButton').pack(side='left', padx=2)
        ttk.Button(button_frame, text="🗑️ Remove", 
                  command=self.remove_repository, style='Action.TButton').pack(side='left', padx=2)
        
        # Info note
        info_frame = ttk.Frame(list_frame)
        info_frame.pack(pady=(0, 5), fill='x')
        info_label = ttk.Label(info_frame, text="ℹ️  Add public GitHub repositories or local folders for analysis", 
                              font=('Segoe UI', 8), foreground='#666666')
        info_label.pack(side='left')
        
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
        
        self.repo_tree.pack(side='left', fill='both', expand=True)
        repo_scrollbar.pack(side='right', fill='y')
        
        self.repo_tree.bind('<<TreeviewSelect>>', self.on_repository_select)
        
        # Repository info panel
        info_frame = ttk.LabelFrame(self.left_frame, text="Repository Information", padding=10)
        info_frame.pack(fill='both', expand=True, pady=(0, 10))
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8, width=45, 
                                                  font=('Consolas', 9), state='disabled')
        self.info_text.pack(fill='both', expand=True)
        
        # Batch operations
        batch_frame = ttk.LabelFrame(self.left_frame, text="Batch Operations", padding=10)
        batch_frame.pack(fill='x')
        ttk.Button(batch_frame, text="🔍 Analyze All", 
                  command=self.analyze_all_repositories, style='Primary.TButton').pack(fill='x', pady=2)
        ttk.Button(batch_frame, text="📝 Generate All READMEs", 
                  command=self.generate_all_readmes, style='Primary.TButton').pack(fill='x', pady=2)
        ttk.Button(batch_frame, text="💾 Export All", 
                  command=self.export_all_readmes, style='Action.TButton').pack(fill='x', pady=2)
    
    def create_configuration_panel(self):
        """Create the configuration and preview panel."""
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill='both', expand=True)
        
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
        
        # Template selection with combobox for better space usage
        selection_frame = ttk.Frame(template_frame)
        selection_frame.pack(fill='x', pady=5)
        
        ttk.Label(selection_frame, text="Template:").pack(side='left')
        self.template_combo = ttk.Combobox(selection_frame, textvariable=self.template_var,
                                         values=templates, state='readonly', width=15)
        self.template_combo.pack(side='left', padx=5)
        self.template_combo.bind('<<ComboboxSelected>>', lambda e: self.on_template_change())
        
        # Template description
        self.template_desc_var = tk.StringVar()
        self.template_desc_label = ttk.Label(template_frame, textvariable=self.template_desc_var,
                                           foreground='gray', wraplength=300, font=('Arial', 9))
        self.template_desc_label.pack(anchor='w', pady=2)
        
        # Template actions
        template_actions = ttk.Frame(template_frame)
        template_actions.pack(fill='x', pady=5)
        
        ttk.Button(template_actions, text="🎨 Create Custom", 
                  command=self.open_template_builder, style='Action.TButton').pack(side='left')
        ttk.Button(template_actions, text="📁 Manage", 
                  command=self.manage_templates, style='Action.TButton').pack(side='left', padx=5)
        
        # Update description when template changes
        self.update_template_description()
        
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
        ttk.Button(action_frame, text="📤 Commit to Repo", 
                  command=self.commit_readme_to_repo, style='Action.TButton').pack(side='left', padx=5)
        
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
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        ttk.Button(button_frame, text="🔄 Refresh", 
                  command=self.refresh_preview, style='Action.TButton').pack(side='left', padx=2)
        ttk.Button(button_frame, text="📋 Copy to Clipboard", 
                  command=self.copy_preview_to_clipboard, style='Action.TButton').pack(side='left', padx=2)
        button_frame.pack(side='right')
        
        # Preview text area with enhanced styling
        self.preview_text = scrolledtext.ScrolledText(self.preview_frame, 
                                                     font=('Consolas', 10), 
                                                     wrap=tk.WORD,
                                                     bg='#f8f9fa',
                                                     fg='#24292f',
                                                     insertbackground='#24292f',
                                                     selectbackground='#0969da',
                                                     selectforeground='white')
        self.preview_text.insert('1.0', "Welcome to RepoReadme! 👋\n\nTo get started:\n1. Add a repository using the buttons above\n2. Select and analyze a repository\n3. Choose your template style\n4. Watch the magic happen here!\n\nYour professional README preview will appear with beautiful syntax highlighting.")
        
        # Setup syntax highlighting tags
        self._setup_markdown_tags()
        
        control_frame.pack(fill='x', pady=(0, 10))
        self.preview_text.pack(fill='both', expand=True)
    
    def _setup_markdown_tags(self):
        """Setup text tags for markdown syntax highlighting."""
        # Headers with GitHub-like styling
        self.preview_text.tag_configure("h1", font=('Segoe UI', 20, 'bold'), foreground='#1f2328', spacing1=10, spacing3=10)
        self.preview_text.tag_configure("h2", font=('Segoe UI', 16, 'bold'), foreground='#1f2328', spacing1=8, spacing3=8)
        self.preview_text.tag_configure("h3", font=('Segoe UI', 14, 'bold'), foreground='#1f2328', spacing1=6, spacing3=6)
        
        # Emphasis
        self.preview_text.tag_configure("bold", font=('Segoe UI', 10, 'bold'), foreground='#1f2328')
        self.preview_text.tag_configure("italic", font=('Segoe UI', 10, 'italic'), foreground='#656d76')
        
        # Code styling
        self.preview_text.tag_configure("code", font=('Consolas', 9), 
                                       background='#f6f8fa', foreground='#d73a49',
                                       relief='flat', borderwidth=1, lmargin1=2, lmargin2=2)
        self.preview_text.tag_configure("code_block", font=('Consolas', 9), 
                                       background='#f6f8fa', foreground='#24292f',
                                       relief='flat', lmargin1=15, rmargin=15, spacing1=5, spacing3=5)
        
        # Links
        self.preview_text.tag_configure("link", foreground='#0969da', underline=True)
        
        # Lists
        self.preview_text.tag_configure("list_item", foreground='#24292f', lmargin1=20, lmargin2=20)
        
        # Quotes
        self.preview_text.tag_configure("quote", foreground='#656d76', 
                                       background='#f6f8fa', lmargin1=15, rmargin=15, 
                                       spacing1=3, spacing3=3)
        
        # Table styling
        self.preview_text.tag_configure("table_header", font=('Segoe UI', 10, 'bold'), foreground='#1f2328')
        self.preview_text.tag_configure("table_row", foreground='#24292f')
        
        # Special styling
        self.preview_text.tag_configure("emoji", font=('Segoe UI Emoji', 12))
        self.preview_text.tag_configure("separator", foreground='#d0d7de')
        
        # Badges (shields.io style)
        self.preview_text.tag_configure("badge", font=('Segoe UI', 8), 
                                       background='#0969da', foreground='white',
                                       relief='flat', borderwidth=1)
    
    def copy_preview_to_clipboard(self):
        """Copy the preview content to clipboard."""
        # Temporarily enable to get content
        was_disabled = str(self.preview_text['state']) == 'disabled'
        if was_disabled:
            self.preview_text.config(state='normal')
        
        content = self.preview_text.get('1.0', tk.END).strip()
        
        # Restore state
        if was_disabled:
            self.preview_text.config(state='disabled')
        
        # Check if we have real content to copy
        welcome_messages = [
            "Welcome to RepoReadme!",
            "Select and analyze a repository",
            "Select a repository and configure template"
        ]
        
        if content and not any(msg in content for msg in welcome_messages):
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()  # Keep clipboard data
            
            # Show feedback
            self.status_var.set("README content copied to clipboard!")
            messagebox.showinfo("Copied! 📋", "README content has been copied to clipboard!")
        else:
            messagebox.showwarning("Nothing to Copy", "Generate a README first to copy content.")
    
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
        print("🔍 DEBUG: add_local_repository() called")
        folder_path = filedialog.askdirectory(title="Select Repository Folder")
        print(f"🔍 DEBUG: Selected folder path: {folder_path}")
        if folder_path:
            repo_name = os.path.basename(folder_path)
            print(f"🔍 DEBUG: Creating repo_item with name: {repo_name}")
            repo_item = RepositoryItem(repo_name, folder_path, "", "local")
            print(f"🔍 DEBUG: Repo item created: {repo_item.name}, type: {repo_item.repo_type}")
            self.repositories.append(repo_item)
            print(f"🔍 DEBUG: Added to repositories list. Total repos: {len(self.repositories)}")
            self.update_repository_list()
            print("🔍 DEBUG: Repository list updated")
            self.logger.info(f"Added local repository: {repo_name}", "GUI")
    
    def add_github_repository(self):
        """Add a GitHub repository."""
        print("🔍 DEBUG: add_github_repository() called")
        print(f"🔍 DEBUG: GitHub client available: {self.github_client is not None}")
        
        if self.github_client is None:
            print("🔍 DEBUG: GitHub client is None, showing error")
            messagebox.showerror("GitHub Unavailable", 
                               "GitHub client not available. Please ensure PyGithub is installed.")
            return
            
        # Update status to show we're opening dialog
        print("🔍 DEBUG: Setting status and opening dialog")
        self.status_var.set("Opening GitHub repository dialog...")
        
        dialog = GitHubRepoDialog(self.root, self.github_client)
        print(f"🔍 DEBUG: Dialog created, result: {dialog.result}")
        
        if dialog.result:
            print("🔍 DEBUG: Dialog has result, proceeding with addition")
            # Update status during addition
            self.status_var.set("Adding repository to list...")
            
            repo_name, repo_url = dialog.result
            print(f"🔍 DEBUG: Extracted repo_name: {repo_name}, repo_url: {repo_url}")
            
            repo_item = RepositoryItem(repo_name, "", repo_url, "github")
            print(f"🔍 DEBUG: Created GitHub repo_item: {repo_item.name}, type: {repo_item.repo_type}")
            
            print(f"🔍 DEBUG: Repositories before append: {len(self.repositories)}")
            self.repositories.append(repo_item)
            print(f"🔍 DEBUG: Repositories after append: {len(self.repositories)}")
            
            print("🔍 DEBUG: Calling update_repository_list()")
            self.update_repository_list()
            print("🔍 DEBUG: Repository list updated")
            
            # Show success feedback
            total_repos = len(self.repositories)
            self.status_var.set(f"Successfully added {repo_name} - Total: {total_repos} repositories")
            print(f"🔍 DEBUG: About to show success message for {repo_name}")
            messagebox.showinfo("Repository Added Successfully", 
                              f"✅ Added GitHub repository:\n{repo_name}\n\nTotal repositories: {total_repos}")
            
            # Select the newly added repository
            for item in self.repo_tree.get_children():
                item_text = self.repo_tree.item(item)['text']
                # Look for the full repo name or just the repo part
                if repo_name in item_text or repo_name.split('/')[-1] in item_text:
                    self.repo_tree.selection_set(item)
                    self.repo_tree.see(item)
                    # Trigger selection event
                    event = type('Event', (), {'widget': self.repo_tree})()
                    self.on_repository_select(event)
                    break
            
            self.logger.info(f"Added GitHub repository: {repo_name}", "GUI")
            
            # Automatically analyze the newly added GitHub repository
            if messagebox.askyesno("Auto-Analyze Repository", 
                                 f"Would you like to automatically analyze '{repo_name}' now?\n\nThis will clone the repository and extract project information."):
                # Update status and start analysis
                self.status_var.set(f"Starting analysis of {repo_name}...")
                self.selected_repo = repo_item  # Set the selected repo
                self.analyze_selected_repository()
            else:
                # Reset status to ready if user declined analysis
                self.status_var.set("Ready - Repository added successfully")
        else:
            # Dialog was cancelled, reset status
            self.status_var.set("Ready - Add repository cancelled")
    
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
        print(f"🔍 DEBUG: update_repository_list() called with {len(self.repositories)} repositories")
        
        # Clear existing items
        existing_items = self.repo_tree.get_children()
        print(f"🔍 DEBUG: Clearing {len(existing_items)} existing items from tree")
        for item in existing_items:
            self.repo_tree.delete(item)
        
        # Add repositories
        for i, repo in enumerate(self.repositories):
            print(f"🔍 DEBUG: Adding repo {i+1}: {repo.name} (type: {repo.repo_type}, status: {repo.status})")
            type_icon = "📁" if repo.repo_type == "local" else "🐙"
            status_icon = {
                "pending": "⏳",
                "analyzing": "🔍", 
                "completed": "✅",
                "error": "❌"
            }.get(repo.status, "❓")
            
            tree_item = self.repo_tree.insert('', 'end', text=f"{type_icon} {repo.name}",
                                values=(repo.repo_type, f"{status_icon} {repo.status}"))
            print(f"🔍 DEBUG: Inserted tree item: {tree_item}")
        
        print(f"🔍 DEBUG: Repository list update completed. Tree now has {len(self.repo_tree.get_children())} items")
    
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
                # For GitHub repos, clone to temp directory and analyze
                temp_path = None
                try:
                    # Update UI to show cloning status
                    self.root.after(0, lambda: self._update_clone_status("Cloning repository..."))
                    
                    temp_path = self._clone_github_repository(repo_item)
                    
                    # Update UI to show analysis status  
                    self.root.after(0, lambda: self._update_clone_status("Analyzing cloned repository..."))
                    
                    # Analyze the cloned repository
                    metadata = self.analyzer.analyze_repository(temp_path, repo_item.name, repo_item.url)
                    
                finally:
                    # Clean up temporary directory
                    if temp_path:
                        self._cleanup_temp_directory(temp_path)
            
            repo_item.metadata = metadata
            repo_item.status = "completed"
            
            # Update UI
            self.root.after(0, lambda: self._update_analysis_ui(repo_item, "completed"))
            
        except Exception as e:
            repo_item.status = "error"
            error_msg = str(e)  # Capture the error message
            self.logger.error(f"Repository analysis failed: {e}", "ANALYSIS", e)
            self.root.after(0, lambda: self._update_analysis_ui(repo_item, "error", error_msg))
        
        finally:
            self.is_analyzing = False
    
    def _clone_github_repository(self, repo_item: RepositoryItem) -> str:
        """Clone a GitHub repository to a temporary directory."""
        try:
            # Create temporary directory for the cloned repo
            temp_base = tempfile.mkdtemp(prefix="reporeadme_temp_")
            repo_name_safe = repo_item.name.replace('/', '_')
            temp_dir = os.path.join(temp_base, repo_name_safe)
            
            # Clone the repository
            self.logger.info(f"Cloning GitHub repository: {repo_item.url}", "GITHUB_CLONE")
            
            # Use git clone command
            result = subprocess.run([
                'git', 'clone', '--depth', '1', repo_item.url, temp_dir
            ], capture_output=True, text=True, timeout=120)  # Increased timeout
            
            if result.returncode != 0:
                # Cleanup on failure
                shutil.rmtree(temp_base, ignore_errors=True)
                raise Exception(f"Git clone failed: {result.stderr}")
            
            self.logger.info(f"Successfully cloned repository to: {temp_dir}", "GITHUB_CLONE")
            return temp_dir
            
        except subprocess.TimeoutExpired:
            # Cleanup on timeout
            if 'temp_base' in locals():
                shutil.rmtree(temp_base, ignore_errors=True)
            raise Exception("Repository cloning timed out (2 minutes)")
        except Exception as e:
            self.logger.error(f"Failed to clone GitHub repository: {e}", "GITHUB_CLONE")
            raise
    
    def _cleanup_temp_directory(self, temp_path: str):
        """Clean up temporary directory."""
        try:
            if os.path.exists(temp_path):
                # Clean up the parent temp directory (contains the cloned repo)
                parent_temp = os.path.dirname(temp_path)
                if parent_temp and "reporeadme_temp_" in parent_temp:
                    shutil.rmtree(parent_temp, ignore_errors=True)
                    self.logger.info(f"Cleaned up temporary directory: {parent_temp}", "CLEANUP")
                else:
                    # Fallback to just the repo directory
                    shutil.rmtree(temp_path, ignore_errors=True)
                    self.logger.info(f"Cleaned up temporary directory: {temp_path}", "CLEANUP")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp directory {temp_path}: {e}", "CLEANUP")
    
    def _update_clone_status(self, message: str):
        """Update the status message during cloning/analysis."""
        if hasattr(self, 'progress_var'):
            self.progress_var.set(message)
        if hasattr(self, 'status_var'):
            self.status_var.set(message)
    
    
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
            
            # Update preview with syntax highlighting
            self._update_preview_with_highlighting(readme_content)
            
            # Switch to preview tab
            self.notebook.select(1)
            
            self.status_var.set(f"README generated for {self.selected_repo.name}")
            
        except Exception as e:
            self.logger.error(f"README generation failed: {e}", "GENERATION", e)
            messagebox.showerror("Generation Error", f"Failed to generate README: {str(e)}")
    
    def save_readme(self):
        """Save the generated README to file."""
        if not self.selected_repo:
            messagebox.showwarning("No Selection", "Please select a repository first.")
            return
        
        # Check if we have a README to save (either generated or from preview)
        readme_content = ""
        if self.selected_repo.generated_readme:
            readme_content = self.selected_repo.generated_readme
        else:
            # Try to get content from preview area
            preview_content = self.preview_text.get('1.0', tk.END).strip()
            if preview_content and preview_content != "Select a repository and configure template to see preview...":
                readme_content = preview_content
            else:
                messagebox.showwarning("No README", "Generate a README first.")
                return
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Default filename with sanitized repo name
        safe_name = re.sub(r'[^\w\-_.]', '_', self.selected_repo.name)
        default_name = f"{safe_name}_README.md"
        
        # Get save location, defaulting to output directory
        file_path = filedialog.asksaveasfilename(
            title="Save README As",
            initialdir=output_dir,
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                
                messagebox.showinfo("Success", f"README saved successfully!\n\n📁 Location: {file_path}")
                self.status_var.set(f"README saved to {os.path.basename(file_path)}")
                
                self.logger.log_readme_generation(
                    self.selected_repo.name, self.template_var.get(), file_path, True
                )
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save README: {str(e)}")
                self.logger.error(f"README save failed: {e}", "SAVE", e)
    
    def commit_readme_to_repo(self):
        """Commit the generated README directly to the repository."""
        if not self.selected_repo:
            messagebox.showwarning("No Selection", "Please select a repository first.")
            return
        
        # Check if we have a README to commit
        readme_content = ""
        if self.selected_repo.generated_readme:
            readme_content = self.selected_repo.generated_readme
        else:
            # Try to get content from preview area
            preview_content = self.preview_text.get('1.0', tk.END).strip()
            if preview_content and "Select and analyze a repository" not in preview_content:
                readme_content = preview_content
            else:
                messagebox.showwarning("No README", "Generate a README first.")
                return
        
        # Show commit dialog
        commit_dialog = CommitReadmeDialog(self.root, self.selected_repo, readme_content, self.logger)
        
        if commit_dialog.success:
            self.status_var.set(f"README committed to {self.selected_repo.name}")
            messagebox.showinfo("Success", f"README successfully committed to {self.selected_repo.name}!")
    
    # Template Management
    
    def update_template_description(self):
        """Update the template description label."""
        template = self.template_var.get()
        description = self.template_engine.get_template_description(template)
        self.template_desc_var.set(description)
    
    def open_template_builder(self):
        """Open the custom template builder dialog."""
        try:
            result = create_custom_template_builder(self.root)
            if result:
                # Add the custom template to the available templates
                custom_name = f"custom_{result.name.lower().replace(' ', '_')}"
                
                # Update template dropdown
                current_values = list(self.template_combo['values'])
                if custom_name not in current_values:
                    current_values.append(custom_name)
                    self.template_combo['values'] = current_values
                
                # Select the new template
                self.template_var.set(custom_name)
                self.update_template_description()
                self.on_template_change()
                
                messagebox.showinfo("Success", f"Custom template '{result.name}' created successfully!")
                
        except Exception as e:
            messagebox.showerror("Template Builder Error", f"Failed to open template builder: {str(e)}")
    
    def manage_templates(self):
        """Open the template management dialog."""
        try:
            from pathlib import Path
            import subprocess
            import platform
            import shutil
            
            # Create the custom templates folder
            templates_dir = Path.home() / ".reporeadme" / "custom_templates"
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to open folder in file manager with fallback
            opened = False
            
            try:
                if platform.system() == "Windows":
                    os.startfile(str(templates_dir))
                    opened = True
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(templates_dir)], check=True)
                    opened = True
                else:  # Linux
                    # Try common Linux file managers
                    file_managers = ["xdg-open", "nautilus", "dolphin", "thunar", "pcmanfm", "nemo"]
                    for fm in file_managers:
                        if shutil.which(fm):
                            subprocess.run([fm, str(templates_dir)], check=True)
                            opened = True
                            break
                    
                    if not opened:
                        # If no file manager found, just show the path
                        raise FileNotFoundError("No suitable file manager found")
                        
            except (subprocess.CalledProcessError, FileNotFoundError, OSError):
                # If file manager fails, show the path instead
                messagebox.showinfo("Templates Folder", 
                                  f"Custom templates folder created:\n\n{templates_dir}\n\n"
                                  f"Copy this path to open manually in your file manager.")
                return
            
            if opened:
                messagebox.showinfo("Templates", f"Custom templates folder opened:\n{templates_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to access templates folder: {str(e)}")
    
    def open_bulk_analyzer(self):
        """Open the bulk repository analyzer dialog."""
        try:
            # Create and show the bulk analyzer dialog
            bulk_dialog = create_bulk_analyzer(self.root)
            
            # If repositories were discovered and added, refresh the main GUI
            if hasattr(bulk_dialog, 'discovered_repos') and bulk_dialog.discovered_repos:
                # Add discovered repositories to main repository list
                for repo_info in bulk_dialog.discovered_repos:
                    if repo_info.selected_for_analysis:  # Only add selected repos
                        repo_item = RepositoryItem(
                            name=repo_info.full_name,
                            path="",
                            url=repo_info.clone_url,
                            repo_type="github"
                        )
                        self.repositories.append(repo_item)
                
                self.update_repository_list()
                self.status_var.set(f"Added {len([r for r in bulk_dialog.discovered_repos if r.selected_for_analysis])} repositories from bulk scanner")
                
        except Exception as e:
            self.logger.error(f"Failed to open bulk analyzer: {e}", "BULK_ANALYZER")
            messagebox.showerror("Bulk Analyzer Error", f"Failed to open bulk analyzer: {str(e)}")
    
    def open_profile_builder(self):
        """Open the GitHub Profile Builder dialog."""
        try:
            # Create and show the profile builder dialog
            profile_dialog = create_profile_builder(self.root)
            
            # The profile builder is self-contained and handles its own exports
            # No need to integrate with the main repository list
            self.logger.info("GitHub Profile Builder opened")
                
        except Exception as e:
            self.logger.error(f"Failed to open GitHub Profile Builder: {e}", "PROFILE_BUILDER")
            messagebox.showerror("Profile Builder Error", f"Failed to open GitHub Profile Builder: {str(e)}")
    
    # Event Handlers
    
    def on_template_change(self):
        """Handle template selection change."""
        self.update_template_description()
        if self.selected_repo and self.selected_repo.metadata:
            self.refresh_preview()
    
    def on_option_change(self):
        """Handle option change."""
        if self.selected_repo and self.selected_repo.metadata:
            self.refresh_preview()
    
    def refresh_preview(self):
        """Refresh the README preview."""
        if not self.selected_repo or not self.selected_repo.metadata:
            self.preview_text.config(state='normal')
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', "Select and analyze a repository to see preview...\n\nOnce you've analyzed a repository, your professional README will appear here with:\n✨ Beautiful syntax highlighting\n🎨 GitHub-style formatting\n📋 Copy-to-clipboard functionality")
            self.preview_text.config(state='disabled')
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
            
            # Update preview with syntax highlighting
            self._update_preview_with_highlighting(preview_content)
            
        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Preview Error: {str(e)}")
    
    def _update_preview_with_highlighting(self, content: str):
        """Update preview with markdown syntax highlighting."""
        self.preview_text.config(state='normal')
        self.preview_text.delete('1.0', tk.END)
        
        lines = content.split('\n')
        current_line = 1
        in_code_block = False
        in_table = False
        
        for line in lines:
            line_start = self.preview_text.index(tk.END + "-1c linestart")
            
            # Insert the line first
            self.preview_text.insert(tk.END, line + '\n')
            
            line_end = self.preview_text.index(tk.END + "-1c lineend")
            
            # Apply line-level highlighting
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                self.preview_text.tag_add("code_block", line_start, line_end)
            elif in_code_block:
                self.preview_text.tag_add("code_block", line_start, line_end)
            elif line.startswith('# '):
                self.preview_text.tag_add("h1", line_start, line_end)
            elif line.startswith('## '):
                self.preview_text.tag_add("h2", line_start, line_end)
            elif line.startswith('### '):
                self.preview_text.tag_add("h3", line_start, line_end)
            elif line.startswith('> '):
                self.preview_text.tag_add("quote", line_start, line_end)
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                self.preview_text.tag_add("list_item", line_start, line_end)
            elif line.startswith('|') and '|' in line[1:]:
                # Table detection
                in_table = True
                if '---' in line:
                    self.preview_text.tag_add("table_header", line_start, line_end)
                else:
                    self.preview_text.tag_add("table_row", line_start, line_end)
            elif line.strip() == '---':
                self.preview_text.tag_add("separator", line_start, line_end)
            else:
                in_table = False
            
            # Apply inline highlighting if not in code block
            if not in_code_block:
                self._apply_inline_highlighting(line, line_start, current_line)
            
            current_line += 1
        
        self.preview_text.config(state='disabled')
    
    def _apply_inline_highlighting(self, line: str, line_start: str, line_num: int):
        """Apply inline highlighting for code, bold, links, etc."""
        # Inline code `code`
        import re
        for match in re.finditer(r'`([^`]+)`', line):
            start_col = match.start()
            end_col = match.end()
            start_pos = f"{line_num}.{start_col}"
            end_pos = f"{line_num}.{end_col}"
            self.preview_text.tag_add("code", start_pos, end_pos)
        
        # Bold **text**
        for match in re.finditer(r'\*\*([^*]+)\*\*', line):
            start_col = match.start()
            end_col = match.end()
            start_pos = f"{line_num}.{start_col}"
            end_pos = f"{line_num}.{end_col}"
            self.preview_text.tag_add("bold", start_pos, end_pos)
        
        # Links [text](url)
        for match in re.finditer(r'\[([^\]]+)\]\([^)]+\)', line):
            start_col = match.start()
            end_col = match.end()
            start_pos = f"{line_num}.{start_col}"
            end_pos = f"{line_num}.{end_col}"
            self.preview_text.tag_add("link", start_pos, end_pos)
        
        # Badge images ![alt](url)
        for match in re.finditer(r'!\[([^\]]*)\]\([^)]+\)', line):
            start_col = match.start()
            end_col = match.end()
            start_pos = f"{line_num}.{start_col}"
            end_pos = f"{line_num}.{end_col}"
            self.preview_text.tag_add("badge", start_pos, end_pos)
    
    
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
                    # Analyze GitHub repository
                    temp_path = None
                    try:
                        # Clone the repository to temporary location
                        temp_path = self._clone_github_repository(repo)
                        
                        # Analyze the cloned repository
                        metadata = self.analyzer.analyze_repository(temp_path, repo.name, repo.url)
                        repo.metadata = metadata
                        repo.status = "completed"
                        
                    finally:
                        # Clean up temporary directory
                        if temp_path:
                            self._cleanup_temp_directory(temp_path)
            
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
        print("🔍 DEBUG: GitHubRepoDialog.__init__() called")
        self.result = None
        self.github_client = github_client
        print(f"🔍 DEBUG: Dialog initialized with github_client: {github_client is not None}")
        
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
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(self.dialog)
        self.progress_label = ttk.Label(self.progress_frame, text="Validating repository...")
        self.progress_label.pack(pady=5)
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', padx=20)
        
        # Buttons
        self.button_frame = ttk.Frame(self.dialog)
        self.add_button = ttk.Button(self.button_frame, text="Add", command=self.on_add)
        self.add_button.pack(side='left', padx=5)
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side='left')
        self.button_frame.pack(pady=20)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.on_add())
        
        # Wait for dialog to complete
        print("🔍 DEBUG: Starting dialog wait_window()")
        parent.wait_window(self.dialog)
        print(f"🔍 DEBUG: Dialog completed, final result: {self.result}")
        
        # Additional debug info about the result
        if self.result:
            repo_name, repo_url = self.result
            print(f"🔍 DEBUG: Successfully captured result - Name: '{repo_name}', URL: '{repo_url}'")
    
    def on_add(self):
        """Handle add button click."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Invalid URL", "Please enter a repository URL.")
            return
        
        # Validate GitHub URL format
        if 'github.com' not in url:
            messagebox.showerror("Invalid URL", "Please enter a valid GitHub repository URL.\nExample: https://github.com/username/repository")
            return
        
        # Parse repository name from URL
        try:
            parts = url.rstrip('/').split('/')
            if len(parts) < 2:
                raise ValueError("Invalid URL format")
            
            owner = parts[-2]
            repo = parts[-1]
            
            # Remove .git if present
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            repo_name = f"{owner}/{repo}"
            
            # Start validation in background thread
            self._start_validation(repo_name, url)
            
        except Exception as e:
            messagebox.showerror("Invalid URL", 
                               f"Please enter a valid GitHub repository URL.\nError: {str(e)}\n\nExample: https://github.com/username/repository")
    
    def _start_validation(self, repo_name, url):
        """Start repository validation in background thread."""
        # Show progress UI
        self.progress_frame.pack(pady=10)
        self.progress_bar.start()
        
        # Disable buttons during validation
        self.add_button.config(state='disabled')
        self.cancel_button.config(text='Cancel', command=self._cancel_validation)
        
        # Start validation thread
        import threading
        self.validation_thread = threading.Thread(
            target=self._validate_repository_thread,
            args=(repo_name, url),
            daemon=True
        )
        self.validation_cancelled = False
        self.validation_thread.start()
    
    def _validate_repository_thread(self, repo_name, url):
        """Validate repository in background thread."""
        try:
            # Update progress
            self.dialog.after(0, lambda: self.progress_label.config(text=f"Validating {repo_name}..."))
            
            # Test if repository exists (if github_client is available)
            if hasattr(self, 'github_client') and self.github_client:
                try:
                    # Add a timeout for the GitHub API call
                    import socket
                    socket.setdefaulttimeout(10)  # 10 second timeout
                    
                    test_repo = self.github_client.get_repo(repo_name)
                    
                    if self.validation_cancelled:
                        return
                    
                    # Repository found - show success and close dialog
                    self.dialog.after(0, lambda: self._validation_success(repo_name, url, test_repo))
                    
                except Exception as e:
                    if self.validation_cancelled:
                        return
                        
                    if "404" in str(e) or "Not Found" in str(e):
                        self.dialog.after(0, lambda: self._validation_error(
                            f"❌ Repository '{repo_name}' not found or is private.\nPlease check the URL and try again."))
                    else:
                        # Other API error (timeout, network, etc.), but let's continue anyway
                        print(f"🔍 DEBUG: GitHub API error (continuing anyway): {e}")
                        self.dialog.after(0, lambda: self._validation_warning(repo_name, url))
            else:
                # No GitHub client, proceed without validation
                if self.validation_cancelled:
                    return
                self.dialog.after(0, lambda: self._validation_success(repo_name, url, None))
                
        except Exception as e:
            if not self.validation_cancelled:
                self.dialog.after(0, lambda: self._validation_error(f"Validation error: {str(e)}"))
    
    def _validation_success(self, repo_name, url, test_repo):
        """Handle successful validation."""
        print(f"🔍 DEBUG: _validation_success called for {repo_name}")
        self._hide_progress()
        
        if test_repo:
            print(f"🔍 DEBUG: Test repo found: {test_repo.full_name}")
            messagebox.showinfo("Repository Found", 
                              f"✅ Repository found: {test_repo.full_name}\n{test_repo.description or 'No description'}")
        else:
            print("🔍 DEBUG: No test repo (proceeding without GitHub validation)")
        
        print(f"🔍 DEBUG: Setting dialog result: ({repo_name}, {url})")
        self.result = (repo_name, url)
        print("🔍 DEBUG: Destroying dialog")
        self.dialog.destroy()
    
    def _validation_warning(self, repo_name, url):
        """Handle validation warning (API error but continue)."""
        print(f"🔍 DEBUG: _validation_warning called for {repo_name}")
        self._hide_progress()
        messagebox.showwarning("Validation Warning", 
                             f"⚠️  Could not validate repository '{repo_name}'.\nProceeding anyway...")
        print(f"🔍 DEBUG: Setting dialog result (warning): ({repo_name}, {url})")
        self.result = (repo_name, url)
        print("🔍 DEBUG: Destroying dialog (warning)")
        self.dialog.destroy()
    
    def _validation_error(self, error_msg):
        """Handle validation error."""
        print(f"🔍 DEBUG: _validation_error called: {error_msg}")
        self._hide_progress()
        messagebox.showerror("Repository Not Found", error_msg)
        print("🔍 DEBUG: Error dialog shown, dialog result remains None")
    
    def _cancel_validation(self):
        """Cancel ongoing validation."""
        self.validation_cancelled = True
        self._hide_progress()
    
    def _hide_progress(self):
        """Hide progress UI and restore buttons."""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        self.add_button.config(state='normal')
        self.cancel_button.config(text='Cancel', command=self.on_cancel)
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.dialog.destroy()


class LoadingDialog:
    """Simple loading dialog with progress indicator."""
    
    def __init__(self, parent, message="Loading..."):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Loading")
        self.dialog.geometry("300x100")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 150
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 50
        self.dialog.geometry(f"+{x}+{y}")
        
        # Content
        ttk.Label(self.dialog, text=message).pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start()
    
    def close(self):
        """Close the loading dialog."""
        if self.dialog.winfo_exists():
            self.progress.stop()
            self.dialog.destroy()


class CommitReadmeDialog:
    """Dialog for committing README to repository."""
    
    def __init__(self, parent, repo_item, readme_content, logger):
        self.success = False
        self.repo_item = repo_item
        self.readme_content = readme_content
        self.logger = logger
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📤 Commit README to Repository")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 300
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 200
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        
        # Wait for dialog to complete
        parent.wait_window(self.dialog)
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(header_frame, text=f"📤 Commit README to: {self.repo_item.name}", 
                 font=('Arial', 12, 'bold')).pack()
        
        # Repository info
        info_frame = ttk.LabelFrame(self.dialog, text="Repository Information", padding=10)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(info_frame, text=f"Type: {self.repo_item.repo_type}").pack(anchor='w')
        if self.repo_item.path:
            ttk.Label(info_frame, text=f"Path: {self.repo_item.path}").pack(anchor='w')
        if self.repo_item.url:
            ttk.Label(info_frame, text=f"URL: {self.repo_item.url}").pack(anchor='w')
        
        # Commit options
        options_frame = ttk.LabelFrame(self.dialog, text="Commit Options", padding=10)
        options_frame.pack(fill='x', padx=20, pady=10)
        
        # Commit message
        ttk.Label(options_frame, text="Commit Message:").pack(anchor='w')
        self.commit_msg_var = tk.StringVar(value="📝 Add/Update README.md via RepoReadme")
        commit_entry = ttk.Entry(options_frame, textvariable=self.commit_msg_var, width=70)
        commit_entry.pack(fill='x', pady=5)
        
        # Branch selection for GitHub repos
        if self.repo_item.repo_type == "github":
            ttk.Label(options_frame, text="Target Branch:").pack(anchor='w', pady=(10, 0))
            self.branch_var = tk.StringVar(value="main")
            branch_frame = ttk.Frame(options_frame)
            branch_frame.pack(fill='x', pady=5)
            
            for branch in ["main", "master", "develop"]:
                ttk.Radiobutton(branch_frame, text=branch, variable=self.branch_var, 
                               value=branch).pack(side='left', padx=5)
        
        # File options
        self.overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Overwrite existing README.md", 
                       variable=self.overwrite_var).pack(anchor='w', pady=5)
        
        self.create_pr_var = tk.BooleanVar(value=False)
        if self.repo_item.repo_type == "github":
            ttk.Checkbutton(options_frame, text="Create pull request (for GitHub repos)", 
                           variable=self.create_pr_var).pack(anchor='w')
        
        # Preview
        preview_frame = ttk.LabelFrame(self.dialog, text="README Preview (first 500 chars)", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        preview_text = scrolledtext.ScrolledText(preview_frame, height=8, wrap=tk.WORD, 
                                               font=('Consolas', 9), state='disabled')
        preview_text.pack(fill='both', expand=True)
        
        # Show preview
        preview_text.config(state='normal')
        preview_content = self.readme_content[:500] + ("..." if len(self.readme_content) > 500 else "")
        preview_text.insert('1.0', preview_content)
        preview_text.config(state='disabled')
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="📤 Commit README", 
                  command=self.commit_readme, style='Primary.TButton').pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel, style='Action.TButton').pack(side='right')
    
    def commit_readme(self):
        """Perform the actual commit."""
        try:
            commit_msg = self.commit_msg_var.get().strip()
            if not commit_msg:
                messagebox.showerror("Invalid Input", "Please enter a commit message.")
                return
            
            # Show progress
            progress_dialog = LoadingDialog(self.dialog, "Committing README...")
            
            try:
                if self.repo_item.repo_type == "local":
                    success = self._commit_to_local_repo(commit_msg)
                elif self.repo_item.repo_type == "github":
                    branch = self.branch_var.get() if hasattr(self, 'branch_var') else "main"
                    success = self._commit_to_github_repo(commit_msg, branch)
                else:
                    success = False
                    messagebox.showerror("Unsupported", "Repository type not supported for commits.")
            
            finally:
                progress_dialog.close()
            
            if success:
                self.success = True
                self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Commit Error", f"Failed to commit README: {str(e)}")
            self.logger.error(f"README commit failed: {e}", "COMMIT")
    
    def _commit_to_local_repo(self, commit_msg):
        """Commit README to local Git repository."""
        try:
            import git
            
            if not self.repo_item.path or not os.path.exists(self.repo_item.path):
                messagebox.showerror("Invalid Path", "Repository path not found.")
                return False
            
            # Check if it's a git repository
            try:
                repo = git.Repo(self.repo_item.path)
            except git.InvalidGitRepositoryError:
                if messagebox.askyesno("Not a Git Repo", 
                                     "This folder is not a Git repository. Initialize it?"):
                    repo = git.Repo.init(self.repo_item.path)
                else:
                    return False
            
            # Write README.md file
            readme_path = os.path.join(self.repo_item.path, "README.md")
            
            if os.path.exists(readme_path) and not self.overwrite_var.get():
                if not messagebox.askyesno("File Exists", "README.md already exists. Overwrite?"):
                    return False
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(self.readme_content)
            
            # Add and commit
            repo.index.add(['README.md'])
            repo.index.commit(commit_msg)
            
            self.logger.info(f"README committed to local repo: {self.repo_item.path}", "COMMIT")
            return True
            
        except Exception as e:
            messagebox.showerror("Git Error", f"Failed to commit to local repository: {str(e)}")
            self.logger.error(f"Local commit failed: {e}", "COMMIT")
            return False
    
    def _commit_to_github_repo(self, commit_msg, branch):
        """Commit README to GitHub repository."""
        try:
            from github import Github
            import base64
            
            if not self.repo_item.url:
                messagebox.showerror("No URL", "GitHub repository URL not available.")
                return False
            
            # Parse repository name from URL
            repo_name = self.repo_item.name
            if '/' not in repo_name:
                messagebox.showerror("Invalid Repo", "Cannot determine GitHub repository name.")
                return False
            
            # Initialize GitHub client (this requires authentication for commits)
            github_token = self._get_github_token()
            if not github_token:
                messagebox.showwarning("Authentication Required", 
                                     "GitHub token required for commits. This feature needs authentication setup.")
                return False
            
            github_client = Github(github_token)
            repo = github_client.get_repo(repo_name)
            
            # Check if README.md already exists
            try:
                existing_file = repo.get_contents("README.md", ref=branch)
                if not self.overwrite_var.get():
                    if not messagebox.askyesno("File Exists", "README.md already exists. Overwrite?"):
                        return False
                
                # Update existing file
                repo.update_file(
                    path="README.md",
                    message=commit_msg,
                    content=self.readme_content,
                    sha=existing_file.sha,
                    branch=branch
                )
            except:
                # Create new file
                repo.create_file(
                    path="README.md",
                    message=commit_msg,
                    content=self.readme_content,
                    branch=branch
                )
            
            # Create PR if requested
            if self.create_pr_var.get() and branch != "main":
                try:
                    pr = repo.create_pull(
                        title=f"Add/Update README.md",
                        body=f"Automated README update via RepoReadme\n\n{commit_msg}",
                        head=branch,
                        base="main"
                    )
                    messagebox.showinfo("Pull Request Created", f"PR created: {pr.html_url}")
                except Exception as pr_error:
                    self.logger.warning(f"Failed to create PR: {pr_error}", "COMMIT")
            
            self.logger.info(f"README committed to GitHub repo: {repo_name}", "COMMIT")
            return True
            
        except Exception as e:
            messagebox.showerror("GitHub Error", f"Failed to commit to GitHub: {str(e)}")
            self.logger.error(f"GitHub commit failed: {e}", "COMMIT")
            return False
    
    def _get_github_token(self):
        """Get GitHub token from user or config."""
        # Try to get from config first (basic implementation)
        try:
            config_path = os.path.expanduser("~/.reporeadme/github_token.txt")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        return token
        except:
            pass
        
        # Prompt user for token
        token_dialog = GitHubTokenDialog(self.dialog)
        return token_dialog.token if token_dialog.token else None
    
    def cancel(self):
        """Cancel the commit dialog."""
        self.dialog.destroy()


class GitHubTokenDialog:
    """Simple dialog for GitHub token input."""
    
    def __init__(self, parent):
        self.token = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔑 GitHub Authentication Required")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 150
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        
        # Wait for dialog
        parent.wait_window(self.dialog)
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(header_frame, text="🔑 GitHub Personal Access Token Required", 
                 font=('Arial', 12, 'bold')).pack()
        
        # Instructions
        info_frame = ttk.LabelFrame(self.dialog, text="Setup Instructions", padding=10)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        instructions = [
            "1. Go to GitHub.com → Settings → Developer settings → Personal access tokens",
            "2. Click 'Generate new token' and select required scopes:",
            "   • repo (for private repositories)",
            "   • public_repo (for public repositories)",
            "3. Copy the generated token and paste it below",
            "4. The token will be saved securely for future use"
        ]
        
        for instruction in instructions:
            ttk.Label(info_frame, text=instruction, font=('Arial', 9)).pack(anchor='w', pady=1)
        
        # Token input
        token_frame = ttk.LabelFrame(self.dialog, text="Access Token", padding=10)
        token_frame.pack(fill='x', padx=20, pady=10)
        
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(token_frame, textvariable=self.token_var, width=60, show='*')
        token_entry.pack(fill='x', pady=5)
        token_entry.focus()
        
        # Save option
        self.save_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(token_frame, text="Save token securely for future use", 
                       variable=self.save_var).pack(anchor='w', pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="✅ Save & Continue", 
                  command=self.save_token).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side='right')
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.save_token())
    
    def save_token(self):
        """Save the token and close dialog."""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Invalid Token", "Please enter a valid GitHub token.")
            return
        
        self.token = token
        
        # Save token if requested
        if self.save_var.get():
            try:
                config_dir = os.path.expanduser("~/.reporeadme")
                os.makedirs(config_dir, exist_ok=True)
                
                token_path = os.path.join(config_dir, "github_token.txt")
                with open(token_path, 'w', encoding='utf-8') as f:
                    f.write(token)
                
                # Set secure permissions (owner read-only)
                os.chmod(token_path, 0o600)
                
            except Exception as e:
                messagebox.showwarning("Save Failed", f"Failed to save token: {str(e)}")
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()


# Compatibility alias for CI testing
RepoReadmeApp = RepoReadmeGUI

def main():
    """Main entry point for the GUI application."""
    app = RepoReadmeGUI()
    app.run()

if __name__ == '__main__':
    main()