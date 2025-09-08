#!/usr/bin/env python3
"""
Demo Script for New Features

Demonstrates the expanded CV and LinkedIn generation capabilities
added to the RepoReadme application.
"""

from src.cv_generator import CVGenerator, CVConfig
from src.linkedin_generator import LinkedInGenerator, LinkedInConfig
from src.profile_builder import GitHubProfile

def create_sample_github_profile():
    """Create a comprehensive sample GitHub profile for demonstration."""
    profile = GitHubProfile()
    
    # Basic information
    profile.username = "johndeveloper"
    profile.name = "John Developer"
    profile.email = "john.developer@example.com"
    profile.location = "San Francisco, CA"
    profile.website = "https://johndeveloper.dev"
    profile.bio = "Full-stack developer passionate about building scalable web applications"
    
    # GitHub statistics
    profile.total_repositories = 42
    profile.original_repositories = 35
    profile.forked_repositories = 7
    profile.public_repositories = 40
    profile.private_repositories = 2
    profile.total_stars_received = 285
    profile.total_forks_received = 67
    
    # Developer profile
    profile.developer_type = "Full-stack Developer"
    profile.experience_level = "Senior"
    
    # Languages and skills
    profile.languages_used = {
        "Python": 2500, "JavaScript": 2200, "TypeScript": 1800,
        "Java": 1200, "Go": 800, "HTML": 600, "CSS": 500, "SQL": 400
    }
    profile.languages_percentage = {
        "Python": 28.5, "JavaScript": 25.1, "TypeScript": 20.5,
        "Java": 13.7, "Go": 9.1, "HTML": 2.3, "CSS": 0.8
    }
    profile.primary_languages = ["Python", "JavaScript", "TypeScript", "Java", "Go"]
    
    # Project types
    profile.has_web_projects = True
    profile.has_mobile_projects = False
    profile.has_apis = True
    profile.has_libraries = True
    profile.has_cli_tools = True
    
    # Quality metrics
    profile.collaboration_score = 85.2
    profile.innovation_score = 78.9
    profile.repositories_with_readme = 38
    profile.repositories_with_tests = 25
    profile.repositories_with_ci = 15
    profile.repositories_with_docker = 8
    
    # Featured projects
    profile.featured_projects = [
        {
            "name": "awesome-api-framework",
            "description": "A modern Python framework for building REST APIs with automatic documentation",
            "stars": 127,
            "forks": 23,
            "language": "Python",
            "url": "https://github.com/johndeveloper/awesome-api-framework",
            "topics": ["api", "framework", "python", "rest"],
            "project_type": "library",
            "updated_at": "2024-08-15T10:30:00Z",
            "has_readme": True
        },
        {
            "name": "react-dashboard-pro",
            "description": "Professional dashboard template built with React and TypeScript",
            "stars": 89,
            "forks": 34,
            "language": "TypeScript",
            "url": "https://github.com/johndeveloper/react-dashboard-pro",
            "topics": ["react", "typescript", "dashboard", "ui"],
            "project_type": "web-app",
            "updated_at": "2024-09-01T14:20:00Z",
            "has_readme": True
        },
        {
            "name": "microservice-toolkit",
            "description": "Go-based toolkit for building and deploying microservices",
            "stars": 45,
            "forks": 12,
            "language": "Go",
            "url": "https://github.com/johndeveloper/microservice-toolkit",
            "topics": ["go", "microservices", "devops", "kubernetes"],
            "project_type": "library",
            "updated_at": "2024-07-22T09:15:00Z",
            "has_readme": True
        }
    ]
    
    # Project categories
    profile.project_categories = {
        "web-apps": [
            {"name": "react-dashboard-pro", "stars": 89, "language": "TypeScript"},
            {"name": "e-commerce-platform", "stars": 32, "language": "JavaScript"}
        ],
        "libraries": [
            {"name": "awesome-api-framework", "stars": 127, "language": "Python"},
            {"name": "microservice-toolkit", "stars": 45, "language": "Go"}
        ],
        "cli-tools": [
            {"name": "deploy-helper", "stars": 18, "language": "Python"},
            {"name": "git-workflow", "stars": 12, "language": "Go"}
        ]
    }
    
    return profile

def demo_cv_generation():
    """Demonstrate CV generation functionality."""
    print("🔨 CV Generation Demo")
    print("=" * 50)
    
    # Create sample profile
    profile = create_sample_github_profile()
    
    # Configure CV generation
    cv_config = CVConfig()
    cv_config.cv_style = "modern"
    cv_config.target_role = "Senior Full-Stack Developer"
    cv_config.target_industry = "FinTech"
    cv_config.include_summary = True
    cv_config.include_skills = True
    cv_config.include_projects = True
    cv_config.include_achievements = True
    cv_config.max_featured_projects = 6
    cv_config.use_professional_language = True
    
    # Additional personal information
    additional_info = {
        "email": "john.developer@example.com",
        "phone": "+1 (555) 123-4567",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/johndeveloper",
        "website": "https://johndeveloper.dev",
        "work_experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Startup Inc",
                "location": "San Francisco, CA",
                "start_date": "2022",
                "end_date": "Present",
                "description": "Lead development of scalable web applications and mentor junior developers",
                "achievements": [
                    "Built microservices architecture handling 1M+ requests/day",
                    "Mentored 3 junior developers and led code review processes",
                    "Reduced deployment time by 60% through CI/CD optimization"
                ],
                "technologies": ["Python", "JavaScript", "Docker", "Kubernetes"]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "school": "University of California, Berkeley",
                "year": "2019"
            }
        ]
    }
    
    # Generate CV
    cv_generator = CVGenerator(cv_config)
    cv_data = cv_generator.generate_cv_from_profile(profile, additional_info)
    
    print(f"✅ Generated CV for: {cv_data.personal_info.get('name', 'Professional')}")
    print(f"📊 Professional Summary ({len(cv_data.professional_summary)} chars):")
    print(f"   {cv_data.professional_summary[:150]}...")
    print(f"🔧 Technical Skills: {len(cv_data.technical_skills)} categories")
    print(f"🚀 Featured Projects: {len(cv_data.featured_projects)}")
    print(f"💼 Work Experience: {len(cv_data.work_experience)} entries")
    print(f"🏆 Achievements: {len(cv_data.achievements)}")
    
    return cv_data

