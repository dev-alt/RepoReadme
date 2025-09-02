"""
Template Builder Module

Custom template builder dialog for creating personalized README templates.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

try:
    from .templates.readme_templates import TemplateConfig, ProjectMetadata
except ImportError:
    from templates.readme_templates import TemplateConfig, ProjectMetadata


@dataclass
class CustomTemplateConfig:
    """Configuration for custom templates."""
    name: str
    description: str
    sections: List[str]
    header_style: str
    emoji_theme: str
    color_scheme: str
    badge_style: str
    footer_style: str
    custom_sections: Dict[str, str]


class TemplateBuilderDialog:
    """Dialog for building custom README templates."""
    
    def __init__(self, parent):
        """Initialize the template builder dialog."""
        self.parent = parent
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🎨 Custom Template Builder")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_ui()
        
        # Default values
        self.template_config = CustomTemplateConfig(
            name="",
            description="",
            sections=[],
            header_style="modern",
            emoji_theme="github",
            color_scheme="default",
            badge_style="flat",
            footer_style="simple",
            custom_sections={}
        )
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Basic Info Tab
        self.create_basic_info_tab()
        
        # Sections Tab
        self.create_sections_tab()
        
        # Styling Tab
        self.create_styling_tab()
        
        # Custom Content Tab
        self.create_custom_content_tab()
        
        # Preview Tab
        self.create_preview_tab()
        
        # Button frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self.cancel, style='Action.TButton').pack(side='left')
        
        ttk.Button(button_frame, text="👁️ Preview", 
                  command=self.generate_preview, style='Action.TButton').pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="💾 Save Template", 
                  command=self.save_template, style='Action.TButton').pack(side='right')
        
        ttk.Button(button_frame, text="📁 Load Template", 
                  command=self.load_template, style='Action.TButton').pack(side='right', padx=(0, 5))
    
    def create_basic_info_tab(self):
        """Create the basic information tab."""
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="📝 Basic Info")
        
        # Template Name
        ttk.Label(basic_frame, text="Template Name:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', padx=10, pady=10)
        self.name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.name_var, width=40).grid(
            row=0, column=1, padx=10, pady=10, sticky='ew')
        
        # Description
        ttk.Label(basic_frame, text="Description:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky='nw', padx=10, pady=10)
        self.description_text = tk.Text(basic_frame, height=4, width=40, wrap=tk.WORD)
        self.description_text.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        # Template Type
        ttk.Label(basic_frame, text="Template Type:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky='w', padx=10, pady=10)
        self.template_type_var = tk.StringVar(value="custom")
        type_frame = ttk.Frame(basic_frame)
        type_frame.grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        ttk.Radiobutton(type_frame, text="🎨 Custom Design", variable=self.template_type_var, 
                       value="custom").pack(side='left')
        ttk.Radiobutton(type_frame, text="🔧 Based on Existing", variable=self.template_type_var,
                       value="based_on").pack(side='left', padx=10)
        
        # Base Template (if based on existing)
        self.base_template_var = tk.StringVar(value="modern")
        ttk.Label(basic_frame, text="Base Template:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        base_combo = ttk.Combobox(basic_frame, textvariable=self.base_template_var,
                                 values=["modern", "classic", "minimalist", "developer", "academic", 
                                        "corporate", "startup", "gaming", "security", "ai_ml", 
                                        "mobile", "opensource"])
        base_combo.grid(row=3, column=1, padx=10, pady=5, sticky='ew')
        
        # Configure grid weights
        basic_frame.columnconfigure(1, weight=1)
    
    def create_sections_tab(self):
        """Create the sections selection tab."""
        sections_frame = ttk.Frame(self.notebook)
        self.notebook.add(sections_frame, text="📋 Sections")
        
        # Left frame for available sections
        left_frame = ttk.LabelFrame(sections_frame, text="Available Sections")
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=10)
        
        # Available sections list
        self.available_sections = [
            "Header & Description", "Badges", "Table of Contents", "Features",
            "Technology Stack", "Installation", "Usage Examples", "API Documentation",
            "Architecture", "Performance Metrics", "Screenshots", "System Requirements",
            "Contributing Guidelines", "License", "Acknowledgments", "Support & Contact",
            "Roadmap", "Changelog", "FAQ", "Community Links"
        ]
        
        self.sections_listbox = tk.Listbox(left_frame, selectmode='multiple', height=15)
        self.sections_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        for section in self.available_sections:
            self.sections_listbox.insert(tk.END, section)
        
        # Middle frame for buttons
        middle_frame = ttk.Frame(sections_frame)
        middle_frame.pack(side='left', fill='y', padx=10, pady=50)
        
        ttk.Button(middle_frame, text="➡️", command=self.add_section).pack(pady=5)
        ttk.Button(middle_frame, text="⬅️", command=self.remove_section).pack(pady=5)
        ttk.Button(middle_frame, text="🔼", command=self.move_up).pack(pady=5)
        ttk.Button(middle_frame, text="🔽", command=self.move_down).pack(pady=5)
        
        # Right frame for selected sections
        right_frame = ttk.LabelFrame(sections_frame, text="Selected Sections")
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=10)
        
        self.selected_sections = tk.Listbox(right_frame, height=15)
        self.selected_sections.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_styling_tab(self):
        """Create the styling options tab."""
        styling_frame = ttk.Frame(self.notebook)
        self.notebook.add(styling_frame, text="🎨 Styling")
        
        # Header Style
        ttk.Label(styling_frame, text="Header Style:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky='w', padx=10, pady=10)
        self.header_style_var = tk.StringVar(value="modern")
        header_combo = ttk.Combobox(styling_frame, textvariable=self.header_style_var,
                                   values=["modern", "classic", "minimalist", "centered", "banner"])
        header_combo.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        # Emoji Theme
        ttk.Label(styling_frame, text="Emoji Theme:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky='w', padx=10, pady=10)
        self.emoji_theme_var = tk.StringVar(value="github")
        emoji_combo = ttk.Combobox(styling_frame, textvariable=self.emoji_theme_var,
                                  values=["github", "unicode", "none", "custom"])
        emoji_combo.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        # Color Scheme
        ttk.Label(styling_frame, text="Color Scheme:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky='w', padx=10, pady=10)
        self.color_scheme_var = tk.StringVar(value="default")
        color_combo = ttk.Combobox(styling_frame, textvariable=self.color_scheme_var,
                                  values=["default", "blue", "green", "purple", "orange", "red"])
        color_combo.grid(row=2, column=1, padx=10, pady=10, sticky='ew')
        
        # Badge Style
        ttk.Label(styling_frame, text="Badge Style:", font=('Arial', 10, 'bold')).grid(
            row=3, column=0, sticky='w', padx=10, pady=10)
        self.badge_style_var = tk.StringVar(value="flat")
        badge_combo = ttk.Combobox(styling_frame, textvariable=self.badge_style_var,
                                  values=["flat", "flat-square", "plastic", "for-the-badge"])
        badge_combo.grid(row=3, column=1, padx=10, pady=10, sticky='ew')
        
        # Footer Style
        ttk.Label(styling_frame, text="Footer Style:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky='w', padx=10, pady=10)
        self.footer_style_var = tk.StringVar(value="simple")
        footer_combo = ttk.Combobox(styling_frame, textvariable=self.footer_style_var,
                                   values=["simple", "detailed", "branding", "none"])
        footer_combo.grid(row=4, column=1, padx=10, pady=10, sticky='ew')
        
        # Configure grid weights
        styling_frame.columnconfigure(1, weight=1)
    
    def create_custom_content_tab(self):
        """Create the custom content tab."""
        custom_frame = ttk.Frame(self.notebook)
        self.notebook.add(custom_frame, text="✏️ Custom Content")
        
        # Custom sections
        ttk.Label(custom_frame, text="Add custom sections with your own content:", 
                 font=('Arial', 10, 'bold')).pack(padx=10, pady=10)
        
        # Custom section name
        section_frame = ttk.Frame(custom_frame)
        section_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(section_frame, text="Section Name:").pack(side='left')
        self.custom_section_name = tk.StringVar()
        ttk.Entry(section_frame, textvariable=self.custom_section_name).pack(side='left', padx=5)
        ttk.Button(section_frame, text="Add Section", 
                  command=self.add_custom_section).pack(side='left', padx=5)
        
        # Custom sections list
        list_frame = ttk.Frame(custom_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left: Custom sections list
        left_custom_frame = ttk.LabelFrame(list_frame, text="Custom Sections")
        left_custom_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.custom_sections_listbox = tk.Listbox(left_custom_frame)
        self.custom_sections_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.custom_sections_listbox.bind('<<ListboxSelect>>', self.on_custom_section_select)
        
        # Right: Content editor
        right_custom_frame = ttk.LabelFrame(list_frame, text="Section Content")
        right_custom_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.custom_content_text = scrolledtext.ScrolledText(right_custom_frame, height=15)
        self.custom_content_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Custom content buttons
        custom_buttons_frame = ttk.Frame(right_custom_frame)
        custom_buttons_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(custom_buttons_frame, text="💾 Save Content", 
                  command=self.save_custom_content).pack(side='right')
        ttk.Button(custom_buttons_frame, text="🗑️ Delete Section", 
                  command=self.delete_custom_section).pack(side='right', padx=5)
    
    def create_preview_tab(self):
        """Create the preview tab."""
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="👁️ Preview")
        
        # Preview controls
        controls_frame = ttk.Frame(preview_frame)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(controls_frame, text="Template Preview:", 
                 font=('Arial', 12, 'bold')).pack(side='left')
        ttk.Button(controls_frame, text="🔄 Refresh Preview", 
                  command=self.generate_preview).pack(side='right')
        
        # Preview text
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=25)
        self.preview_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def add_section(self):
        """Add selected section to template."""
        selection = self.sections_listbox.curselection()
        for index in selection:
            section = self.available_sections[index]
            if section not in [self.selected_sections.get(i) for i in range(self.selected_sections.size())]:
                self.selected_sections.insert(tk.END, section)
    
    def remove_section(self):
        """Remove selected section from template."""
        selection = self.selected_sections.curselection()
        for index in reversed(selection):
            self.selected_sections.delete(index)
    
    def move_up(self):
        """Move selected section up."""
        selection = self.selected_sections.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            item = self.selected_sections.get(index)
            self.selected_sections.delete(index)
            self.selected_sections.insert(index - 1, item)
            self.selected_sections.selection_set(index - 1)
    
    def move_down(self):
        """Move selected section down."""
        selection = self.selected_sections.curselection()
        if selection and selection[0] < self.selected_sections.size() - 1:
            index = selection[0]
            item = self.selected_sections.get(index)
            self.selected_sections.delete(index)
            self.selected_sections.insert(index + 1, item)
            self.selected_sections.selection_set(index + 1)
    
    def add_custom_section(self):
        """Add a new custom section."""
        name = self.custom_section_name.get().strip()
        if name and name not in [self.custom_sections_listbox.get(i) for i in range(self.custom_sections_listbox.size())]:
            self.custom_sections_listbox.insert(tk.END, name)
            self.custom_section_name.set("")
    
    def on_custom_section_select(self, event):
        """Handle custom section selection."""
        selection = self.custom_sections_listbox.curselection()
        if selection:
            section_name = self.custom_sections_listbox.get(selection[0])
            # Load content if it exists
            content = getattr(self.template_config.custom_sections, section_name, "")
            self.custom_content_text.delete('1.0', tk.END)
            self.custom_content_text.insert('1.0', content)
    
    def save_custom_content(self):
        """Save custom section content."""
        selection = self.custom_sections_listbox.curselection()
        if selection:
            section_name = self.custom_sections_listbox.get(selection[0])
            content = self.custom_content_text.get('1.0', tk.END).strip()
            self.template_config.custom_sections[section_name] = content
            messagebox.showinfo("Saved", f"Content saved for section: {section_name}")
    
    def delete_custom_section(self):
        """Delete selected custom section."""
        selection = self.custom_sections_listbox.curselection()
        if selection:
            section_name = self.custom_sections_listbox.get(selection[0])
            if messagebox.askyesno("Delete Section", f"Delete section '{section_name}'?"):
                self.custom_sections_listbox.delete(selection[0])
                if section_name in self.template_config.custom_sections:
                    del self.template_config.custom_sections[section_name]
                self.custom_content_text.delete('1.0', tk.END)
    
    def generate_preview(self):
        """Generate and display template preview."""
        try:
            # Update template config from UI
            self.update_template_config()
            
            # Create sample metadata for preview
            sample_metadata = ProjectMetadata()
            sample_metadata.name = "Sample Project"
            sample_metadata.description = "This is a sample project for template preview"
            sample_metadata.primary_language = "python"
            sample_metadata.frameworks = ["Flask", "SQLAlchemy"]
            sample_metadata.features = ["User Authentication", "API Integration", "Data Visualization"]
            sample_metadata.total_files = 25
            sample_metadata.code_lines = 1500
            
            # Generate preview content
            preview_content = self.generate_custom_template(sample_metadata)
            
            # Display in preview
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', preview_content)
            
            # Switch to preview tab
            self.notebook.select(4)  # Preview tab
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to generate preview: {str(e)}")
    
    def update_template_config(self):
        """Update template configuration from UI values."""
        self.template_config.name = self.name_var.get()
        self.template_config.description = self.description_text.get('1.0', tk.END).strip()
        self.template_config.header_style = self.header_style_var.get()
        self.template_config.emoji_theme = self.emoji_theme_var.get()
        self.template_config.color_scheme = self.color_scheme_var.get()
        self.template_config.badge_style = self.badge_style_var.get()
        self.template_config.footer_style = self.footer_style_var.get()
        
        # Get selected sections
        self.template_config.sections = [
            self.selected_sections.get(i) for i in range(self.selected_sections.size())
        ]
    
    def generate_custom_template(self, metadata: ProjectMetadata) -> str:
        """Generate README content using the custom template."""
        content = []
        
        # Header
        if self.template_config.header_style == "modern":
            emoji = "🚀" if metadata.project_type != "unknown" else "📦"
            content.append(f"# {emoji} {metadata.name}")
        elif self.template_config.header_style == "classic":
            content.append(f"# {metadata.name}")
        elif self.template_config.header_style == "centered":
            content.append(f"<h1 align='center'>{metadata.name}</h1>")
        
        content.append("")
        
        if metadata.description:
            if self.template_config.header_style == "modern":
                content.append(f"> {metadata.description}")
            else:
                content.append(metadata.description)
            content.append("")
        
        # Process selected sections
        for section in self.template_config.sections:
            if section == "Badges":
                self._add_badges_section(content, metadata)
            elif section == "Features":
                self._add_features_section(content, metadata)
            elif section == "Technology Stack":
                self._add_tech_stack_section(content, metadata)
            elif section == "Installation":
                self._add_installation_section(content, metadata)
            # Add more section handlers as needed
        
        # Add custom sections
        for section_name, section_content in self.template_config.custom_sections.items():
            content.append(f"## {section_name}")
            content.append("")
            content.append(section_content)
            content.append("")
        
        # Footer
        if self.template_config.footer_style != "none":
            content.append("---")
            content.append("")
            if self.template_config.footer_style == "simple":
                content.append("Made with ❤️")
            elif self.template_config.footer_style == "branding":
                content.append("Generated with [RepoReadme](https://github.com/dev-alt/RepoReadme)")
        
        return "\n".join(content)
    
    def _add_badges_section(self, content, metadata):
        """Add badges section to content."""
        if self.template_config.badge_style != "none":
            badges = []
            if metadata.primary_language:
                badges.append(f"![{metadata.primary_language}](https://img.shields.io/badge/-{metadata.primary_language}-blue?style={self.template_config.badge_style})")
            if metadata.license:
                badges.append(f"![License](https://img.shields.io/badge/license-{metadata.license}-green?style={self.template_config.badge_style})")
            
            if badges:
                content.extend(badges)
                content.append("")
    
    def _add_features_section(self, content, metadata):
        """Add features section to content."""
        if metadata.features:
            emoji = "✨" if self.template_config.emoji_theme != "none" else ""
            content.append(f"## {emoji} Features")
            content.append("")
            for feature in metadata.features:
                bullet = "-" if self.template_config.emoji_theme == "none" else "- ⭐"
                content.append(f"{bullet} **{feature}**")
            content.append("")
    
    def _add_tech_stack_section(self, content, metadata):
        """Add technology stack section to content."""
        if metadata.primary_language or metadata.frameworks:
            emoji = "🛠️" if self.template_config.emoji_theme != "none" else ""
            content.append(f"## {emoji} Technology Stack")
            content.append("")
            if metadata.primary_language:
                content.append(f"**Language:** {metadata.primary_language.title()}")
            if metadata.frameworks:
                content.append(f"**Frameworks:** {', '.join(metadata.frameworks)}")
            content.append("")
    
    def _add_installation_section(self, content, metadata):
        """Add installation section to content."""
        emoji = "🚀" if self.template_config.emoji_theme != "none" else ""
        content.append(f"## {emoji} Installation")
        content.append("")
        content.append("```bash")
        content.append("# Clone the repository")
        content.append(f"git clone <repository-url>")
        content.append("")
        content.append("# Install dependencies")
        if metadata.primary_language == "python":
            content.append("pip install -r requirements.txt")
        elif metadata.primary_language in ["javascript", "typescript"]:
            content.append("npm install")
        else:
            content.append("# Install your dependencies here")
        content.append("```")
        content.append("")
    
    def save_template(self):
        """Save the custom template to file."""
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Please enter a template name.")
            return
        
        self.update_template_config()
        
        # Get save location
        templates_dir = Path.home() / ".reporeadme" / "custom_templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.template_config.name.lower().replace(' ', '_')}.json"
        file_path = filedialog.asksaveasfilename(
            title="Save Custom Template",
            initialdir=str(templates_dir),
            initialfile=filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.template_config), f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Template saved successfully!\n\n📁 {file_path}")
                self.result = self.template_config
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save template: {str(e)}")
    
    def load_template(self):
        """Load a custom template from file."""
        templates_dir = Path.home() / ".reporeadme" / "custom_templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = filedialog.askopenfilename(
            title="Load Custom Template",
            initialdir=str(templates_dir),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load data into UI
                self.name_var.set(data.get('name', ''))
                self.description_text.delete('1.0', tk.END)
                self.description_text.insert('1.0', data.get('description', ''))
                
                self.header_style_var.set(data.get('header_style', 'modern'))
                self.emoji_theme_var.set(data.get('emoji_theme', 'github'))
                self.color_scheme_var.set(data.get('color_scheme', 'default'))
                self.badge_style_var.set(data.get('badge_style', 'flat'))
                self.footer_style_var.set(data.get('footer_style', 'simple'))
                
                # Load sections
                self.selected_sections.delete(0, tk.END)
                for section in data.get('sections', []):
                    self.selected_sections.insert(tk.END, section)
                
                # Load custom sections
                self.custom_sections_listbox.delete(0, tk.END)
                custom_sections = data.get('custom_sections', {})
                for section_name in custom_sections.keys():
                    self.custom_sections_listbox.insert(tk.END, section_name)
                
                self.template_config.custom_sections = custom_sections
                
                messagebox.showinfo("Success", "Template loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load template: {str(e)}")
    
    def cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.dialog.destroy()
    
    def get_result(self):
        """Get the dialog result."""
        self.dialog.wait_window()
        return self.result


def create_custom_template_builder(parent):
    """Create and show the custom template builder dialog."""
    dialog = TemplateBuilderDialog(parent)
    return dialog.get_result()