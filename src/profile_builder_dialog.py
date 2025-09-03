#!/usr/bin/env python3
"""
GitHub Profile Builder Dialog

GUI interface for building comprehensive GitHub profiles from user repositories.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import asyncio
import json
import os
import time
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from .profile_builder import GitHubProfileBuilder, ProfileBuilderConfig, ProfileExporter
    from .config.github_auth import GitHubAuthManager
    from .utils.logger import get_logger
except ImportError:
    from profile_builder import GitHubProfileBuilder, ProfileBuilderConfig, ProfileExporter
    from config.github_auth import GitHubAuthManager
    from utils.logger import get_logger


class ProfileBuilderDialog:
    """Dialog for building GitHub profiles."""
    
    def __init__(self, parent):
        """Initialize the profile builder dialog."""
        self.parent = parent
        self.logger = get_logger()
        self.auth_manager = GitHubAuthManager()
        
        # Create main dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🚀 GitHub Profile Builder")
        self.dialog.geometry("900x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        # State variables
        self.current_profile = None
        self.is_building = False
        self.build_task = None
        
        # Configuration
        self.config = ProfileBuilderConfig()
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Profile Configuration
        self.create_config_tab()
        
        # Tab 2: Build Profile
        self.create_build_tab()
        
        # Tab 3: Profile Results
        self.create_results_tab()
        
        # Tab 4: Export Options
        self.create_export_tab()
        
        # Bottom buttons
        self.create_bottom_buttons()
    
    def create_config_tab(self):
        """Create the profile configuration tab."""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuration")
        
        # Scrollable frame
        canvas = tk.Canvas(config_frame)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # GitHub Authentication
        auth_frame = ttk.LabelFrame(scrollable_frame, text="🔑 GitHub Authentication", padding=15)
        auth_frame.pack(fill='x', padx=10, pady=10)
        
        # Username
        ttk.Label(auth_frame, text="GitHub Username:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(auth_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        # GitHub Token
        ttk.Label(auth_frame, text="GitHub Token:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5)
        self.github_token_var = tk.StringVar()
        token_entry = ttk.Entry(auth_frame, textvariable=self.github_token_var, 
                               width=50, show='*')
        token_entry.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        ttk.Button(auth_frame, text="Test Connection", 
                  command=self.test_github_connection).grid(row=1, column=2, padx=5)
        
        auth_frame.columnconfigure(1, weight=1)
        
        # Analysis Settings
        analysis_frame = ttk.LabelFrame(scrollable_frame, text="📊 Analysis Settings", padding=15)
        analysis_frame.pack(fill='x', padx=10, pady=10)
        
        # Repository filters
        filters_subframe = ttk.Frame(analysis_frame)
        filters_subframe.pack(fill='x', pady=5)
        
        self.include_forks_var = tk.BooleanVar(value=self.config.include_forks)
        self.include_archived_var = tk.BooleanVar(value=self.config.include_archived)
        
        ttk.Checkbutton(filters_subframe, text="🍴 Include Forked Repositories", 
                       variable=self.include_forks_var).pack(anchor='w')
        ttk.Checkbutton(filters_subframe, text="📦 Include Archived Repositories", 
                       variable=self.include_archived_var).pack(anchor='w')
        
        # Repository size filter
        size_frame = ttk.Frame(analysis_frame)
        size_frame.pack(fill='x', pady=5)
        ttk.Label(size_frame, text="Minimum Repository Size (KB):").pack(side='left')
        self.min_size_var = tk.IntVar(value=self.config.min_repo_size_kb)
        ttk.Spinbox(size_frame, from_=0, to=1000, textvariable=self.min_size_var, 
                   width=10).pack(side='left', padx=10)
        
        # Max repositories to analyze
        max_repos_frame = ttk.Frame(analysis_frame)
        max_repos_frame.pack(fill='x', pady=5)
        ttk.Label(max_repos_frame, text="Max Repositories to Analyze:").pack(side='left')
        self.max_repos_var = tk.IntVar(value=self.config.max_repos_to_analyze or 500)
        ttk.Spinbox(max_repos_frame, from_=10, to=2000, increment=50,
                   textvariable=self.max_repos_var, width=10).pack(side='left', padx=10)
        
        # Portfolio Settings
        portfolio_frame = ttk.LabelFrame(scrollable_frame, text="🎨 Portfolio Settings", padding=15)
        portfolio_frame.pack(fill='x', padx=10, pady=10)
        
        # Featured projects settings
        featured_frame = ttk.Frame(portfolio_frame)
        featured_frame.pack(fill='x', pady=5)
        ttk.Label(featured_frame, text="Max Featured Projects:").pack(side='left')
        self.max_featured_var = tk.IntVar(value=self.config.max_featured_projects)
        ttk.Spinbox(featured_frame, from_=3, to=12, 
                   textvariable=self.max_featured_var, width=10).pack(side='left', padx=10)
        
        # Minimum stars for featured
        stars_frame = ttk.Frame(portfolio_frame)
        stars_frame.pack(fill='x', pady=5)
        ttk.Label(stars_frame, text="Min Stars for Featured:").pack(side='left')
        self.min_stars_featured_var = tk.IntVar(value=self.config.min_stars_for_featured)
        ttk.Spinbox(stars_frame, from_=0, to=100, 
                   textvariable=self.min_stars_featured_var, width=10).pack(side='left', padx=10)
        
        # Options
        options_frame = ttk.Frame(portfolio_frame)
        options_frame.pack(fill='x', pady=10)
        
        self.prioritize_recent_var = tk.BooleanVar(value=self.config.prioritize_recent_activity)
        ttk.Checkbutton(options_frame, text="⏰ Prioritize Recent Activity", 
                       variable=self.prioritize_recent_var).pack(anchor='w')
        
        # Export Format Settings
        export_frame = ttk.LabelFrame(scrollable_frame, text="💾 Export Settings", padding=15)
        export_frame.pack(fill='x', padx=10, pady=10)
        
        self.generate_html_var = tk.BooleanVar(value=self.config.generate_portfolio_html)
        self.generate_resume_var = tk.BooleanVar(value=self.config.generate_resume_data)
        self.export_raw_var = tk.BooleanVar(value=self.config.export_raw_data)
        
        ttk.Checkbutton(export_frame, text="🌐 Generate HTML Portfolio", 
                       variable=self.generate_html_var).pack(anchor='w')
        ttk.Checkbutton(export_frame, text="📄 Generate Resume Data", 
                       variable=self.generate_resume_var).pack(anchor='w')
        ttk.Checkbutton(export_frame, text="📊 Export Raw Profile Data", 
                       variable=self.export_raw_var).pack(anchor='w')
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_build_tab(self):
        """Create the profile building tab."""
        build_frame = ttk.Frame(self.notebook)
        self.notebook.add(build_frame, text="🏗️ Build Profile")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(build_frame, text="📋 Instructions", padding=15)
        instructions_frame.pack(fill='x', padx=10, pady=10)
        
        instructions_text = """Welcome to the GitHub Profile Builder! This tool will:

1. 🔍 Discover all your GitHub repositories
2. 📊 Analyze each repository for technologies, languages, and project types
3. 🧠 Generate insights about your development skills and experience
4. 🎨 Create a comprehensive developer profile
5. 💾 Export your profile in multiple formats (JSON, HTML portfolio, resume data)

Make sure you have configured your GitHub username and token in the Configuration tab, then click "Build My Profile" to get started."""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text, 
                                    justify='left', wraplength=800, font=('Arial', 10))
        instructions_label.pack()
        
        # Build Controls
        controls_frame = ttk.Frame(build_frame)
        controls_frame.pack(fill='x', padx=10, pady=20)
        
        self.build_btn = ttk.Button(controls_frame, text="🚀 Build My Profile", 
                                   command=self.start_profile_build, style='Action.TButton')
        self.build_btn.pack(side='left', padx=10)
        
        self.stop_build_btn = ttk.Button(controls_frame, text="⏹️ Stop Building", 
                                        command=self.stop_profile_build, style='Action.TButton',
                                        state='disabled')
        self.stop_build_btn.pack(side='left', padx=10)
        
        # Progress
        progress_frame = ttk.Frame(build_frame)
        progress_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(progress_frame, text="Progress:").pack(anchor='w')
        self.build_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.build_progress.pack(fill='x', pady=5)
        
        self.build_status_var = tk.StringVar(value="Ready to build your GitHub profile")
        ttk.Label(progress_frame, textvariable=self.build_status_var).pack(anchor='w')
        
        # Build Log
        log_frame = ttk.LabelFrame(build_frame, text="📝 Build Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.build_log = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.build_log.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_results_tab(self):
        """Create the profile results tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📊 Profile Results")
        
        # Profile Summary
        summary_frame = ttk.LabelFrame(results_frame, text="👤 Profile Summary", padding=15)
        summary_frame.pack(fill='x', padx=10, pady=10)
        
        self.summary_text = tk.Text(summary_frame, height=8, wrap=tk.WORD, state='disabled',
                                   font=('Consolas', 10))
        self.summary_text.pack(fill='x', pady=5)
        
        # Statistics Overview
        stats_frame = ttk.LabelFrame(results_frame, text="📈 Statistics Overview")
        stats_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create treeview for statistics
        columns = ('metric', 'value', 'details')
        self.stats_tree = ttk.Treeview(stats_frame, columns=columns, show='headings', height=12)
        
        self.stats_tree.heading('metric', text='Metric')
        self.stats_tree.heading('value', text='Value')
        self.stats_tree.heading('details', text='Details')
        
        self.stats_tree.column('metric', width=200, minwidth=150)
        self.stats_tree.column('value', width=100, minwidth=80)
        self.stats_tree.column('details', width=300, minwidth=200)
        
        # Scrollbar for stats
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient='vertical', command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        stats_scrollbar.pack(side='right', fill='y')
        
        # Quick Actions
        actions_frame = ttk.Frame(results_frame)
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(actions_frame, text="🌐 Preview HTML Portfolio", 
                  command=self.preview_html_portfolio).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="📋 Copy Profile Summary", 
                  command=self.copy_profile_summary).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="🔄 Refresh Results", 
                  command=self.refresh_results).pack(side='right', padx=5)
    
    def create_export_tab(self):
        """Create the export options tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="💾 Export")
        
        # Export Status
        status_frame = ttk.LabelFrame(export_frame, text="📊 Export Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.export_status_var = tk.StringVar(value="No profile built yet")
        ttk.Label(status_frame, textvariable=self.export_status_var, 
                 font=('Arial', 11, 'bold')).pack()
        
        # Export Options
        options_frame = ttk.LabelFrame(export_frame, text="💾 Export Formats", padding=15)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        # JSON Export
        json_frame = ttk.Frame(options_frame)
        json_frame.pack(fill='x', pady=5)
        ttk.Button(json_frame, text="📄 Export JSON Profile", 
                  command=self.export_json_profile).pack(side='left', padx=5)
        ttk.Label(json_frame, text="Complete profile data in JSON format").pack(side='left', padx=10)
        
        # HTML Portfolio Export
        html_frame = ttk.Frame(options_frame)
        html_frame.pack(fill='x', pady=5)
        ttk.Button(html_frame, text="🌐 Export HTML Portfolio", 
                  command=self.export_html_portfolio).pack(side='left', padx=5)
        ttk.Label(html_frame, text="Beautiful portfolio website").pack(side='left', padx=10)
        
        # PDF Portfolio Export
        pdf_frame = ttk.Frame(options_frame)
        pdf_frame.pack(fill='x', pady=5)
        ttk.Button(pdf_frame, text="📄 Export PDF Portfolio", 
                  command=self.export_pdf_portfolio).pack(side='left', padx=5)
        ttk.Label(pdf_frame, text="Print-ready portfolio document").pack(side='left', padx=10)
        
        # Resume Data Export
        resume_frame = ttk.Frame(options_frame)
        resume_frame.pack(fill='x', pady=5)
        ttk.Button(resume_frame, text="📋 Export Resume Data", 
                  command=self.export_resume_data).pack(side='left', padx=5)
        ttk.Label(resume_frame, text="Resume-ready structured data").pack(side='left', padx=10)
        
        # Batch Export
        batch_frame = ttk.Frame(options_frame)
        batch_frame.pack(fill='x', pady=15)
        ttk.Button(batch_frame, text="📦 Export All Formats", 
                  command=self.export_all_formats, style='Action.TButton').pack(side='left', padx=5)
        ttk.Label(batch_frame, text="Export JSON, HTML, PDF, and Resume data").pack(side='left', padx=10)
        
        # Portfolio Builder Integration
        integration_frame = ttk.LabelFrame(export_frame, text="🔗 Portfolio Integration", padding=15)
        integration_frame.pack(fill='x', padx=10, pady=10)
        
        integration_text = """Your exported profile data can be used to:

• 🌐 Create a personal portfolio website
• 📄 Auto-generate resume sections  
• 📊 Build interactive developer dashboards
• 🎯 Showcase skills for job applications
• 📈 Track your development progress over time

The HTML portfolio is ready to deploy to GitHub Pages, Netlify, or any web host!"""
        
        ttk.Label(integration_frame, text=integration_text, justify='left', 
                 wraplength=800, font=('Arial', 10)).pack()
        
        # Sample Data Preview
        preview_frame = ttk.LabelFrame(export_frame, text="👁️ Data Preview")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=8, wrap=tk.WORD,
                                                     font=('Consolas', 9))
        self.preview_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_bottom_buttons(self):
        """Create bottom control buttons."""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="❌ Close", command=self.close_dialog).pack(side='right')
        ttk.Button(button_frame, text="💾 Save Settings", command=self.save_settings).pack(side='right', padx=10)
        ttk.Button(button_frame, text="📁 Open Output Folder", command=self.open_output_folder).pack(side='left')
    
    def test_github_connection(self):
        """Test GitHub API connection."""
        username = self.username_var.get().strip()
        token = self.github_token_var.get().strip()
        
        if not username:
            messagebox.showwarning("Missing Username", "Please enter your GitHub username.")
            return
        
        try:
            from github import Github
            
            if token:
                github = Github(token)
                # Test authenticated access
                user = github.get_user(username)
                rate_limit = github.get_rate_limit()
                messagebox.showinfo("Connection Success", 
                    f"✅ Connected to GitHub!\n\n"
                    f"User: {user.login} ({user.name})\n"
                    f"Public Repos: {user.public_repos}\n"
                    f"Rate Limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")
            else:
                # Test public access
                github = Github()
                user = github.get_user(username)
                messagebox.showinfo("Connection Success", 
                    f"✅ Connected to GitHub (Public Access)!\n\n"
                    f"User: {user.login} ({user.name})\n"
                    f"Public Repos: {user.public_repos}\n"
                    f"Note: Use a token for private repos and higher rate limits")
                
        except Exception as e:
            messagebox.showerror("Connection Failed", f"❌ Failed to connect to GitHub:\n{str(e)}")
    
    def start_profile_build(self):
        """Start building the GitHub profile."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Missing Username", "Please enter your GitHub username.")
            return
        
        if self.is_building:
            return
        
        # Update configuration from UI
        self._update_config_from_ui()
        
        self.is_building = True
        self.build_btn.config(state='disabled')
        self.stop_build_btn.config(state='normal')
        self.build_progress['value'] = 0
        
        # Clear build log
        self.build_log.delete('1.0', tk.END)
        
        # Start building in background thread
        self.build_task = threading.Thread(target=self._build_worker, args=(username,))
        self.build_task.daemon = True
        self.build_task.start()
    
    def _build_worker(self, username: str):
        """Worker thread for profile building."""
        try:
            token = self.github_token_var.get().strip() or None
            
            # Create profile builder
            builder = GitHubProfileBuilder(self.config)
            
            # Progress callback
            def progress_callback(message, progress):
                self.dialog.after(0, lambda: self._update_build_progress(message, progress))
            
            # Build profile
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            profile = loop.run_until_complete(
                builder.build_profile(username, token, progress_callback)
            )
            
            loop.close()
            
            # Update UI in main thread
            self.dialog.after(0, lambda: self._build_completed(profile))
            
        except Exception as e:
            self.logger.error(f"Profile building failed: {e}")
            self.dialog.after(0, lambda: self._build_failed(str(e)))
    
    def _update_build_progress(self, message: str, progress: int):
        """Update build progress in UI."""
        self.build_status_var.set(message)
        self.build_progress['value'] = progress
        
        # Log message
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.build_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.build_log.see(tk.END)
    
    def _build_completed(self, profile):
        """Handle profile building completion."""
        self.current_profile = profile
        self.is_building = False
        
        # Update UI
        self.build_btn.config(state='normal')
        self.stop_build_btn.config(state='disabled')
        self.build_progress['value'] = 100
        self.build_status_var.set("✅ Profile building completed!")
        
        # Log completion
        self._update_build_progress(f"🎉 Profile built successfully! Analyzed {profile.total_analyzed_repos} repositories", 100)
        
        # Update results
        self._update_results_display()
        
        # Update export status
        self.export_status_var.set("✅ Profile ready for export")
        
        # Switch to results tab
        self.notebook.select(2)
        
        messagebox.showinfo("Profile Complete", 
            f"🎉 GitHub profile built successfully!\n\n"
            f"Username: {profile.username}\n"
            f"Developer Type: {profile.developer_type}\n"
            f"Experience Level: {profile.experience_level}\n"
            f"Repositories Analyzed: {profile.total_analyzed_repos}\n"
            f"Total Stars: {profile.total_stars_received}\n"
            f"Primary Languages: {', '.join(profile.primary_languages[:3])}")
    
    def _build_failed(self, error_message: str):
        """Handle profile building failure."""
        self.is_building = False
        self.build_btn.config(state='normal')
        self.stop_build_btn.config(state='disabled')
        self.build_status_var.set("❌ Profile building failed")
        
        self._update_build_progress(f"❌ Error: {error_message}", 0)
        
        messagebox.showerror("Build Failed", f"Failed to build GitHub profile:\n{error_message}")
    
    def stop_profile_build(self):
        """Stop the profile building process."""
        if self.build_task and self.build_task.is_alive():
            self.is_building = False
            self.build_status_var.set("⏹️ Stopping profile build...")
    
    def _update_config_from_ui(self):
        """Update configuration from UI values."""
        self.config.include_forks = self.include_forks_var.get()
        self.config.include_archived = self.include_archived_var.get()
        self.config.min_repo_size_kb = self.min_size_var.get()
        self.config.max_repos_to_analyze = self.max_repos_var.get()
        self.config.max_featured_projects = self.max_featured_var.get()
        self.config.min_stars_for_featured = self.min_stars_featured_var.get()
        self.config.prioritize_recent_activity = self.prioritize_recent_var.get()
        self.config.generate_portfolio_html = self.generate_html_var.get()
        self.config.generate_resume_data = self.generate_resume_var.get()
        self.config.export_raw_data = self.export_raw_var.get()
    
    def _update_results_display(self):
        """Update the results display with current profile data."""
        if not self.current_profile:
            return
        
        profile = self.current_profile
        
        # Update summary
        summary_text = f"""GitHub Profile: @{profile.username}
Name: {profile.name or 'Not specified'}
Developer Type: {profile.developer_type}
Experience Level: {profile.experience_level}
Bio: {profile.bio or 'No bio available'}

🏆 Profile Highlights:
• {profile.total_repositories} total repositories ({profile.original_repositories} original, {profile.forked_repositories} forks)
• {profile.total_stars_received} stars received across all repositories  
• {len(profile.languages_used)} programming languages used
• {profile.collaboration_score:.0f}/100 collaboration score
• {profile.innovation_score:.0f}/100 innovation score

💻 Top Languages: {', '.join(profile.primary_languages[:5])}

🚀 Project Types:
• Web Applications: {'Yes' if profile.has_web_projects else 'No'}
• Mobile Apps: {'Yes' if profile.has_mobile_projects else 'No'}
• CLI Tools: {'Yes' if profile.has_cli_tools else 'No'}
• Libraries: {'Yes' if profile.has_libraries else 'No'}
• APIs: {'Yes' if profile.has_apis else 'No'}"""
        
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary_text)
        self.summary_text.config(state='disabled')
        
        # Update statistics tree
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Add statistics
        stats = [
            ("Total Repositories", profile.total_repositories, f"{profile.public_repositories} public, {profile.private_repositories} private"),
            ("Original Projects", profile.original_repositories, f"{profile.forked_repositories} forks excluded"),
            ("Total Stars Received", profile.total_stars_received, "Across all repositories"),
            ("Total Forks Received", profile.total_forks_received, "Community engagement"),
            ("Languages Used", len(profile.languages_used), f"Primary: {', '.join(profile.primary_languages[:3])}"),
            ("Developer Type", profile.developer_type, f"{profile.experience_level} experience"),
            ("Collaboration Score", f"{profile.collaboration_score:.0f}/100", "Based on forks, public repos, READMEs"),
            ("Innovation Score", f"{profile.innovation_score:.0f}/100", "Based on stars, originality, diversity"),
            ("Repositories with README", profile.repositories_with_readme, f"{(profile.repositories_with_readme/max(profile.total_repositories,1)*100):.0f}% coverage"),
            ("Featured Projects", len(profile.featured_projects), f"Min {self.config.min_stars_for_featured} stars"),
        ]
        
        for metric, value, details in stats:
            self.stats_tree.insert('', 'end', values=(metric, value, details))
        
        # Update preview
        self._update_export_preview()
    
    def _update_export_preview(self):
        """Update the export preview."""
        if not self.current_profile:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', "No profile data available")
            return
        
        # Show JSON preview
        try:
            from profile_builder import ProfileExporter
            exporter = ProfileExporter(self.current_profile)
            profile_dict = exporter._profile_to_dict()
            
            # Show condensed preview
            preview_data = {
                "username": profile_dict["username"],
                "name": profile_dict["name"],
                "developer_type": profile_dict["developer_type"],
                "total_repositories": profile_dict["total_repositories"],
                "total_stars_received": profile_dict["total_stars_received"],
                "primary_languages": profile_dict["primary_languages"],
                "featured_projects": len(profile_dict["featured_projects"]),
                "collaboration_score": profile_dict["collaboration_score"],
                "analysis_date": profile_dict["analysis_date"]
            }
            
            preview_json = json.dumps(preview_data, indent=2)
            
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Sample Profile Data (condensed):\n\n{preview_json}")
            
        except Exception as e:
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', f"Error generating preview: {e}")
    
    def export_json_profile(self):
        """Export profile to JSON format."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save GitHub Profile JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{self.current_profile.username}_github_profile.json"
        )
        
        if file_path:
            try:
                from profile_builder import ProfileExporter
                exporter = ProfileExporter(self.current_profile)
                exporter.export_to_json(file_path)
                
                messagebox.showinfo("Export Success", f"Profile exported to:\n{file_path}")
                self._update_build_progress(f"✅ JSON profile exported to {file_path}", 100)
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export JSON profile:\n{str(e)}")
    
    def export_html_portfolio(self):
        """Export HTML portfolio."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save HTML Portfolio",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=f"{self.current_profile.username}_portfolio.html"
        )
        
        if file_path:
            try:
                from profile_builder import ProfileExporter
                exporter = ProfileExporter(self.current_profile)
                exporter.export_to_html_portfolio(file_path)
                
                messagebox.showinfo("Export Success", f"HTML portfolio exported to:\n{file_path}")
                self._update_build_progress(f"✅ HTML portfolio exported to {file_path}", 100)
                
                # Ask if user wants to open it
                if messagebox.askyesno("Open Portfolio", "Would you like to open the portfolio in your browser?"):
                    webbrowser.open(f"file://{os.path.abspath(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export HTML portfolio:\n{str(e)}")
    
    def export_pdf_portfolio(self):
        """Export PDF portfolio."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save PDF Portfolio",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"{self.current_profile.username}_portfolio.pdf"
        )
        
        if file_path:
            try:
                # Show progress dialog
                progress_dialog = tk.Toplevel(self.dialog)
                progress_dialog.title("Generating PDF")
                progress_dialog.geometry("400x150")
                progress_dialog.transient(self.dialog)
                progress_dialog.grab_set()
                
                # Center the progress dialog
                progress_dialog.geometry("+%d+%d" % (
                    self.dialog.winfo_rootx() + 250,
                    self.dialog.winfo_rooty() + 200
                ))
                
                progress_label = ttk.Label(progress_dialog, text="Generating PDF portfolio...")
                progress_label.pack(pady=20)
                
                progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
                progress_bar.pack(fill='x', padx=20, pady=10)
                progress_bar.start()
                
                status_label = ttk.Label(progress_dialog, text="This may take a few moments...")
                status_label.pack(pady=10)
                
                progress_dialog.update()
                
                def generate_pdf():
                    try:
                        from profile_builder import ProfileExporter
                        exporter = ProfileExporter(self.current_profile)
                        exporter.export_to_pdf_portfolio(file_path)
                        return True
                    except Exception as e:
                        return str(e)
                
                # Run PDF generation in a thread
                import threading
                
                result = [None]  # Use list to allow modification in thread
                
                def pdf_worker():
                    result[0] = generate_pdf()
                
                thread = threading.Thread(target=pdf_worker)
                thread.daemon = True
                thread.start()
                
                # Wait for completion with timeout
                timeout = 60  # 60 seconds
                elapsed = 0
                while thread.is_alive() and elapsed < timeout:
                    progress_dialog.update()
                    time.sleep(0.1)
                    elapsed += 0.1
                
                progress_dialog.destroy()
                
                if thread.is_alive():
                    messagebox.showwarning("Timeout", "PDF generation is taking longer than expected. Please try again or check if you have a PDF generation tool installed.")
                elif result[0] is True:
                    messagebox.showinfo("Export Success", f"PDF portfolio exported to:\n{file_path}")
                    self._update_build_progress(f"✅ PDF portfolio exported to {file_path}", 100)
                    
                    # Ask if user wants to open it
                    if messagebox.askyesno("Open PDF", "Would you like to open the PDF portfolio?"):
                        import subprocess
                        import platform
                        
                        try:
                            if platform.system() == "Windows":
                                os.startfile(file_path)
                            elif platform.system() == "Darwin":  # macOS
                                subprocess.call(["open", file_path])
                            else:  # Linux
                                subprocess.call(["xdg-open", file_path])
                        except Exception as e:
                            messagebox.showinfo("PDF Created", f"PDF portfolio saved to:\n{file_path}\n\nPlease open it manually.")
                else:
                    error_msg = result[0] if isinstance(result[0], str) else "Unknown error occurred"
                    
                    # Check if it's a dependency issue
                    if "No PDF generation method available" in error_msg:
                        messagebox.showerror("PDF Export Error", 
                            "PDF generation requires additional software. Please install one of the following:\n\n"
                            "• WeasyPrint: pip install weasyprint\n"
                            "• Playwright: pip install playwright && playwright install chromium\n"
                            "• wkhtmltopdf: Download from https://wkhtmltopdf.org/\n"
                            "• Google Chrome or Chromium browser\n\n"
                            "Then try exporting again.")
                    else:
                        messagebox.showerror("PDF Export Error", f"Failed to export PDF portfolio:\n{error_msg}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export PDF portfolio:\n{str(e)}")
    
    def export_resume_data(self):
        """Export resume data."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Resume Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{self.current_profile.username}_resume_data.json"
        )
        
        if file_path:
            try:
                from profile_builder import ProfileExporter
                exporter = ProfileExporter(self.current_profile)
                exporter.export_resume_data(file_path)
                
                messagebox.showinfo("Export Success", f"Resume data exported to:\n{file_path}")
                self._update_build_progress(f"✅ Resume data exported to {file_path}", 100)
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export resume data:\n{str(e)}")
    
    def export_all_formats(self):
        """Export all formats to a folder."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        folder_path = filedialog.askdirectory(title="Select Export Folder")
        if not folder_path:
            return
        
        # Show progress dialog
        progress_dialog = tk.Toplevel(self.dialog)
        progress_dialog.title("Exporting All Formats")
        progress_dialog.geometry("450x200")
        progress_dialog.transient(self.dialog)
        progress_dialog.grab_set()
        
        # Center the progress dialog
        progress_dialog.geometry("+%d+%d" % (
            self.dialog.winfo_rootx() + 200,
            self.dialog.winfo_rooty() + 150
        ))
        
        progress_label = ttk.Label(progress_dialog, text="Exporting all formats...")
        progress_label.pack(pady=15)
        
        progress_bar = ttk.Progressbar(progress_dialog, mode='determinate', maximum=100)
        progress_bar.pack(fill='x', padx=20, pady=10)
        
        status_label = ttk.Label(progress_dialog, text="Starting export...")
        status_label.pack(pady=5)
        
        progress_dialog.update()
        
        try:
            from profile_builder import ProfileExporter
            exporter = ProfileExporter(self.current_profile)
            
            username = self.current_profile.username
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Define all files
            json_file = os.path.join(folder_path, f"{username}_profile_{timestamp}.json")
            html_file = os.path.join(folder_path, f"{username}_portfolio_{timestamp}.html")
            pdf_file = os.path.join(folder_path, f"{username}_portfolio_{timestamp}.pdf")
            resume_file = os.path.join(folder_path, f"{username}_resume_{timestamp}.json")
            
            files_created = []
            total_steps = 4
            
            # Step 1: Export JSON
            status_label.config(text="Exporting JSON profile...")
            progress_dialog.update()
            exporter.export_to_json(json_file)
            files_created.append(os.path.basename(json_file))
            progress_bar['value'] = 25
            progress_dialog.update()
            
            # Step 2: Export HTML
            status_label.config(text="Generating HTML portfolio...")
            progress_dialog.update()
            exporter.export_to_html_portfolio(html_file)
            files_created.append(os.path.basename(html_file))
            progress_bar['value'] = 50
            progress_dialog.update()
            
            # Step 3: Export PDF (with error handling)
            pdf_success = False
            try:
                status_label.config(text="Generating PDF portfolio...")
                progress_dialog.update()
                exporter.export_to_pdf_portfolio(pdf_file)
                files_created.append(os.path.basename(pdf_file))
                pdf_success = True
            except Exception as e:
                self.logger.warning(f"PDF export failed: {e}")
                # PDF generation failed, but continue with other exports
            
            progress_bar['value'] = 75
            progress_dialog.update()
            
            # Step 4: Export Resume Data
            status_label.config(text="Exporting resume data...")
            progress_dialog.update()
            exporter.export_resume_data(resume_file)
            files_created.append(os.path.basename(resume_file))
            progress_bar['value'] = 100
            progress_dialog.update()
            
            progress_dialog.destroy()
            
            # Show completion message
            success_msg = f"Formats exported to:\n{folder_path}\n\nFiles created:\n"
            success_msg += "\n".join(f"• {file}" for file in files_created)
            
            if not pdf_success:
                success_msg += "\n\n⚠️ Note: PDF export failed. Install a PDF generator for PDF support:\n"
                success_msg += "• WeasyPrint: pip install weasyprint\n"
                success_msg += "• Playwright: pip install playwright && playwright install chromium\n"
                success_msg += "• wkhtmltopdf or Chrome browser"
            
            messagebox.showinfo("Export Complete", success_msg)
            self._update_build_progress(f"✅ All formats exported to {folder_path}", 100)
            
        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.destroy()
            messagebox.showerror("Export Error", f"Failed to export all formats:\n{str(e)}")
    
    def preview_html_portfolio(self):
        """Preview the HTML portfolio in browser."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        try:
            # Create temporary HTML file
            import tempfile
            from profile_builder import ProfileExporter
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
            exporter = ProfileExporter(self.current_profile)
            html_content = exporter._generate_portfolio_html()
            temp_file.write(html_content)
            temp_file.close()
            
            # Open in browser
            webbrowser.open(f"file://{temp_file.name}")
            
            self._update_build_progress(f"✅ Portfolio preview opened in browser", 100)
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview portfolio:\n{str(e)}")
    
    def copy_profile_summary(self):
        """Copy profile summary to clipboard."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please build a profile first.")
            return
        
        try:
            summary = self.summary_text.get('1.0', tk.END).strip()
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(summary)
            self.dialog.update()
            
            messagebox.showinfo("Copied", "Profile summary copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy summary:\n{str(e)}")
    
    def refresh_results(self):
        """Refresh the results display."""
        if self.current_profile:
            self._update_results_display()
            messagebox.showinfo("Refreshed", "Results display refreshed!")
    
    def open_output_folder(self):
        """Open the output folder in file manager."""
        output_dir = Path.home() / "github_profiles"
        output_dir.mkdir(exist_ok=True)
        
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
    
    def save_settings(self):
        """Save current settings."""
        try:
            settings_dir = Path.home() / '.reporeadme'
            settings_dir.mkdir(exist_ok=True)
            
            settings = {
                'username': self.username_var.get(),
                'github_token': self.github_token_var.get(),
                'include_forks': self.include_forks_var.get(),
                'include_archived': self.include_archived_var.get(),
                'min_repo_size_kb': self.min_size_var.get(),
                'max_repos_to_analyze': self.max_repos_var.get(),
                'max_featured_projects': self.max_featured_var.get(),
                'min_stars_for_featured': self.min_stars_featured_var.get(),
                'prioritize_recent': self.prioritize_recent_var.get(),
                'generate_html': self.generate_html_var.get(),
                'generate_resume': self.generate_resume_var.get(),
                'export_raw': self.export_raw_var.get()
            }
            
            settings_file = settings_dir / 'profile_builder_settings.json'
            with settings_file.open('w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{str(e)}")
    
    def load_settings(self):
        """Load saved settings."""
        try:
            settings_file = Path.home() / '.reporeadme' / 'profile_builder_settings.json'
            if settings_file.exists():
                with settings_file.open('r') as f:
                    settings = json.load(f)
                
                self.username_var.set(settings.get('username', ''))
                self.github_token_var.set(settings.get('github_token', ''))
                self.include_forks_var.set(settings.get('include_forks', False))
                self.include_archived_var.set(settings.get('include_archived', False))
                self.min_size_var.set(settings.get('min_repo_size_kb', 1))
                self.max_repos_var.set(settings.get('max_repos_to_analyze', 500))
                self.max_featured_var.set(settings.get('max_featured_projects', 6))
                self.min_stars_featured_var.set(settings.get('min_stars_for_featured', 1))
                self.prioritize_recent_var.set(settings.get('prioritize_recent', True))
                self.generate_html_var.set(settings.get('generate_html', True))
                self.generate_resume_var.set(settings.get('generate_resume', True))
                self.export_raw_var.set(settings.get('export_raw', True))
                
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
    
    def close_dialog(self):
        """Close the dialog."""
        if self.is_building:
            if messagebox.askyesno("Confirm Close", "Profile building is in progress. Do you want to stop and close?"):
                self.is_building = False
                self.dialog.destroy()
        else:
            self.dialog.destroy()


def create_profile_builder(parent):
    """Create and show the profile builder dialog."""
    return ProfileBuilderDialog(parent)