def demo_linkedin_generation():
    """Demonstrate LinkedIn profile generation functionality."""
    print("\n💼 LinkedIn Profile Generation Demo")
    print("=" * 50)
    
    # Create sample profile
    profile = create_sample_github_profile()
    
    # Configure LinkedIn generation
    linkedin_config = LinkedInConfig()
    linkedin_config.tone = "professional"
    linkedin_config.length = "medium"
    linkedin_config.target_role = "Senior Full-Stack Developer"
    linkedin_config.target_industry = "FinTech"
    linkedin_config.include_emojis = False
    linkedin_config.use_first_person = True
    linkedin_config.focus_on_results = True
    linkedin_config.emphasize_innovation = True
    linkedin_config.optimize_for_keywords = True
    linkedin_config.include_call_to_action = True
    linkedin_config.personal_brand_keywords = ["full-stack", "scalable", "microservices", "fintech"]
    linkedin_config.company_preferences = ["Google", "Meta", "Netflix", "Stripe"]
    
    # Generate LinkedIn content
    linkedin_generator = LinkedInGenerator(linkedin_config)
    linkedin_profile = linkedin_generator.generate_linkedin_profile(profile)
    
    print(f"✅ Generated LinkedIn content for: @{profile.username}")
    print(f"📢 Headline ({len(linkedin_profile.headline)} chars):")
    print(f"   {linkedin_profile.headline}")
    print(f"📄 Professional Summary ({len(linkedin_profile.summary)} chars):")
    print(f"   {linkedin_profile.summary[:200]}...")
    print(f"🎯 Top Skills: {len(linkedin_profile.top_skills)}")
    print(f"💡 Post Ideas: {len(linkedin_profile.post_ideas)}")
    print(f"📰 Article Topics: {len(linkedin_profile.article_topics)}")
    print(f"🤝 Connection Targets: {len(linkedin_profile.connection_targets)}")
    print(f"🔍 Industry Keywords: {len(linkedin_profile.industry_keywords)}")
    print(f"💡 Improvement Tips: {len(linkedin_profile.profile_improvement_tips)}")
    
    return linkedin_profile

def demo_export_capabilities():
    """Demonstrate export capabilities."""
    print("\n💾 Export Capabilities Demo")
    print("=" * 50)
    
    # Generate sample data
    profile = create_sample_github_profile()
    
    # Generate CV
    cv_generator = CVGenerator(CVConfig())
    cv_data = cv_generator.generate_cv_from_profile(profile)
    
    # Generate LinkedIn content
    linkedin_generator = LinkedInGenerator(LinkedInConfig())
    linkedin_profile = linkedin_generator.generate_linkedin_profile(profile)
    
    # Test export formats
    from src.cv_generator import CVExporter
    from src.linkedin_generator import LinkedInExporter
    
    cv_exporter = CVExporter(cv_data)
    linkedin_exporter = LinkedInExporter(linkedin_profile)
    
    # Generate export content (without actually writing files)
    html_content = cv_exporter._generate_cv_html()
    linkedin_text = linkedin_exporter._generate_text_export()
    
    print(f"✅ CV HTML Export: {len(html_content):,} characters")
    print(f"✅ LinkedIn Text Export: {len(linkedin_text):,} characters")
    print("📋 Available Export Formats:")
    print("   • CV: HTML, PDF, JSON")
    print("   • LinkedIn: Text Guide, JSON, Action Plan")

def main():
    """Run the complete demo."""
    print("🚀 RepoReadme Extended Features Demo")
    print("Demonstrating CV and LinkedIn Generation Capabilities")
    print("=" * 70)
    
    try:
        # Demo CV generation
        cv_data = demo_cv_generation()
        
        # Demo LinkedIn generation
        linkedin_profile = demo_linkedin_generation()
        
        # Demo export capabilities
        demo_export_capabilities()
        
        print(f"\n🎉 Demo Complete!")
        print("=" * 70)
        print("✨ Key Features Demonstrated:")
        print("   • Professional CV generation from GitHub profiles")
        print("   • LinkedIn profile content optimization")
        print("   • Multiple export formats (HTML, PDF, JSON, Text)")
        print("   • Customizable styling and targeting options")
        print("   • Integration with existing RepoReadme architecture")
        print("")
        print("🔧 How to Use:")
        print("   1. Run the main application: python main.py")
        print("   2. Click 'CV Generator' or 'LinkedIn Generator'")
        print("   3. Enter your GitHub username")
        print("   4. Customize settings and generate content")
        print("   5. Export in your preferred format")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()