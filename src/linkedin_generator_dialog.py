#!/usr/bin/env python3
"""
LinkedIn Generator Dialog

GUI interface for generating optimized LinkedIn profile content from GitHub profile data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from .linkedin_generator import LinkedInGenerator, LinkedInConfig, LinkedInExporter
    from .profile_builder import GitHubProfile, GitHubProfileBuilder, ProfileBuilderConfig
    from .config.github_auth import GitHubAuthManager
    from .utils.logger import get_logger
except ImportError:
    from linkedin_generator import LinkedInGenerator, LinkedInConfig, LinkedInExporter
    from profile_builder import GitHubProfile, GitHubProfileBuilder, ProfileBuilderConfig
    from config.github_auth import GitHubAuthManager
    from utils.logger import get_logger


class LinkedInGeneratorDialog:
    """Dialog for generating LinkedIn profile content from GitHub profiles."""
    
    def __init__(self, parent):
        """Initialize the LinkedIn generator dialog."""
        self.parent = parent
        self.logger = get_logger()
        self.auth_manager = GitHubAuthManager()
        
        # Create main dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("💼 LinkedIn Profile Generator")
        self.dialog.geometry("1100x900")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 30,
            parent.winfo_rooty() + 30
        ))
        
        # State variables
        self.current_profile = None
        self.current_linkedin_data = None
        self.is_generating = False
        
        # Configuration
        self.linkedin_config = LinkedInConfig()
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Profile Source
        self.create_source_tab()
        
        # Tab 2: Content Configuration
        self.create_config_tab()
        
        # Tab 3: Target & Positioning
        self.create_targeting_tab()
        
        # Tab 4: Generate Content
        self.create_generate_tab()
        
        # Tab 5: Content Results
        self.create_results_tab()
        
        # Tab 6: Export & Tips
        self.create_export_tab()
        
        # Bottom buttons
        self.create_bottom_buttons()
    
    def create_source_tab(self):
        """Create the profile source tab."""
        source_frame = ttk.Frame(self.notebook)
        self.notebook.add(source_frame, text="👤 Profile Source")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(source_frame, text="📋 About LinkedIn Profile Generator", padding=15)
        instructions_frame.pack(fill='x', padx=10, pady=10)
        
        instructions_text = """Welcome to the LinkedIn Profile Generator! This tool creates optimized LinkedIn content from your GitHub profile.

🎯 What this tool generates:
• Compelling headlines optimized for keywords and recruiters
• Professional summaries that highlight your technical achievements
• Skill recommendations based on your GitHub activity
• Project descriptions optimized for LinkedIn
• Content ideas for posts and articles
• Networking suggestions and connection targets
• Profile optimization tips to improve visibility

