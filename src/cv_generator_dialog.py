#!/usr/bin/env python3
"""
CV Generator Dialog

GUI interface for generating professional CVs from GitHub profile data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from .cv_generator import CVGenerator, CVConfig, CVExporter
    from .profile_builder import GitHubProfile, GitHubProfileBuilder, ProfileBuilderConfig
    from .config.github_auth import GitHubAuthManager
    from .utils.logger import get_logger
except ImportError:
    from cv_generator import CVGenerator, CVConfig, CVExporter
    from profile_builder import GitHubProfile, GitHubProfileBuilder, ProfileBuilderConfig
    from config.github_auth import GitHubAuthManager
    from utils.logger import get_logger


class CVGeneratorDialog:
    """Dialog for generating CVs from GitHub profiles."""
    
    def __init__(self, parent):
        """Initialize the CV generator dialog."""
        self.parent = parent
        self.logger = get_logger()
        self.auth_manager = GitHubAuthManager()
        
        # Create main dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📄 CV Generator")
        self.dialog.geometry("1000x800")
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
        self.current_cv_data = None
        self.is_generating = False
        
        # Configuration
        self.cv_config = CVConfig()
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Profile Source
        self.create_source_tab()
        
        # Tab 2: CV Configuration
        self.create_config_tab()
        
        # Tab 3: Personal Information
        self.create_personal_tab()
        
        # Tab 4: Generate CV
        self.create_generate_tab()
        
        # Tab 5: Preview & Export
        self.create_export_tab()
        
        # Bottom buttons
        self.create_bottom_buttons()
    
    def create_source_tab(self):
        """Create the profile source tab."""
        source_frame = ttk.Frame(self.notebook)
        self.notebook.add(source_frame, text="👤 Profile Source")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(source_frame, text="📋 Instructions", padding=15)
        instructions_frame.pack(fill='x', padx=10, pady=10)
        
        instructions_text = """Welcome to the CV Generator! This tool creates professional CVs from your GitHub profile data.
        
You can either:
1. Use an existing GitHub profile (if you've already built one)
2. Build a new profile by analyzing GitHub repositories
3. Import CV data from a JSON file

The CV generator will create professional resume content including:
• Professional summary based on your GitHub activity
• Technical skills extracted from your repositories  
• Project descriptions optimized for job applications
• Professional experience synthesized from your work"""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text, 
                                    justify='left', wraplength=900, font=('Arial', 10))
        instructions_label.pack()
        
        # Profile Source Options
        source_options_frame = ttk.LabelFrame(source_frame, text="📊 Profile Data Source", padding=15)
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
                 font=('Arial', 10, 'bold')).pack()
        
        # Load/Build Profile Button
        action_frame = ttk.Frame(source_frame)
        action_frame.pack(fill='x', padx=10, pady=20)
        
        self.load_profile_btn = ttk.Button(action_frame, text="🔄 Load/Build Profile", 
                                          command=self.load_profile, style='Action.TButton')
        self.load_profile_btn.pack(side='left', padx=10)
        
        self.profile_info_btn = ttk.Button(action_frame, text="ℹ️ View Profile Info", 
                                          command=self.show_profile_info, state='disabled')
        self.profile_info_btn.pack(side='left', padx=10)
    
    def create_config_tab(self):
        """Create the CV configuration tab."""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ CV Configuration")
        
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
        
        # CV Style and Format
        style_frame = ttk.LabelFrame(scrollable_frame, text="🎨 CV Style & Format", padding=15)
        style_frame.pack(fill='x', padx=10, pady=10)
        
        # CV Style
        style_options_frame = ttk.Frame(style_frame)
        style_options_frame.pack(fill='x', pady=5)
        
        ttk.Label(style_options_frame, text="CV Style:").pack(side='left')
        self.cv_style_var = tk.StringVar(value=self.cv_config.cv_style)
        style_combo = ttk.Combobox(style_options_frame, textvariable=self.cv_style_var,
                                  values=['modern', 'classic', 'minimal', 'technical', 'creative'],
                                  state='readonly', width=15)
        style_combo.pack(side='left', padx=10)
        
        # CV Format
        ttk.Label(style_options_frame, text="Format:").pack(side='left', padx=(20, 0))
        self.cv_format_var = tk.StringVar(value=self.cv_config.cv_format)
        format_combo = ttk.Combobox(style_options_frame, textvariable=self.cv_format_var,
                                   values=['html', 'pdf', 'json'], state='readonly', width=10)
        format_combo.pack(side='left', padx=10)
        
        # Content Sections
        sections_frame = ttk.LabelFrame(scrollable_frame, text="📝 Content Sections", padding=15)
        sections_frame.pack(fill='x', padx=10, pady=10)
        
        sections_grid = ttk.Frame(sections_frame)
        sections_grid.pack(fill='x')
        
        # Create checkbuttons for content sections
        self.include_summary_var = tk.BooleanVar(value=self.cv_config.include_summary)
        self.include_skills_var = tk.BooleanVar(value=self.cv_config.include_skills)
        self.include_projects_var = tk.BooleanVar(value=self.cv_config.include_projects)
        self.include_experience_var = tk.BooleanVar(value=self.cv_config.include_experience)
        self.include_education_var = tk.BooleanVar(value=self.cv_config.include_education)
        self.include_achievements_var = tk.BooleanVar(value=self.cv_config.include_achievements)
        self.include_contact_var = tk.BooleanVar(value=self.cv_config.include_contact_info)
        
        # Arrange in grid
        ttk.Checkbutton(sections_grid, text="📋 Professional Summary", 
                       variable=self.include_summary_var).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(sections_grid, text="🔧 Technical Skills", 
                       variable=self.include_skills_var).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(sections_grid, text="💼 Work Experience", 
                       variable=self.include_experience_var).grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(sections_grid, text="🚀 Featured Projects", 
                       variable=self.include_projects_var).grid(row=1, column=1, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(sections_grid, text="🎓 Education", 
                       variable=self.include_education_var).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(sections_grid, text="🏆 Achievements", 
                       variable=self.include_achievements_var).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(sections_grid, text="📞 Contact Information", 
                       variable=self.include_contact_var).grid(row=3, column=0, sticky='w', padx=5, pady=2)
        
        # Projects Configuration
        projects_frame = ttk.LabelFrame(scrollable_frame, text="🚀 Projects Configuration", padding=15)
        projects_frame.pack(fill='x', padx=10, pady=10)
        
        # Max featured projects
        projects_options_frame = ttk.Frame(projects_frame)
        projects_options_frame.pack(fill='x', pady=5)
        
        ttk.Label(projects_options_frame, text="Max Featured Projects:").pack(side='left')
        self.max_projects_var = tk.IntVar(value=self.cv_config.max_featured_projects)
        ttk.Spinbox(projects_options_frame, from_=3, to=15, textvariable=self.max_projects_var, 
                   width=5).pack(side='left', padx=10)
        
        ttk.Label(projects_options_frame, text="Min Stars:").pack(side='left', padx=(20, 0))
        self.min_stars_var = tk.IntVar(value=self.cv_config.min_stars_for_projects)
        ttk.Spinbox(projects_options_frame, from_=0, to=50, textvariable=self.min_stars_var, 
                   width=5).pack(side='left', padx=10)
        
        # Project options
        project_options_frame = ttk.Frame(projects_frame)
        project_options_frame.pack(fill='x', pady=5)
        
        self.prioritize_recent_var = tk.BooleanVar(value=self.cv_config.prioritize_recent_projects)
        self.group_projects_var = tk.BooleanVar(value=self.cv_config.group_projects_by_type)
        
        ttk.Checkbutton(project_options_frame, text="⏰ Prioritize Recent Projects", 
                       variable=self.prioritize_recent_var).pack(anchor='w')
        ttk.Checkbutton(project_options_frame, text="📂 Group Projects by Type", 
                       variable=self.group_projects_var).pack(anchor='w')
        
        # Skills Configuration
        skills_frame = ttk.LabelFrame(scrollable_frame, text="🔧 Skills Configuration", padding=15)
        skills_frame.pack(fill='x', padx=10, pady=10)
        
        skills_options_frame = ttk.Frame(skills_frame)
        skills_options_frame.pack(fill='x', pady=5)
        
        ttk.Label(skills_options_frame, text="Max Skills to Show:").pack(side='left')
        self.max_skills_var = tk.IntVar(value=self.cv_config.max_skills_to_show)
        ttk.Spinbox(skills_options_frame, from_=8, to=25, textvariable=self.max_skills_var, 
                   width=5).pack(side='left', padx=10)
        
        skills_checkboxes_frame = ttk.Frame(skills_frame)
        skills_checkboxes_frame.pack(fill='x', pady=5)
        
        self.group_skills_var = tk.BooleanVar(value=self.cv_config.group_skills_by_category)
        self.show_proficiency_var = tk.BooleanVar(value=self.cv_config.show_skill_proficiency)
        
        ttk.Checkbutton(skills_checkboxes_frame, text="📂 Group Skills by Category", 
                       variable=self.group_skills_var).pack(anchor='w')
        ttk.Checkbutton(skills_checkboxes_frame, text="📊 Show Skill Proficiency Levels", 
                       variable=self.show_proficiency_var).pack(anchor='w')
        
        # Targeting Configuration
        targeting_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Job Targeting", padding=15)
        targeting_frame.pack(fill='x', padx=10, pady=10)
        
        # Target role
        role_frame = ttk.Frame(targeting_frame)
        role_frame.pack(fill='x', pady=5)
        
        ttk.Label(role_frame, text="Target Role:").pack(side='left')
        self.target_role_var = tk.StringVar(value=self.cv_config.target_role or "")
        role_entry = ttk.Entry(role_frame, textvariable=self.target_role_var, width=25)
        role_entry.pack(side='left', padx=10)
        
        # Target industry
        ttk.Label(role_frame, text="Industry:").pack(side='left', padx=(20, 0))
        self.target_industry_var = tk.StringVar(value=self.cv_config.target_industry or "")
        industry_entry = ttk.Entry(role_frame, textvariable=self.target_industry_var, width=20)
        industry_entry.pack(side='left', padx=10)
        
        # Additional Options
        options_frame = ttk.LabelFrame(scrollable_frame, text="🔧 Additional Options", padding=15)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        self.include_portfolio_link_var = tk.BooleanVar(value=self.cv_config.include_portfolio_link)
        self.include_github_stats_var = tk.BooleanVar(value=self.cv_config.include_github_stats)
        self.professional_language_var = tk.BooleanVar(value=self.cv_config.use_professional_language)
        
        ttk.Checkbutton(options_frame, text="🔗 Include Portfolio Link", 
                       variable=self.include_portfolio_link_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="📊 Include GitHub Statistics", 
                       variable=self.include_github_stats_var).pack(anchor='w')
        ttk.Checkbutton(options_frame, text="💼 Use Professional Language", 
                       variable=self.professional_language_var).pack(anchor='w')
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_personal_tab(self):
        """Create the personal information tab."""
        personal_frame = ttk.Frame(self.notebook)
        self.notebook.add(personal_frame, text="👤 Personal Info")
        
        # Instructions
        instructions_frame = ttk.LabelFrame(personal_frame, text="📝 Additional Information", padding=15)
        instructions_frame.pack(fill='x', padx=10, pady=10)
        
        instructions_text = """Complete your personal information to enhance your CV. 
This information will be combined with your GitHub profile data."""
        
        ttk.Label(instructions_frame, text=instructions_text, wraplength=800, 
                 font=('Arial', 10)).pack()
        
        # Personal Information Form
        info_frame = ttk.LabelFrame(personal_frame, text="📋 Personal Information", padding=15)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        # Create form fields
        form_frame = ttk.Frame(info_frame)
        form_frame.pack(fill='x')
        
        # Personal details
        self.full_name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.linkedin_var = tk.StringVar()
        self.website_var = tk.StringVar()
        
        # Row 0
        ttk.Label(form_frame, text="Full Name:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(form_frame, textvariable=self.full_name_var, width=25).grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        ttk.Label(form_frame, text="Phone:").grid(row=0, column=2, sticky='w', padx=(20, 0), pady=5)
        ttk.Entry(form_frame, textvariable=self.phone_var, width=20).grid(row=0, column=3, padx=10, pady=5, sticky='ew')
        
        # Row 1
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(form_frame, textvariable=self.email_var, width=25).grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        
        ttk.Label(form_frame, text="Location:").grid(row=1, column=2, sticky='w', padx=(20, 0), pady=5)
        ttk.Entry(form_frame, textvariable=self.location_var, width=20).grid(row=1, column=3, padx=10, pady=5, sticky='ew')
        
        # Row 2
        ttk.Label(form_frame, text="LinkedIn:").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(form_frame, textvariable=self.linkedin_var, width=25).grid(row=2, column=1, padx=10, pady=5, sticky='ew')
        
        ttk.Label(form_frame, text="Website:").grid(row=2, column=2, sticky='w', padx=(20, 0), pady=5)
        ttk.Entry(form_frame, textvariable=self.website_var, width=20).grid(row=2, column=3, padx=10, pady=5, sticky='ew')
        
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        
        # Work Experience
        experience_frame = ttk.LabelFrame(personal_frame, text="💼 Work Experience", padding=15)
        experience_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Experience text area
        exp_instructions = ttk.Label(experience_frame, 
            text="Enter work experience as JSON (optional - will synthesize from GitHub if empty):")
        exp_instructions.pack(anchor='w', pady=(0, 5))
        
        self.experience_text = scrolledtext.ScrolledText(experience_frame, height=8, wrap=tk.WORD,
                                                        font=('Consolas', 9))
        self.experience_text.pack(fill='both', expand=True, pady=5)
        
        # Sample JSON
        sample_json = '''[
  {
    "title": "Senior Software Developer",
    "company": "Tech Company Inc",
    "location": "San Francisco, CA", 
    "start_date": "2022",
    "end_date": "Present",
    "description": "Led development of web applications",
    "achievements": ["Built 5 major features", "Mentored 3 junior developers"],
    "technologies": ["JavaScript", "React", "Node.js"]
  }
]'''
        
        self.experience_text.insert('1.0', sample_json)
        
        # Education & Certifications
        education_frame = ttk.Frame(experience_frame)
        education_frame.pack(fill='x', pady=10)
        
        # Education
        edu_left_frame = ttk.LabelFrame(education_frame, text="🎓 Education", padding=10)
        edu_left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.education_text = scrolledtext.ScrolledText(edu_left_frame, height=4, wrap=tk.WORD,
                                                       font=('Consolas', 9))
        self.education_text.pack(fill='both', expand=True)
        
        edu_sample = '''[
  {
    "degree": "Bachelor of Science",
    "field": "Computer Science", 
    "school": "University Name",
    "year": "2020"
  }
]'''
        self.education_text.insert('1.0', edu_sample)
        
        # Certifications
        cert_right_frame = ttk.LabelFrame(education_frame, text="📜 Certifications", padding=10)
        cert_right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.certifications_text = scrolledtext.ScrolledText(cert_right_frame, height=4, wrap=tk.WORD,
                                                            font=('Consolas', 9))
        self.certifications_text.pack(fill='both', expand=True)
        
        cert_sample = '''[
  {
    "name": "AWS Certified Developer",
    "issuer": "Amazon Web Services", 
    "year": "2023"
  }
]'''
        self.certifications_text.insert('1.0', cert_sample)
    
    def create_generate_tab(self):
        """Create the CV generation tab."""
        generate_frame = ttk.Frame(self.notebook)
        self.notebook.add(generate_frame, text="🔨 Generate CV")
        
        # Generation Status
        status_frame = ttk.LabelFrame(generate_frame, text="📊 Generation Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.generation_status_var = tk.StringVar(value="Ready to generate CV")
        ttk.Label(status_frame, textvariable=self.generation_status_var, 
                 font=('Arial', 11, 'bold')).pack()
        
        # Generate Controls
        controls_frame = ttk.Frame(generate_frame)
        controls_frame.pack(fill='x', padx=10, pady=20)
        
        self.generate_btn = ttk.Button(controls_frame, text="🔨 Generate CV", 
                                      command=self.generate_cv, style='Action.TButton')
        self.generate_btn.pack(side='left', padx=10)
        
        self.preview_btn = ttk.Button(controls_frame, text="👁️ Preview CV", 
                                     command=self.preview_cv, state='disabled')
        self.preview_btn.pack(side='left', padx=10)
        
        # Generation Log
        log_frame = ttk.LabelFrame(generate_frame, text="📝 Generation Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.generation_log = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.generation_log.pack(fill='both', expand=True, padx=5, pady=5)
        
        # CV Preview
        preview_frame = ttk.LabelFrame(generate_frame, text="👁️ CV Summary")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.cv_summary_text = scrolledtext.ScrolledText(preview_frame, height=10, wrap=tk.WORD,
                                                        font=('Consolas', 9), state='disabled')
        self.cv_summary_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_export_tab(self):
        """Create the export tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="💾 Export CV")
        
        # Export Status
        status_frame = ttk.LabelFrame(export_frame, text="📊 Export Status", padding=15)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.export_status_var = tk.StringVar(value="No CV generated yet")
        ttk.Label(status_frame, textvariable=self.export_status_var, 
                 font=('Arial', 11, 'bold')).pack()
        
        # Export Options
        options_frame = ttk.LabelFrame(export_frame, text="💾 Export Formats", padding=15)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        # HTML Export
        html_frame = ttk.Frame(options_frame)
        html_frame.pack(fill='x', pady=5)
        ttk.Button(html_frame, text="🌐 Export HTML CV", 
                  command=self.export_html_cv).pack(side='left', padx=5)
        ttk.Label(html_frame, text="Professional HTML CV ready for web or print").pack(side='left', padx=10)
        
        # PDF Export
        pdf_frame = ttk.Frame(options_frame)
        pdf_frame.pack(fill='x', pady=5)
        ttk.Button(pdf_frame, text="📄 Export PDF CV", 
                  command=self.export_pdf_cv).pack(side='left', padx=5)
        ttk.Label(pdf_frame, text="Print-ready PDF document").pack(side='left', padx=10)
        
        # JSON Export
        json_frame = ttk.Frame(options_frame)
        json_frame.pack(fill='x', pady=5)
        ttk.Button(json_frame, text="📋 Export JSON Data", 
                  command=self.export_json_cv).pack(side='left', padx=5)
        ttk.Label(json_frame, text="Structured CV data for further processing").pack(side='left', padx=10)
        
        # Batch Export
        batch_frame = ttk.Frame(options_frame)
        batch_frame.pack(fill='x', pady=15)
        ttk.Button(batch_frame, text="📦 Export All Formats", 
                  command=self.export_all_formats, style='Action.TButton').pack(side='left', padx=5)
        ttk.Label(batch_frame, text="Export HTML, PDF, and JSON versions").pack(side='left', padx=10)
        
        # Usage Tips
        tips_frame = ttk.LabelFrame(export_frame, text="💡 Usage Tips", padding=15)
        tips_frame.pack(fill='x', padx=10, pady=10)
        
        tips_text = """Tips for using your generated CV:

• HTML Version: Best for online applications and ATS systems. Can be easily customized with CSS.
• PDF Version: Perfect for email attachments and printing. Maintains formatting across devices.
• JSON Version: Use for importing into other tools or building custom CV templates.

The CV generator creates professional, ATS-friendly resumes that highlight your GitHub achievements
and technical skills while maintaining traditional resume structure that recruiters expect."""
        
        ttk.Label(tips_frame, text=tips_text, justify='left', 
                 wraplength=900, font=('Arial', 10)).pack()
        
        # Sample Preview
        sample_frame = ttk.LabelFrame(export_frame, text="👁️ CV Content Preview")
        sample_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.cv_preview_text = scrolledtext.ScrolledText(sample_frame, height=12, wrap=tk.WORD,
                                                        font=('Consolas', 9))
        self.cv_preview_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_bottom_buttons(self):
        """Create bottom control buttons."""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="❌ Close", command=self.close_dialog).pack(side='right')
        ttk.Button(button_frame, text="💾 Save Settings", command=self.save_settings).pack(side='right', padx=10)
        ttk.Button(button_frame, text="📁 Open Output Folder", command=self.open_output_folder).pack(side='left')
    
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
        """Load or build GitHub profile based on selected source."""
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
        
        # Show building process (simplified)
        self.profile_status_var.set("Building profile...")
        self.load_profile_btn.config(state='disabled')
        
        try:
            # This would typically use the GitHubProfileBuilder
            # For now, create a mock profile for demonstration
            from profile_builder import GitHubProfile
            
            # Mock profile data - in real implementation, this would be built
            profile = GitHubProfile()
            profile.username = username
            profile.name = username.replace('_', ' ').replace('-', ' ').title()
            profile.developer_type = "Full-stack Developer"
            profile.experience_level = "Mid-level"
            profile.total_repositories = 25
            profile.original_repositories = 20
            profile.total_stars_received = 150
            profile.total_forks_received = 45
            profile.languages_used = {"Python": 1000, "JavaScript": 800, "TypeScript": 600}
            profile.languages_percentage = {"Python": 35.7, "JavaScript": 28.6, "TypeScript": 21.4}
            profile.primary_languages = ["Python", "JavaScript", "TypeScript"]
            profile.has_web_projects = True
            profile.has_mobile_projects = False
            profile.has_apis = True
            profile.has_libraries = True
            profile.has_cli_tools = True
            profile.collaboration_score = 75.0
            profile.innovation_score = 68.0
            profile.featured_projects = [
                {"name": "awesome-project", "description": "An awesome web application", 
                 "stars": 45, "forks": 12, "language": "Python", "url": "https://github.com/user/awesome-project",
                 "topics": ["web", "api"], "project_type": "web-app", "updated_at": "2024-01-15T00:00:00Z"}
            ]
            
            self.current_profile = profile
            self.profile_status_var.set(f"✅ Profile loaded: {username} ({profile.developer_type})")
            self.profile_info_btn.config(state='normal')
            
            # Auto-fill some personal information from profile
            if not self.full_name_var.get() and profile.name:
                self.full_name_var.set(profile.name)
            if not self.email_var.get() and profile.email:
                self.email_var.set(profile.email)
            if not self.location_var.get() and profile.location:
                self.location_var.set(profile.location)
            if not self.website_var.get() and profile.website:
                self.website_var.set(profile.website)
            
        except Exception as e:
            messagebox.showerror("Profile Build Error", f"Failed to build GitHub profile:\n{str(e)}")
            self.profile_status_var.set("❌ Profile build failed")
        
        finally:
            self.load_profile_btn.config(state='normal')
    
    def _load_existing_profile(self):
        """Load existing profile from JSON file."""
        if not self.profile_file_var.get():
            messagebox.showwarning("No File Selected", "Please select a profile JSON file.")
            return
        
        try:
            # Load profile from JSON
            # This is a simplified version
            self.profile_status_var.set("✅ Profile loaded from file")
            self.profile_info_btn.config(state='normal')
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load profile file:\n{str(e)}")
    
    def show_profile_info(self):
        """Show detailed profile information."""
        if not self.current_profile:
            return
        
        profile = self.current_profile
        
        info_window = tk.Toplevel(self.dialog)
        info_window.title("Profile Information")
        info_window.geometry("600x400")
        info_window.transient(self.dialog)
        
        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, font=('Consolas', 10))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        info_text = f"""GitHub Profile Information

Username: {profile.username}
Name: {profile.name or 'Not specified'}
Developer Type: {profile.developer_type}
Experience Level: {profile.experience_level}

Repository Statistics:
• Total Repositories: {profile.total_repositories}
• Original Projects: {profile.original_repositories}
• Stars Received: {profile.total_stars_received}
• Forks Received: {profile.total_forks_received}

Technical Profile:
• Languages Used: {len(profile.languages_used)}
• Primary Languages: {', '.join(profile.primary_languages[:5])}
• Collaboration Score: {profile.collaboration_score:.1f}/100
• Innovation Score: {profile.innovation_score:.1f}/100

Project Types:
• Web Projects: {'Yes' if profile.has_web_projects else 'No'}
• Mobile Projects: {'Yes' if profile.has_mobile_projects else 'No'}
• API Projects: {'Yes' if profile.has_apis else 'No'}
• Libraries: {'Yes' if profile.has_libraries else 'No'}
• CLI Tools: {'Yes' if profile.has_cli_tools else 'No'}

Featured Projects: {len(profile.featured_projects)}"""
        
        text_widget.insert('1.0', info_text)
        text_widget.config(state='disabled')
    
    def generate_cv(self):
        """Generate CV from profile data."""
        if not self.current_profile:
            messagebox.showwarning("No Profile", "Please load a GitHub profile first.")
            return
        
        self.generation_status_var.set("Generating CV...")
        self.generate_btn.config(state='disabled')
        
        try:
            # Update configuration from UI
            self._update_config_from_ui()
            
            # Collect additional information
            additional_info = self._collect_additional_info()
            
            # Generate CV
            cv_generator = CVGenerator(self.cv_config)
            self.current_cv_data = cv_generator.generate_cv_from_profile(
                self.current_profile, additional_info
            )
            
            # Log generation
            self._log_generation("✅ CV generated successfully!")
            self._log_generation(f"• Professional Summary: {len(self.current_cv_data.professional_summary)} characters")
            self._log_generation(f"• Technical Skills: {len(self.current_cv_data.technical_skills)} categories")
            self._log_generation(f"• Featured Projects: {len(self.current_cv_data.featured_projects)}")
            self._log_generation(f"• Work Experience: {len(self.current_cv_data.work_experience)} entries")
            self._log_generation(f"• Achievements: {len(self.current_cv_data.achievements)}")
            
            # Update UI
            self.generation_status_var.set("✅ CV generated successfully!")
            self.export_status_var.set("✅ CV ready for export")
            self.preview_btn.config(state='normal')
            
            # Update preview
            self._update_cv_preview()
            
            # Switch to preview tab
            self.notebook.select(4)
            
        except Exception as e:
            self._log_generation(f"❌ CV generation failed: {str(e)}")
            self.generation_status_var.set("❌ CV generation failed")
            messagebox.showerror("Generation Error", f"Failed to generate CV:\n{str(e)}")
        
        finally:
            self.generate_btn.config(state='normal')
    
    def _update_config_from_ui(self):
        """Update CV configuration from UI values."""
        self.cv_config.cv_style = self.cv_style_var.get()
        self.cv_config.cv_format = self.cv_format_var.get()
        self.cv_config.include_summary = self.include_summary_var.get()
        self.cv_config.include_skills = self.include_skills_var.get()
        self.cv_config.include_projects = self.include_projects_var.get()
        self.cv_config.include_experience = self.include_experience_var.get()
        self.cv_config.include_education = self.include_education_var.get()
        self.cv_config.include_achievements = self.include_achievements_var.get()
        self.cv_config.include_contact_info = self.include_contact_var.get()
        self.cv_config.max_featured_projects = self.max_projects_var.get()
        self.cv_config.min_stars_for_projects = self.min_stars_var.get()
        self.cv_config.prioritize_recent_projects = self.prioritize_recent_var.get()
        self.cv_config.group_projects_by_type = self.group_projects_var.get()
        self.cv_config.max_skills_to_show = self.max_skills_var.get()
        self.cv_config.group_skills_by_category = self.group_skills_var.get()
        self.cv_config.show_skill_proficiency = self.show_proficiency_var.get()
        self.cv_config.target_role = self.target_role_var.get() or None
        self.cv_config.target_industry = self.target_industry_var.get() or None
        self.cv_config.include_portfolio_link = self.include_portfolio_link_var.get()
        self.cv_config.include_github_stats = self.include_github_stats_var.get()
        self.cv_config.use_professional_language = self.professional_language_var.get()
        
        # Update personal info in config
        self.cv_config.personal_info = {
            'name': self.full_name_var.get(),
            'phone': self.phone_var.get(),
            'email': self.email_var.get(),
            'location': self.location_var.get(),
            'linkedin': self.linkedin_var.get(),
            'website': self.website_var.get()
        }
    
    def _collect_additional_info(self) -> Dict[str, Any]:
        """Collect additional information from the form."""
        additional_info = {}
        
        # Personal information
        additional_info.update(self.cv_config.personal_info)
        
        # Work experience
        try:
            exp_text = self.experience_text.get('1.0', tk.END).strip()
            if exp_text and exp_text != "[]":
                additional_info['work_experience'] = json.loads(exp_text)
        except json.JSONDecodeError:
            self._log_generation("⚠️ Warning: Invalid work experience JSON, skipping")
        
        # Education
        try:
            edu_text = self.education_text.get('1.0', tk.END).strip()
            if edu_text and edu_text != "[]":
                additional_info['education'] = json.loads(edu_text)
        except json.JSONDecodeError:
            self._log_generation("⚠️ Warning: Invalid education JSON, skipping")
        
        # Certifications
        try:
            cert_text = self.certifications_text.get('1.0', tk.END).strip()
            if cert_text and cert_text != "[]":
                additional_info['certifications'] = json.loads(cert_text)
        except json.JSONDecodeError:
            self._log_generation("⚠️ Warning: Invalid certifications JSON, skipping")
        
        return additional_info
    
    def _log_generation(self, message: str):
        """Log generation message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.generation_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.generation_log.see(tk.END)
        self.dialog.update()
    
    def _update_cv_preview(self):
        """Update CV preview displays."""
        if not self.current_cv_data:
            return
        
        # Summary preview
        summary_text = f"""CV Generation Summary