💡 How it works:
1. Analyzes your GitHub repositories and activity
2. Extracts technical skills, project types, and achievements
3. Generates professional content optimized for LinkedIn's algorithm
4. Provides multiple variations and customization options
5. Offers strategic advice for networking and content creation"""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text, 
                                    justify='left', wraplength=1000, font=('Arial', 10))
        instructions_label.pack()
        
        # Profile Source Options
        source_options_frame = ttk.LabelFrame(source_frame, text="📊 GitHub Profile Source", padding=15)
        source_options_frame.pack(fill='x', padx=10, pady=10)
        
        self.source_var = tk.StringVar(value="github_build")
        
        # Option 1: Build from GitHub
        github_frame = ttk.Frame(source_options_frame)
        github_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(github_frame, text="🔍 Analyze GitHub Profile", 
                       variable=self.source_var, value="github_build").pack(anchor='w')
        
        github_details_frame = ttk.Frame(github_frame)
        github_details_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(github_details_frame, text="GitHub Username:").pack(side='left')
        self.github_username_var = tk.StringVar()
        username_entry = ttk.Entry(github_details_frame, textvariable=self.github_username_var, width=25)
        username_entry.pack(side='left', padx=10)
        
        ttk.Label(github_details_frame, text="GitHub Token (optional):").pack(side='left', padx=(20, 0))
        self.github_token_var = tk.StringVar()
        token_entry = ttk.Entry(github_details_frame, textvariable=self.github_token_var, 
                               width=30, show='*')
        token_entry.pack(side='left', padx=10)
        
        # Option 2: Use existing profile
        existing_frame = ttk.Frame(source_options_frame)
        existing_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(existing_frame, text="📁 Use Existing Profile Data", 
                       variable=self.source_var, value="existing").pack(anchor='w')
        
        existing_details_frame = ttk.Frame(existing_frame)
        existing_details_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(existing_details_frame, text="📂 Browse Profile JSON", 
                  command=self.browse_profile_file).pack(side='left')
        self.profile_file_var = tk.StringVar()
        ttk.Label(existing_details_frame, textvariable=self.profile_file_var, 
                 foreground='blue').pack(side='left', padx=10)
        
        # Current profile status
        status_frame = ttk.LabelFrame(source_frame, text="📊 Current Profile Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.profile_status_var = tk.StringVar(value="No profile loaded")
        ttk.Label(status_frame, textvariable=self.profile_status_var, 
                 font=('Arial', 11, 'bold')).pack()
        
        # Load Profile Button
        action_frame = ttk.Frame(source_frame)
        action_frame.pack(fill='x', padx=10, pady=20)
        
        self.load_profile_btn = ttk.Button(action_frame, text="🔄 Load/Build Profile", 
                                          command=self.load_profile, style='Action.TButton')
        self.load_profile_btn.pack(side='left', padx=10)
        
        self.profile_info_btn = ttk.Button(action_frame, text="ℹ️ View Profile Info", 
                                          command=self.show_profile_info, state='disabled')
        self.profile_info_btn.pack(side='left', padx=10)
    
    def create_config_tab(self):
        """Create the content configuration tab."""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Content Style")
        
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
        
        # Content Style
        style_frame = ttk.LabelFrame(scrollable_frame, text="✍️ Writing Style", padding=15)
        style_frame.pack(fill='x', padx=10, pady=10)
        
        style_row1 = ttk.Frame(style_frame)
        style_row1.pack(fill='x', pady=5)
        
        ttk.Label(style_row1, text="Tone:").pack(side='left')
        self.tone_var = tk.StringVar(value=self.linkedin_config.tone)
        tone_combo = ttk.Combobox(style_row1, textvariable=self.tone_var,
                                 values=['professional', 'approachable', 'authoritative', 'creative'],
                                 state='readonly', width=15)
        tone_combo.pack(side='left', padx=10)
        
        ttk.Label(style_row1, text="Length:").pack(side='left', padx=(20, 0))
        self.length_var = tk.StringVar(value=self.linkedin_config.length)
        length_combo = ttk.Combobox(style_row1, textvariable=self.length_var,
                                   values=['short', 'medium', 'long'], state='readonly', width=10)
        length_combo.pack(side='left', padx=10)
        
        style_options_frame = ttk.Frame(style_frame)
        style_options_frame.pack(fill='x', pady=10)
        
        self.include_emojis_var = tk.BooleanVar(value=self.linkedin_config.include_emojis)
        self.first_person_var = tk.BooleanVar(value=self.linkedin_config.use_first_person)
        
        ttk.Checkbutton(style_options_frame, text="😊 Include Emojis", 
                       variable=self.include_emojis_var).pack(anchor='w')
        ttk.Checkbutton(style_options_frame, text="👤 Use First Person (I/my vs They/their)", 
                       variable=self.first_person_var).pack(anchor='w')
        
        # Content Focus
        focus_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Content Focus", padding=15)
        focus_frame.pack(fill='x', padx=10, pady=10)
        
        focus_grid = ttk.Frame(focus_frame)
        focus_grid.pack(fill='x')
        
        self.focus_results_var = tk.BooleanVar(value=self.linkedin_config.focus_on_results)
        self.highlight_leadership_var = tk.BooleanVar(value=self.linkedin_config.highlight_leadership)
        self.emphasize_innovation_var = tk.BooleanVar(value=self.linkedin_config.emphasize_innovation)
        self.personal_touches_var = tk.BooleanVar(value=self.linkedin_config.include_personal_touches)
        
        ttk.Checkbutton(focus_grid, text="📊 Focus on Results & Metrics", 
                       variable=self.focus_results_var).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(focus_grid, text="👑 Highlight Leadership Experience", 
                       variable=self.highlight_leadership_var).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(focus_grid, text="💡 Emphasize Innovation & Creativity", 
                       variable=self.emphasize_innovation_var).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(focus_grid, text="🎨 Include Personal Touches", 
                       variable=self.personal_touches_var).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # LinkedIn Optimization
        optimization_frame = ttk.LabelFrame(scrollable_frame, text="🔍 LinkedIn Optimization", padding=15)
        optimization_frame.pack(fill='x', padx=10, pady=10)
        
        opt_options = ttk.Frame(optimization_frame)
        opt_options.pack(fill='x', pady=5)
        
        self.optimize_keywords_var = tk.BooleanVar(value=self.linkedin_config.optimize_for_keywords)
        self.include_cta_var = tk.BooleanVar(value=self.linkedin_config.include_call_to_action)
        self.open_opportunities_var = tk.BooleanVar(value=self.linkedin_config.mention_open_to_opportunities)
        
        ttk.Checkbutton(opt_options, text="🔑 Optimize for Keywords & Search", 
                       variable=self.optimize_keywords_var).pack(anchor='w')
        ttk.Checkbutton(opt_options, text="📢 Include Call-to-Action", 
                       variable=self.include_cta_var).pack(anchor='w')
        ttk.Checkbutton(opt_options, text="🚀 Mention Open to Opportunities", 
                       variable=self.open_opportunities_var).pack(anchor='w')
        
        # Personal Branding
        branding_frame = ttk.LabelFrame(scrollable_frame, text="🎨 Personal Branding", padding=15)
        branding_frame.pack(fill='x', padx=10, pady=10)
        
        # Brand keywords
        keywords_frame = ttk.Frame(branding_frame)
        keywords_frame.pack(fill='x', pady=5)
        
        ttk.Label(keywords_frame, text="Brand Keywords (comma-separated):").pack(anchor='w')
        self.brand_keywords_var = tk.StringVar()
        brand_keywords_entry = ttk.Entry(keywords_frame, textvariable=self.brand_keywords_var, width=60)
        brand_keywords_entry.pack(fill='x', pady=2)
        
        # Company preferences
        companies_frame = ttk.Frame(branding_frame)
        companies_frame.pack(fill='x', pady=5)
        
        ttk.Label(companies_frame, text="Preferred Companies (comma-separated):").pack(anchor='w')
        self.company_preferences_var = tk.StringVar()
        companies_entry = ttk.Entry(companies_frame, textvariable=self.company_preferences_var, width=60)
        companies_entry.pack(fill='x', pady=2)
        
        # Location preferences
        locations_frame = ttk.Frame(branding_frame)
        locations_frame.pack(fill='x', pady=5)
        
        ttk.Label(locations_frame, text="Location Preferences (comma-separated):").pack(anchor='w')
        self.location_preferences_var = tk.StringVar()
        locations_entry = ttk.Entry(locations_frame, textvariable=self.location_preferences_var, width=60)
        locations_entry.pack(fill='x', pady=2)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_targeting_tab(self):
        """Create the targeting and positioning tab."""
        targeting_frame = ttk.Frame(self.notebook)
        self.notebook.add(targeting_frame, text="🎯 Targeting")
        
        # Target Role
        role_frame = ttk.LabelFrame(targeting_frame, text="💼 Target Role", padding=15)
        role_frame.pack(fill='x', padx=10, pady=10)
        
        role_details_frame = ttk.Frame(role_frame)
        role_details_frame.pack(fill='x', pady=5)
        
        ttk.Label(role_details_frame, text="Target Role:").pack(side='left')
        self.target_role_var = tk.StringVar(value=self.linkedin_config.target_role or "")
        role_entry = ttk.Entry(role_details_frame, textvariable=self.target_role_var, width=30)
        role_entry.pack(side='left', padx=10)
        
        ttk.Label(role_details_frame, text="Career Level:").pack(side='left', padx=(20, 0))
        self.career_level_var = tk.StringVar(value=self.linkedin_config.career_level or "")
        level_combo = ttk.Combobox(role_details_frame, textvariable=self.career_level_var,
                                  values=['entry', 'mid', 'senior', 'executive'], 
                                  state='readonly', width=15)
        level_combo.pack(side='left', padx=10)
        
        # Common role examples
        examples_frame = ttk.Frame(role_frame)
        examples_frame.pack(fill='x', pady=10)
        
        ttk.Label(examples_frame, text="💡 Role Examples:", font=('Arial', 10, 'bold')).pack(anchor='w')
        examples_text = ("Software Developer, Senior Frontend Developer, Full Stack Engineer, DevOps Engineer, "
                        "Data Scientist, Product Manager, Engineering Manager, Solutions Architect, "
                        "Technical Lead, CTO")
        ttk.Label(examples_frame, text=examples_text, wraplength=900, 
                 font=('Arial', 9)).pack(anchor='w', pady=2)
        
        # Target Industry
        industry_frame = ttk.LabelFrame(targeting_frame, text="🏢 Target Industry", padding=15)
        industry_frame.pack(fill='x', padx=10, pady=10)
        
        industry_details_frame = ttk.Frame(industry_frame)
        industry_details_frame.pack(fill='x', pady=5)
        
        ttk.Label(industry_details_frame, text="Target Industry:").pack(side='left')
        self.target_industry_var = tk.StringVar(value=self.linkedin_config.target_industry or "")
        industry_entry = ttk.Entry(industry_details_frame, textvariable=self.target_industry_var, width=30)
        industry_entry.pack(side='left', padx=10)
        
        # Industry examples
        industry_examples_frame = ttk.Frame(industry_frame)
        industry_examples_frame.pack(fill='x', pady=10)
        
        ttk.Label(industry_examples_frame, text="💡 Industry Examples:", font=('Arial', 10, 'bold')).pack(anchor='w')
        industry_examples_text = ("FinTech, HealthTech, EdTech, E-commerce, SaaS, Gaming, IoT, AI/ML, "
                                 "Cybersecurity, Cloud Computing, Enterprise Software, Consumer Apps, "
                                 "Developer Tools")
        ttk.Label(industry_examples_frame, text=industry_examples_text, wraplength=900, 
                 font=('Arial', 9)).pack(anchor='w', pady=2)
        
        # Content Strategy
        strategy_frame = ttk.LabelFrame(targeting_frame, text="📝 Content Strategy", padding=15)
        strategy_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        strategy_instructions = ttk.Label(strategy_frame, 
            text="Describe your professional goals and what you want to emphasize in your LinkedIn profile:")
        strategy_instructions.pack(anchor='w', pady=(0, 5))
        
        self.content_strategy_text = scrolledtext.ScrolledText(strategy_frame, height=6, wrap=tk.WORD,
                                                              font=('Arial', 10))
        self.content_strategy_text.pack(fill='both', expand=True, pady=5)
        
        # Sample strategy
        sample_strategy = """Example strategy points you might include:

• Seeking senior technical roles at innovative startups
• Focus on building scalable web applications and leading engineering teams  
• Interested in mentoring junior developers and contributing to open-source
• Passionate about fintech and using technology to democratize financial services
• Looking to connect with other engineering leaders and startup founders
• Want to share insights about technical architecture and team management"""
        
        self.content_strategy_text.insert('1.0', sample_strategy)
        
        # Quick Templates
        templates_frame = ttk.Frame(targeting_frame)
        templates_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(templates_frame, text="🚀 Quick Templates:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        template_buttons_frame = ttk.Frame(templates_frame)
        template_buttons_frame.pack(fill='x', pady=5)
        
        ttk.Button(template_buttons_frame, text="👨‍💻 Senior Developer", 
                  command=lambda: self.apply_template("senior_dev")).pack(side='left', padx=5)
        ttk.Button(template_buttons_frame, text="🚀 Startup Focused", 
                  command=lambda: self.apply_template("startup")).pack(side='left', padx=5)
        ttk.Button(template_buttons_frame, text="🏢 Enterprise", 
                  command=lambda: self.apply_template("enterprise")).pack(side='left', padx=5)
        ttk.Button(template_buttons_frame, text="🔬 Research/Academic", 
                  command=lambda: self.apply_template("academic")).pack(side='left', padx=5)
    
    def create_generate_tab(self):
        """Create the content generation tab."""
        generate_frame = ttk.Frame(self.notebook)
        self.notebook.add(generate_frame, text="🔨 Generate")
        
        # Generation Status
        status_frame = ttk.LabelFrame(generate_frame, text="📊 Generation Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.generation_status_var = tk.StringVar(value="Ready to generate LinkedIn content")
        ttk.Label(status_frame, textvariable=self.generation_status_var, 
                 font=('Arial', 11, 'bold')).pack()
        
        # Generate Controls
        controls_frame = ttk.Frame(generate_frame)
        controls_frame.pack(fill='x', padx=10, pady=20)
        
        self.generate_btn = ttk.Button(controls_frame, text="🔨 Generate LinkedIn Content", 
                                      command=self.generate_linkedin_content, style='Action.TButton')
        self.generate_btn.pack(side='left', padx=10)
        
        self.regenerate_btn = ttk.Button(controls_frame, text="🔄 Regenerate with New Settings", 
                                        command=self.regenerate_content, state='disabled')
        self.regenerate_btn.pack(side='left', padx=10)
        
        # Generation Progress
        progress_frame = ttk.Frame(generate_frame)
        progress_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(progress_frame, text="Progress:").pack(anchor='w')
        self.generation_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.generation_progress.pack(fill='x', pady=5)
        
        # Generation Log
        log_frame = ttk.LabelFrame(generate_frame, text="📝 Generation Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.generation_log = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD)
        self.generation_log.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_results_tab(self):
        """Create the results tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📊 Results")
        
        # Results notebook for different content types
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Headline & Summary Tab
        self.create_headline_summary_tab()
        
        # Skills & Experience Tab
        self.create_skills_experience_tab()
        
        # Content Ideas Tab
        self.create_content_ideas_tab()
        
        # Networking Tab
        self.create_networking_tab()
        
        # Optimization Tab
        self.create_optimization_tab()
    
    def create_headline_summary_tab(self):
        """Create headline and summary results tab."""
        headline_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(headline_frame, text="📝 Headline & Summary")
        
        # Headline Section
        headline_section = ttk.LabelFrame(headline_frame, text="📢 LinkedIn Headline", padding=10)
        headline_section.pack(fill='x', padx=5, pady=5)
        
        self.headline_text = scrolledtext.ScrolledText(headline_section, height=3, wrap=tk.WORD,
                                                      font=('Arial', 11, 'bold'), background='#f0f8ff')
        self.headline_text.pack(fill='x', pady=5)
        
        headline_actions = ttk.Frame(headline_section)
        headline_actions.pack(fill='x', pady=5)
        ttk.Button(headline_actions, text="📋 Copy Headline", 
                  command=lambda: self.copy_text(self.headline_text)).pack(side='left', padx=5)
        
        # Summary Section
        summary_section = ttk.LabelFrame(headline_frame, text="📄 Professional Summary", padding=10)
        summary_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Summary length tabs
        summary_tabs = ttk.Notebook(summary_section)
        summary_tabs.pack(fill='both', expand=True, pady=5)
        
        # Short summary
        short_frame = ttk.Frame(summary_tabs)
        summary_tabs.add(short_frame, text="Short (2 sentences)")
        self.summary_short_text = scrolledtext.ScrolledText(short_frame, height=4, wrap=tk.WORD,
                                                           font=('Arial', 10))
        self.summary_short_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        short_actions = ttk.Frame(short_frame)
        short_actions.pack(fill='x', padx=5, pady=5)
        ttk.Button(short_actions, text="📋 Copy Short Summary", 
                  command=lambda: self.copy_text(self.summary_short_text)).pack(side='left')
        
        # Medium summary
        medium_frame = ttk.Frame(summary_tabs)
        summary_tabs.add(medium_frame, text="Medium (3-4 paragraphs)")
        self.summary_medium_text = scrolledtext.ScrolledText(medium_frame, height=12, wrap=tk.WORD,
                                                            font=('Arial', 10))
        self.summary_medium_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        medium_actions = ttk.Frame(medium_frame)
        medium_actions.pack(fill='x', padx=5, pady=5)
        ttk.Button(medium_actions, text="📋 Copy Medium Summary", 
                  command=lambda: self.copy_text(self.summary_medium_text)).pack(side='left')
        
        # Long summary
        long_frame = ttk.Frame(summary_tabs)
        summary_tabs.add(long_frame, text="Long (5+ paragraphs)")
        self.summary_long_text = scrolledtext.ScrolledText(long_frame, height=15, wrap=tk.WORD,
                                                          font=('Arial', 10))
        self.summary_long_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        long_actions = ttk.Frame(long_frame)
        long_actions.pack(fill='x', padx=5, pady=5)
        ttk.Button(long_actions, text="📋 Copy Long Summary", 
                  command=lambda: self.copy_text(self.summary_long_text)).pack(side='left')
    
    def create_skills_experience_tab(self):
        """Create skills and experience tab."""
        skills_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(skills_frame, text="🔧 Skills & Projects")
        
        # Top Skills Section
        skills_section = ttk.LabelFrame(skills_frame, text="🎯 Top Skills for LinkedIn", padding=10)
        skills_section.pack(fill='x', padx=5, pady=5)
        
        self.skills_text = scrolledtext.ScrolledText(skills_section, height=8, wrap=tk.WORD,
                                                    font=('Arial', 10))
        self.skills_text.pack(fill='both', expand=True, pady=5)
        
        skills_actions = ttk.Frame(skills_section)
        skills_actions.pack(fill='x', pady=5)
        ttk.Button(skills_actions, text="📋 Copy Skills List", 
                  command=lambda: self.copy_text(self.skills_text)).pack(side='left', padx=5)
        
        # Project Descriptions Section
        projects_section = ttk.LabelFrame(skills_frame, text="🚀 Project Descriptions", padding=10)
        projects_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.projects_text = scrolledtext.ScrolledText(projects_section, height=12, wrap=tk.WORD,
                                                      font=('Arial', 10))
        self.projects_text.pack(fill='both', expand=True, pady=5)
        
        projects_actions = ttk.Frame(projects_section)
        projects_actions.pack(fill='x', pady=5)
        ttk.Button(projects_actions, text="📋 Copy Project Descriptions", 
                  command=lambda: self.copy_text(self.projects_text)).pack(side='left', padx=5)
    
    def create_content_ideas_tab(self):
        """Create content ideas tab."""
        content_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(content_frame, text="💡 Content Ideas")
        
        # Post Ideas Section
        posts_section = ttk.LabelFrame(content_frame, text="📝 LinkedIn Post Ideas", padding=10)
        posts_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.post_ideas_text = scrolledtext.ScrolledText(posts_section, height=10, wrap=tk.WORD,
                                                        font=('Arial', 10))
        self.post_ideas_text.pack(fill='both', expand=True, pady=5)
        
        posts_actions = ttk.Frame(posts_section)
        posts_actions.pack(fill='x', pady=5)
        ttk.Button(posts_actions, text="📋 Copy Post Ideas", 
                  command=lambda: self.copy_text(self.post_ideas_text)).pack(side='left', padx=5)
        
        # Article Topics Section
        articles_section = ttk.LabelFrame(content_frame, text="📰 Article Topics", padding=10)
        articles_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.article_topics_text = scrolledtext.ScrolledText(articles_section, height=8, wrap=tk.WORD,
                                                            font=('Arial', 10))
        self.article_topics_text.pack(fill='both', expand=True, pady=5)
        
        articles_actions = ttk.Frame(articles_section)
        articles_actions.pack(fill='x', pady=5)
        ttk.Button(articles_actions, text="📋 Copy Article Topics", 
                  command=lambda: self.copy_text(self.article_topics_text)).pack(side='left', padx=5)
    
    def create_networking_tab(self):
        """Create networking suggestions tab."""
        networking_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(networking_frame, text="🤝 Networking")
        
        # Connection Targets Section
        targets_section = ttk.LabelFrame(networking_frame, text="🎯 Connection Targets", padding=10)
        targets_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.connection_targets_text = scrolledtext.ScrolledText(targets_section, height=8, wrap=tk.WORD,
                                                                font=('Arial', 10))
        self.connection_targets_text.pack(fill='both', expand=True, pady=5)
        
        targets_actions = ttk.Frame(targets_section)
        targets_actions.pack(fill='x', pady=5)
        ttk.Button(targets_actions, text="📋 Copy Connection Strategy", 
                  command=lambda: self.copy_text(self.connection_targets_text)).pack(side='left', padx=5)
        
        # Industry Keywords Section
        keywords_section = ttk.LabelFrame(networking_frame, text="🔑 Industry Keywords", padding=10)
        keywords_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.industry_keywords_text = scrolledtext.ScrolledText(keywords_section, height=6, wrap=tk.WORD,
                                                               font=('Arial', 10))
        self.industry_keywords_text.pack(fill='both', expand=True, pady=5)
        
        keywords_actions = ttk.Frame(keywords_section)
        keywords_actions.pack(fill='x', pady=5)
        ttk.Button(keywords_actions, text="📋 Copy Keywords", 
                  command=lambda: self.copy_text(self.industry_keywords_text)).pack(side='left', padx=5)
    
    def create_optimization_tab(self):
        """Create optimization tips tab."""
        optimization_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(optimization_frame, text="🚀 Optimization")
        
        # Profile Tips Section
        tips_section = ttk.LabelFrame(optimization_frame, text="💡 Profile Improvement Tips", padding=10)
        tips_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.improvement_tips_text = scrolledtext.ScrolledText(tips_section, height=10, wrap=tk.WORD,
                                                              font=('Arial', 10))
        self.improvement_tips_text.pack(fill='both', expand=True, pady=5)
        
        # Keyword Optimization Section
        keyword_opt_section = ttk.LabelFrame(optimization_frame, text="🔍 Keyword Optimization", padding=10)
        keyword_opt_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.keyword_optimization_text = scrolledtext.ScrolledText(keyword_opt_section, height=8, wrap=tk.WORD,
                                                                  font=('Arial', 10))
        self.keyword_optimization_text.pack(fill='both', expand=True, pady=5)
    
    def create_export_tab(self):
        """Create the export tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="💾 Export")
        
        # Export Status
        status_frame = ttk.LabelFrame(export_frame, text="📊 Export Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.export_status_var = tk.StringVar(value="No content generated yet")
        ttk.Label(status_frame, textvariable=self.export_status_var, 
                 font=('Arial', 11, 'bold')).pack()
        
        # Export Options
        options_frame = ttk.LabelFrame(export_frame, text="💾 Export Formats", padding=15)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        # Text Export
        text_frame = ttk.Frame(options_frame)
        text_frame.pack(fill='x', pady=5)
        ttk.Button(text_frame, text="📄 Export Text Guide", 
                  command=self.export_text_guide).pack(side='left', padx=5)
        ttk.Label(text_frame, text="Complete LinkedIn optimization guide in text format").pack(side='left', padx=10)
        
        # JSON Export
        json_frame = ttk.Frame(options_frame)
        json_frame.pack(fill='x', pady=5)
        ttk.Button(json_frame, text="📋 Export JSON Data", 
                  command=self.export_json_data).pack(side='left', padx=5)
        ttk.Label(json_frame, text="Structured LinkedIn content data").pack(side='left', padx=10)
        
        # Action Plan Export
        plan_frame = ttk.Frame(options_frame)
        plan_frame.pack(fill='x', pady=15)
        ttk.Button(plan_frame, text="🎯 Export Action Plan", 
                  command=self.export_action_plan, style='Action.TButton').pack(side='left', padx=5)
        ttk.Label(plan_frame, text="Step-by-step LinkedIn profile improvement plan").pack(side='left', padx=10)
        
        # Usage Guide
        guide_frame = ttk.LabelFrame(export_frame, text="📚 How to Use Your LinkedIn Content", padding=15)
        guide_frame.pack(fill='x', padx=10, pady=10)
        
        guide_text = """🎯 Implementation Guide:

1. Headline: Copy your chosen headline to your LinkedIn profile. Test different versions to see which performs best.

2. Summary: Use the medium-length summary as your About section. The short version works well for InMail templates.

3. Skills: Add the recommended skills to your LinkedIn Skills section. Ask colleagues for endorsements.

4. Projects: Add projects to your Experience or Featured sections with the optimized descriptions.

5. Content Strategy: Use the post ideas and article topics for regular LinkedIn content creation.

6. Networking: Follow the connection targeting strategy to build a relevant professional network.

7. Optimization: Implement the profile improvement tips to increase visibility and engagement."""
        
        ttk.Label(guide_frame, text=guide_text, justify='left', 
                 wraplength=950, font=('Arial', 10)).pack()
        
        # Live Preview
        preview_frame = ttk.LabelFrame(export_frame, text="👁️ Live Preview")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=15, wrap=tk.WORD,
                                                     font=('Consolas', 9))
        self.preview_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_bottom_buttons(self):
        """Create bottom control buttons."""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="❌ Close", command=self.close_dialog).pack(side='right')
        ttk.Button(button_frame, text="💾 Save Settings", command=self.save_settings).pack(side='right', padx=10)
        ttk.Button(button_frame, text="📁 Open Output Folder", command=self.open_output_folder).pack(side='left')
    
    # Implementation methods would continue here...
    # Due to length limits, I'll provide key methods
    
    def browse_profile_file(self):
        """Browse for profile JSON file."""
        file_path = filedialog.askopenfilename(
            title="Select GitHub Profile JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(Path.home() / "github_profiles")
        )
        
        if file_path:
            self.profile_file_var.set(os.path.basename(file_path))
    
    def load_profile(self):
        """Load or build GitHub profile."""
        if self.source_var.get() == "github_build":
            self._build_github_profile()
        elif self.source_var.get() == "existing":
            self._load_existing_profile()
    
    def _build_github_profile(self):
        """Build GitHub profile from username."""
        username = self.github_username_var.get().strip()
        if not username:
            messagebox.showwarning("Missing Username", "Please enter a GitHub username.")
            return
        
        # Mock implementation for demo
        from profile_builder import GitHubProfile
        
        profile = GitHubProfile()
        profile.username = username
        profile.name = username.replace('_', ' ').replace('-', ' ').title()
        profile.developer_type = "Full-stack Developer"
        profile.experience_level = "Mid-level"
        # ... populate other fields
        
        self.current_profile = profile
        self.profile_status_var.set(f"✅ Profile loaded: {username}")
        self.profile_info_btn.config(state='normal')
    
    def apply_template(self, template_type: str):
        """Apply quick template settings."""
        templates = {
            "senior_dev": {
                "role": "Senior Software Developer",
                "industry": "Technology",
                "strategy": "Seeking senior technical leadership roles where I can mentor teams, architect scalable solutions, and drive technical innovation. Passionate about building high-performance applications and leading engineering best practices."
            },
            "startup": {
                "role": "Software Engineer",
                "industry": "Startup",
                "strategy": "Looking to join fast-growing startups where I can wear multiple hats, move quickly, and make significant impact. Excited about building products from 0 to 1 and working in dynamic, collaborative environments."
            },
            "enterprise": {
                "role": "Software Developer",
                "industry": "Enterprise Software",
                "strategy": "Focused on building robust, enterprise-grade software solutions that scale to millions of users. Interested in large-scale system architecture, security, and working with cross-functional teams."
            },
            "academic": {
                "role": "Research Software Engineer",
                "industry": "Research",
                "strategy": "Passionate about applying software engineering to solve complex research problems. Interested in publishing, open-source contributions, and bridging the gap between academic research and practical applications."
            }
        }
        
        template = templates.get(template_type, {})
        if template:
            self.target_role_var.set(template.get("role", ""))
            self.target_industry_var.set(template.get("industry", ""))
            
            self.content_strategy_text.delete('1.0', tk.END)
            self.content_strategy_text.insert('1.0', template.get("strategy", ""))
    
    def generate_linkedin_content(self):
        """Generate LinkedIn content from profile data."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please load a GitHub profile first.")
            return
        
        self.generation_status_var.set("Generating LinkedIn content...")
        self.generate_btn.config(state='disabled')
        self.generation_progress.start()
        
        try:
            # Update configuration from UI
            self._update_config_from_ui()
            
            # Generate LinkedIn content
            linkedin_generator = LinkedInGenerator(self.linkedin_config)
            self.current_linkedin_data = linkedin_generator.generate_linkedin_profile(self.current_profile)
            
            # Update UI with results
            self._update_results_display()
            
            # Log completion
            self._log_generation("✅ LinkedIn content generated successfully!")
            self.generation_status_var.set("✅ LinkedIn content generated!")
            self.export_status_var.set("✅ Content ready for export")
            self.regenerate_btn.config(state='normal')
            
            # Switch to results tab
            self.notebook.select(4)
            
        except Exception as e:
            self._log_generation(f"❌ Generation failed: {str(e)}")
            self.generation_status_var.set("❌ Generation failed")
            messagebox.showerror("Generation Error", f"Failed to generate LinkedIn content:\n{str(e)}")
        
        finally:
            self.generate_btn.config(state='normal')
            self.generation_progress.stop()
    
    def _update_config_from_ui(self):
        """Update LinkedIn configuration from UI values."""
        self.linkedin_config.tone = self.tone_var.get()
        self.linkedin_config.length = self.length_var.get()
        self.linkedin_config.include_emojis = self.include_emojis_var.get()
        self.linkedin_config.use_first_person = self.first_person_var.get()
        self.linkedin_config.focus_on_results = self.focus_results_var.get()
        self.linkedin_config.highlight_leadership = self.highlight_leadership_var.get()
        self.linkedin_config.emphasize_innovation = self.emphasize_innovation_var.get()
        self.linkedin_config.include_personal_touches = self.personal_touches_var.get()
        self.linkedin_config.optimize_for_keywords = self.optimize_keywords_var.get()
        self.linkedin_config.include_call_to_action = self.include_cta_var.get()
        self.linkedin_config.mention_open_to_opportunities = self.open_opportunities_var.get()
        self.linkedin_config.target_role = self.target_role_var.get() or None
        self.linkedin_config.target_industry = self.target_industry_var.get() or None
        
        # Parse comma-separated values
        self.linkedin_config.personal_brand_keywords = [
            kw.strip() for kw in self.brand_keywords_var.get().split(',') if kw.strip()
        ]
        self.linkedin_config.company_preferences = [
            comp.strip() for comp in self.company_preferences_var.get().split(',') if comp.strip()
        ]
        self.linkedin_config.location_preferences = [
            loc.strip() for loc in self.location_preferences_var.get().split(',') if loc.strip()
        ]
    
    def _update_results_display(self):
        """Update the results display with generated content."""
        if not self.current_linkedin_data:
            return
        
        data = self.current_linkedin_data
        
        # Update headline
        self.headline_text.delete('1.0', tk.END)
        self.headline_text.insert('1.0', data.headline)
        
        # Update summaries
        self.summary_short_text.delete('1.0', tk.END)
        self.summary_short_text.insert('1.0', data.summary_short)
        
        self.summary_medium_text.delete('1.0', tk.END)
        self.summary_medium_text.insert('1.0', data.summary)
        
        self.summary_long_text.delete('1.0', tk.END)
        self.summary_long_text.insert('1.0', data.summary_long)
        
        # Update skills
        skills_content = "TOP LINKEDIN SKILLS TO ADD:\n\n"
        for i, skill in enumerate(data.top_skills[:20], 1):
            skills_content += f"{i:2d}. {skill}\n"
        
        if data.skill_categories:
            skills_content += "\n\nSKILLS BY CATEGORY:\n\n"
            for category, skills in data.skill_categories.items():
                skills_content += f"{category}:\n"
                for skill in skills:
                    skills_content += f"  • {skill}\n"
                skills_content += "\n"
        
        self.skills_text.delete('1.0', tk.END)
        self.skills_text.insert('1.0', skills_content)
        
        # Update projects
        projects_content = "OPTIMIZED PROJECT DESCRIPTIONS:\n\n"
        for i, project in enumerate(data.project_descriptions, 1):
            projects_content += f"{i}. {project['name']}\n"
            projects_content += f"{project['description']}\n"
            if project.get('achievements'):
                for achievement in project['achievements']:
                    projects_content += f"  • {achievement}\n"
            projects_content += f"Technologies: {', '.join(project.get('technologies', []))}\n\n"
        
        self.projects_text.delete('1.0', tk.END)
        self.projects_text.insert('1.0', projects_content)
        
        # Update content ideas
        post_content = "LINKEDIN POST IDEAS:\n\n"
        for i, idea in enumerate(data.post_ideas, 1):
            post_content += f"{i:2d}. {idea}\n\n"
        
        self.post_ideas_text.delete('1.0', tk.END)
        self.post_ideas_text.insert('1.0', post_content)
        
        article_content = "LINKEDIN ARTICLE TOPICS:\n\n"
        for i, topic in enumerate(data.article_topics, 1):
            article_content += f"{i:2d}. {topic}\n\n"
        
        self.article_topics_text.delete('1.0', tk.END)
        self.article_topics_text.insert('1.0', article_content)
        
        # Update networking
        targets_content = "CONNECTION TARGETS:\n\n"
        for i, target in enumerate(data.connection_targets, 1):
            targets_content += f"{i:2d}. {target}\n\n"
        
        self.connection_targets_text.delete('1.0', tk.END)
        self.connection_targets_text.insert('1.0', targets_content)
        
        keywords_content = "INDUSTRY KEYWORDS TO USE:\n\n"
        keywords_content += ", ".join(data.industry_keywords)
        
        self.industry_keywords_text.delete('1.0', tk.END)
        self.industry_keywords_text.insert('1.0', keywords_content)
        
        # Update optimization tips
        tips_content = "PROFILE IMPROVEMENT TIPS:\n\n"
        for i, tip in enumerate(data.profile_improvement_tips, 1):
            tips_content += f"{i:2d}. {tip}\n\n"
        
        self.improvement_tips_text.delete('1.0', tk.END)
        self.improvement_tips_text.insert('1.0', tips_content)
        
        keyword_opt_content = "KEYWORD OPTIMIZATION:\n\n"
        for i, opt in enumerate(data.keyword_optimization, 1):
            keyword_opt_content += f"{i:2d}. {opt}\n\n"
        
        self.keyword_optimization_text.delete('1.0', tk.END)
        self.keyword_optimization_text.insert('1.0', keyword_opt_content)
    
    def copy_text(self, text_widget):
        """Copy text from widget to clipboard."""
        try:
            content = text_widget.get('1.0', tk.END).strip()
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(content)
            self.dialog.update()
            messagebox.showinfo("Copied", "Content copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy content:\n{str(e)}")
    
    def _log_generation(self, message: str):
        """Log generation message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.generation_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.generation_log.see(tk.END)
        self.dialog.update()
    
    def regenerate_content(self):
        """Regenerate content with current settings."""
        self.generate_linkedin_content()
    
    def show_profile_info(self):
        """Show profile information dialog."""
        if not self.current_profile:
            return
        
        # Similar to CV generator implementation
        pass
    
    def export_text_guide(self):
        """Export complete text guide."""
        if not self.current_linkedin_data:
            messagebox.showwarning("No Content", "Please generate LinkedIn content first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save LinkedIn Guide",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"LinkedIn_Guide_{self.current_profile.username if self.current_profile else 'Professional'}.txt"
        )
        
        if file_path:
            try:
                exporter = LinkedInExporter(self.current_linkedin_data)
                exporter.export_to_text(file_path)
                
                messagebox.showinfo("Export Success", f"LinkedIn guide exported to:\n{file_path}")
                self._log_generation(f"✅ Text guide exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export guide:\n{str(e)}")
    
    def export_json_data(self):
        """Export JSON data."""
        if not self.current_linkedin_data:
            messagebox.showwarning("No Content", "Please generate LinkedIn content first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save LinkedIn Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"LinkedIn_Data_{self.current_profile.username if self.current_profile else 'Professional'}.json"
        )
        
        if file_path:
            try:
                exporter = LinkedInExporter(self.current_linkedin_data)
                exporter.export_to_json(file_path)
                
                messagebox.showinfo("Export Success", f"LinkedIn data exported to:\n{file_path}")
                self._log_generation(f"✅ JSON data exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    
    def export_action_plan(self):
        """Export action plan for LinkedIn optimization."""
        if not self.current_linkedin_data:
            messagebox.showwarning("No Content", "Please generate LinkedIn content first.")
            return
        
        # Implementation would create a step-by-step action plan
        messagebox.showinfo("Coming Soon", "Action plan export will be available in the next update!")
    
    def open_output_folder(self):
        """Open output folder."""
        output_dir = Path.home() / "linkedin_content"
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
                'github_username': self.github_username_var.get(),
                'github_token': self.github_token_var.get(),
                'tone': self.tone_var.get(),
                'length': self.length_var.get(),
                'target_role': self.target_role_var.get(),
                'target_industry': self.target_industry_var.get(),
                'brand_keywords': self.brand_keywords_var.get(),
                'company_preferences': self.company_preferences_var.get(),
                'location_preferences': self.location_preferences_var.get()
            }
            
            settings_file = settings_dir / 'linkedin_generator_settings.json'
            with settings_file.open('w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{str(e)}")
    
    def load_settings(self):
        """Load saved settings."""
        try:
            settings_file = Path.home() / '.reporeadme' / 'linkedin_generator_settings.json'
            if settings_file.exists():
                with settings_file.open('r') as f:
                    settings = json.load(f)
                
                self.github_username_var.set(settings.get('github_username', ''))
                self.github_token_var.set(settings.get('github_token', ''))
                self.tone_var.set(settings.get('tone', 'professional'))
                self.length_var.set(settings.get('length', 'medium'))
                self.target_role_var.set(settings.get('target_role', ''))
                self.target_industry_var.set(settings.get('target_industry', ''))
                self.brand_keywords_var.set(settings.get('brand_keywords', ''))
                self.company_preferences_var.set(settings.get('company_preferences', ''))
                self.location_preferences_var.set(settings.get('location_preferences', ''))
                
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
    
    def close_dialog(self):
        """Close the dialog."""
        self.dialog.destroy()


def create_linkedin_generator(parent):
    """Create and show the LinkedIn generator dialog."""
    return LinkedInGeneratorDialog(parent)