Personal Information:
Name: {self.current_cv_data.personal_info.get('name', 'Not specified')}
Email: {self.current_cv_data.personal_info.get('email', 'Not specified')}
Location: {self.current_cv_data.personal_info.get('location', 'Not specified')}

Professional Summary:
{self.current_cv_data.professional_summary[:200]}{'...' if len(self.current_cv_data.professional_summary) > 200 else ''}

Technical Skills ({len(self.current_cv_data.technical_skills)} categories):
{', '.join(list(self.current_cv_data.technical_skills.keys())[:5])}

Featured Projects: {len(self.current_cv_data.featured_projects)}
Work Experience: {len(self.current_cv_data.work_experience)}
Achievements: {len(self.current_cv_data.achievements)}

CV Style: {self.current_cv_data.cv_style}
Target Role: {self.current_cv_data.target_role or 'Not specified'}"""
        
        self.cv_summary_text.config(state='normal')
        self.cv_summary_text.delete('1.0', tk.END)
        self.cv_summary_text.insert('1.0', summary_text)
        self.cv_summary_text.config(state='disabled')
        
        # Full preview
        full_preview = self._generate_full_preview()
        self.cv_preview_text.delete('1.0', tk.END)
        self.cv_preview_text.insert('1.0', full_preview)
    
    def _generate_full_preview(self) -> str:
        """Generate full CV preview text."""
        if not self.current_cv_data:
            return "No CV data available"
        
        sections = []
        
        # Header
        sections.append("="*60)
        sections.append(f"CV PREVIEW - {self.current_cv_data.personal_info.get('name', 'Professional')}")
        sections.append("="*60)
        
        # Contact Info
        contact_info = []
        if self.current_cv_data.personal_info.get('email'):
            contact_info.append(f"Email: {self.current_cv_data.personal_info['email']}")
        if self.current_cv_data.personal_info.get('phone'):
            contact_info.append(f"Phone: {self.current_cv_data.personal_info['phone']}")
        if self.current_cv_data.personal_info.get('location'):
            contact_info.append(f"Location: {self.current_cv_data.personal_info['location']}")
        
        if contact_info:
            sections.append(" | ".join(contact_info))
            sections.append("")
        
        # Professional Summary
        if self.current_cv_data.professional_summary:
            sections.append("PROFESSIONAL SUMMARY")
            sections.append("-"*30)
            sections.append(self.current_cv_data.professional_summary)
            sections.append("")
        
        # Technical Skills
        if self.current_cv_data.technical_skills:
            sections.append("TECHNICAL SKILLS")
            sections.append("-"*20)
            for category, skills in self.current_cv_data.technical_skills.items():
                sections.append(f"{category}: {', '.join(skills[:8])}")
            sections.append("")
        
        # Work Experience
        if self.current_cv_data.work_experience:
            sections.append("WORK EXPERIENCE")
            sections.append("-"*20)
            for exp in self.current_cv_data.work_experience:
                sections.append(f"{exp['title']} at {exp['company']}")
                sections.append(f"{exp['start_date']} - {exp['end_date']}")
                sections.append(exp['description'][:200] + "...")
                sections.append("")
        
        # Featured Projects
        if self.current_cv_data.featured_projects:
            sections.append("FEATURED PROJECTS")
            sections.append("-"*20)
            for project in self.current_cv_data.featured_projects[:3]:
                sections.append(f"{project['name']} ({project.get('year', 'Recent')})")
                sections.append(project['description'][:150] + "...")
                if project.get('technologies'):
                    sections.append(f"Technologies: {', '.join(project['technologies'][:5])}")
                sections.append("")
        
        # Achievements
        if self.current_cv_data.achievements:
            sections.append("ACHIEVEMENTS")
            sections.append("-"*15)
            for achievement in self.current_cv_data.achievements[:5]:
                sections.append(f"• {achievement}")
            sections.append("")
        
        return "\n".join(sections)
    
    def preview_cv(self):
        """Preview CV in browser."""
        if not self.current_cv_data:
            messagebox.showwarning("No CV", "Please generate a CV first.")
            return
        
        try:
            # Generate HTML temporarily for preview
            exporter = CVExporter(self.current_cv_data)
            html_content = exporter._generate_cv_html()
            
            # Save to temporary file and open
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
            temp_file.write(html_content)
            temp_file.close()
            
            webbrowser.open(f"file://{temp_file.name}")
            self._log_generation("✅ CV preview opened in browser")
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview CV:\n{str(e)}")
    
    def export_html_cv(self):
        """Export CV to HTML format."""
        if not self.current_cv_data:
            messagebox.showwarning("No CV", "Please generate a CV first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save HTML CV",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=f"CV_{self.current_cv_data.personal_info.get('name', 'Professional').replace(' ', '_')}.html"
        )
        
        if file_path:
            try:
                exporter = CVExporter(self.current_cv_data)
                exporter.export_to_html(file_path)
                
                messagebox.showinfo("Export Success", f"HTML CV exported to:\n{file_path}")
                self._log_generation(f"✅ HTML CV exported to {file_path}")
                
                # Ask if user wants to open it
                if messagebox.askyesno("Open CV", "Would you like to open the CV in your browser?"):
                    webbrowser.open(f"file://{os.path.abspath(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export HTML CV:\n{str(e)}")
    
    def export_pdf_cv(self):
        """Export CV to PDF format."""
        if not self.current_cv_data:
            messagebox.showwarning("No CV", "Please generate a CV first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save PDF CV",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"CV_{self.current_cv_data.personal_info.get('name', 'Professional').replace(' ', '_')}.pdf"
        )
        
        if file_path:
            try:
                exporter = CVExporter(self.current_cv_data)
                exporter.export_to_pdf(file_path)
                
                messagebox.showinfo("Export Success", f"PDF CV exported to:\n{file_path}")
                self._log_generation(f"✅ PDF CV exported to {file_path}")
                
            except Exception as e:
                if "No PDF generation method available" in str(e):
                    messagebox.showerror("PDF Export Error", 
                        "PDF generation requires additional software. Please install one of the following:\n\n"
                        "• WeasyPrint: pip install weasyprint\n"
                        "• Playwright: pip install playwright && playwright install chromium\n"
                        "• wkhtmltopdf: Download from https://wkhtmltopdf.org/\n"
                        "• Google Chrome or Chromium browser\n\n"
                        "Then try exporting again.")
                else:
                    messagebox.showerror("Export Error", f"Failed to export PDF CV:\n{str(e)}")
    
    def export_json_cv(self):
        """Export CV to JSON format."""
        if not self.current_cv_data:
            messagebox.showwarning("No CV", "Please generate a CV first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save CV Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"CV_{self.current_cv_data.personal_info.get('name', 'Professional').replace(' ', '_')}_data.json"
        )
        
        if file_path:
            try:
                exporter = CVExporter(self.current_cv_data)
                exporter.export_to_json(file_path)
                
                messagebox.showinfo("Export Success", f"CV data exported to:\n{file_path}")
                self._log_generation(f"✅ JSON CV data exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export CV data:\n{str(e)}")
    
    def export_all_formats(self):
        """Export CV in all available formats."""
        if not self.current_cv_data:
            messagebox.showwarning("No CV", "Please generate a CV first.")
            return
        
        folder_path = filedialog.askdirectory(title="Select Export Folder")
        if not folder_path:
            return
        
        try:
            exporter = CVExporter(self.current_cv_data)
            
            name = self.current_cv_data.personal_info.get('name', 'Professional').replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Define file paths
            html_file = os.path.join(folder_path, f"CV_{name}_{timestamp}.html")
            pdf_file = os.path.join(folder_path, f"CV_{name}_{timestamp}.pdf")
            json_file = os.path.join(folder_path, f"CV_{name}_data_{timestamp}.json")
            
            files_created = []
            
            # Export HTML
            exporter.export_to_html(html_file)
            files_created.append(os.path.basename(html_file))
            
            # Export JSON
            exporter.export_to_json(json_file)
            files_created.append(os.path.basename(json_file))
            
            # Export PDF (with error handling)
            pdf_success = False
            try:
                exporter.export_to_pdf(pdf_file)
                files_created.append(os.path.basename(pdf_file))
                pdf_success = True
            except Exception as e:
                self.logger.warning(f"PDF export failed: {e}")
            
            # Show completion message
            success_msg = f"CV exported to:\n{folder_path}\n\nFiles created:\n"
            success_msg += "\n".join(f"• {file}" for file in files_created)
            
            if not pdf_success:
                success_msg += "\n\n⚠️ Note: PDF export failed. Install a PDF generator for PDF support."
            
            messagebox.showinfo("Export Complete", success_msg)
            self._log_generation(f"✅ All CV formats exported to {folder_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CV formats:\n{str(e)}")
    
    def open_output_folder(self):
        """Open the output folder in file manager."""
        output_dir = Path.home() / "cv_exports"
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
                'cv_style': self.cv_style_var.get(),
                'cv_format': self.cv_format_var.get(),
                'target_role': self.target_role_var.get(),
                'target_industry': self.target_industry_var.get(),
                'personal_info': {
                    'full_name': self.full_name_var.get(),
                    'phone': self.phone_var.get(),
                    'email': self.email_var.get(),
                    'location': self.location_var.get(),
                    'linkedin': self.linkedin_var.get(),
                    'website': self.website_var.get()
                }
            }
            
            settings_file = settings_dir / 'cv_generator_settings.json'
            with settings_file.open('w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{str(e)}")
    
    def load_settings(self):
        """Load saved settings."""
        try:
            settings_file = Path.home() / '.reporeadme' / 'cv_generator_settings.json'
            if settings_file.exists():
                with settings_file.open('r') as f:
                    settings = json.load(f)
                
                self.github_username_var.set(settings.get('github_username', ''))
                self.github_token_var.set(settings.get('github_token', ''))
                self.cv_style_var.set(settings.get('cv_style', 'modern'))
                self.cv_format_var.set(settings.get('cv_format', 'html'))
                self.target_role_var.set(settings.get('target_role', ''))
                self.target_industry_var.set(settings.get('target_industry', ''))
                
                personal_info = settings.get('personal_info', {})
                self.full_name_var.set(personal_info.get('full_name', ''))
                self.phone_var.set(personal_info.get('phone', ''))
                self.email_var.set(personal_info.get('email', ''))
                self.location_var.set(personal_info.get('location', ''))
                self.linkedin_var.set(personal_info.get('linkedin', ''))
                self.website_var.set(personal_info.get('website', ''))
                
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
    
    def close_dialog(self):
        """Close the dialog."""
        self.dialog.destroy()


def create_cv_generator(parent):
    """Create and show the CV generator dialog."""
    return CVGeneratorDialog(parent)