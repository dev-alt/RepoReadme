#!/usr/bin/env python3
"""
AI LinkedIn Bio Generator Demo

Demonstrates the new AI-powered LinkedIn bio generation feature that analyzes
all GitHub repositories to create compelling, personalized professional bios.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from ai_linkedin_bio_generator import AILinkedInBioGenerator, AIBioConfig, AIGeneratedBio
    from profile_builder import GitHubProfile
except ImportError:
    # Alternative import for when running from different location
    sys.path.insert(0, str(Path(__file__).parent / 'src'))
    from ai_linkedin_bio_generator import AILinkedInBioGenerator, AIBioConfig, AIGeneratedBio
    from profile_builder import GitHubProfile

def create_demo_github_profile():
    """Create a comprehensive demo GitHub profile for AI bio generation."""
    profile = GitHubProfile()
    
    # Basic information
    profile.username = "ai-demo-user"
    profile.name = "Alex Developer"
    profile.email = "alex@example.com"
    profile.location = "San Francisco, CA"
    profile.bio = "Full-stack developer passionate about AI and open source"
    
    # GitHub statistics
    profile.total_repositories = 45
    profile.original_repositories = 38
    profile.forked_repositories = 7
    profile.public_repositories = 43
    profile.total_stars_received = 387
    profile.total_forks_received = 89
    
    # Languages and skills
    profile.languages_used = {
        "Python": 3200, "JavaScript": 2800, "TypeScript": 2100,
        "Go": 1500, "Java": 1200, "Rust": 800, "HTML": 700, "CSS": 500
    }
    profile.primary_languages = ["Python", "JavaScript", "TypeScript", "Go", "Java", "Rust"]
    
    # Featured projects
    profile.featured_projects = [
        {
            "name": "ai-code-analyzer",
            "description": "Advanced AI-powered code analysis tool with ML-based optimization suggestions",
            "stars": 156,
            "forks": 34,
            "language": "Python",
            "topics": ["ai", "machine-learning", "code-analysis", "optimization"],
            "project_type": "library"
        },
        {
            "name": "realtime-dashboard",
            "description": "High-performance real-time analytics dashboard built with React and WebSocket",
            "stars": 89,
            "forks": 23,
            "language": "TypeScript",
            "topics": ["react", "websocket", "dashboard", "analytics"],
            "project_type": "web-app"
        },
        {
            "name": "microservice-orchestrator",
            "description": "Lightweight microservice orchestration platform with auto-scaling capabilities",
            "stars": 67,
            "forks": 18,
            "language": "Go",
            "topics": ["microservices", "orchestration", "scaling", "kubernetes"],
            "project_type": "infrastructure"
        },
        {
            "name": "blockchain-voting-system",
            "description": "Secure blockchain-based voting system with cryptographic verification",
            "stars": 43,
            "forks": 12,
            "language": "Rust",
            "topics": ["blockchain", "voting", "security", "cryptography"],
            "project_type": "application"
        },
        {
            "name": "smart-contract-auditor",
            "description": "Automated smart contract security auditing tool with vulnerability detection",
            "stars": 32,
            "forks": 8,
            "language": "JavaScript",
            "topics": ["blockchain", "security", "auditing", "smart-contracts"],
            "project_type": "cli-tool"
        }
    ]
    
    # Quality metrics
    profile.collaboration_score = 92.5
    profile.innovation_score = 88.7
    profile.repositories_with_readme = 41
    profile.repositories_with_tests = 32
    profile.repositories_with_ci = 28
    profile.repositories_with_docker = 15
    
    return profile

def demo_ai_bio_generation():
    """Demonstrate AI bio generation with different configurations."""
    print("🤖 AI LinkedIn Bio Generator Demo")
    print("=" * 60)
    print()
    
    # Create demo profile
    profile = create_demo_github_profile()
    print(f"📊 Demo Profile: {profile.name} (@{profile.username})")
    print(f"   Repositories: {profile.total_repositories}")
    print(f"   Languages: {', '.join(profile.primary_languages[:4])}")
    print(f"   Stars: {profile.total_stars_received} | Forks: {profile.total_forks_received}")
    print()
    
    # Demo different bio styles
    styles_to_demo = [
        ("professional", "Professional & Polished"),
        ("creative", "Creative & Engaging"),
        ("technical", "Technical & Detailed"),
        ("startup", "Startup & Entrepreneurial")
    ]
    
    for style, description in styles_to_demo:
        print(f"🎨 {description} Bio")
        print("-" * 40)
        
        # Configure AI bio generator
        config = AIBioConfig(
            bio_style=style,
            tone="confident",
            length="medium",
            target_role="Senior Software Engineer",
            target_industry="technology",
            use_metrics=True,
            include_passion_statement=True,
            include_call_to_action=True,
            emphasize_collaboration=True,
            highlight_innovation=True
        )
        
        # Generate bio
        ai_generator = AILinkedInBioGenerator(config)
        ai_bio = ai_generator.generate_ai_bio(profile, config)
        
        # Display results
        print(f"📝 Generated Bio ({len(ai_bio.primary_bio)} chars):")
        print(f'"{ai_bio.primary_bio}"')
        print()
        
        # Show quality metrics
        print(f"📊 Quality Metrics:")
        print(f"   • Readability: {ai_bio.readability_score:.1f}/100")
        print(f"   • Engagement: {ai_bio.engagement_potential.title()}")
        print(f"   • SEO Score: {ai_bio.search_optimization_score:.1f}/100")
        print(f"   • Uniqueness: {ai_bio.uniqueness_score:.1f}/100")
        
        if ai_bio.authenticity_indicators:
            print(f"   • Authenticity: {', '.join(ai_bio.authenticity_indicators)}")
        
        print()
        print("=" * 60)
        print()

def demo_bio_components():
    """Demonstrate bio component breakdown."""
    print("🔧 Bio Component Analysis Demo")
    print("=" * 60)
    print()
    
    profile = create_demo_github_profile()
    
    config = AIBioConfig(
        bio_style="professional",
        tone="confident",
        length="long",
        target_role="Senior Full-Stack Engineer",
        use_metrics=True,
        include_passion_statement=True,
        include_call_to_action=True
    )
    
    ai_generator = AILinkedInBioGenerator(config)
    ai_bio = ai_generator.generate_ai_bio(profile, config)
    
    print("🏗️ Bio Component Breakdown:")
    print()
    
    components = [
        ("Opening Hook", ai_bio.opening_hook),
        ("Expertise Statement", ai_bio.expertise_statement),
        ("Achievement Highlights", ai_bio.achievement_highlights),
        ("Value Proposition", ai_bio.value_proposition),
        ("Passion Statement", ai_bio.passion_statement),
        ("Call to Action", ai_bio.call_to_action)
    ]
    
    for component_name, content in components:
        if content:
            print(f"📌 {component_name}:")
            print(f'   "{content}"')
            print(f"   ({len(content)} characters)")
            print()
    
    print("✨ Complete Bio Assembly:")
    print("-" * 30)
    print(f'"{ai_bio.primary_bio}"')
    print()
    print(f"📏 Total: {len(ai_bio.primary_bio)} characters, {len(ai_bio.primary_bio.split())} words")

def demo_customization_options():
    """Demonstrate customization options."""
    print("⚙️ AI Bio Customization Demo")
    print("=" * 60)
    print()
    
    profile = create_demo_github_profile()
    
    # Demo different tones
    tones = ["confident", "humble", "enthusiastic", "analytical", "visionary"]
    
    print("🎭 Tone Variations:")
    print()
    
    for tone in tones[:3]:  # Show first 3 tones
        config = AIBioConfig(
            bio_style="professional",
            tone=tone,
            length="short",
            target_role="Software Engineer"
        )
        
        ai_generator = AILinkedInBioGenerator(config)
        ai_bio = ai_generator.generate_ai_bio(profile, config)
        
        print(f"🎯 {tone.title()} Tone:")
        print(f'   "{ai_bio.primary_bio[:150]}..."')
        print()
    
    # Demo different lengths
    print("📏 Length Variations:")
    print()
    
    lengths = ["short", "medium", "long"]
    
    for length in lengths:
        config = AIBioConfig(
            bio_style="professional",
            tone="confident",
            length=length,
            target_role="Software Engineer"
        )
        
        ai_generator = AILinkedInBioGenerator(config)
        ai_bio = ai_generator.generate_ai_bio(profile, config)
        
        word_count = len(ai_bio.primary_bio.split())
        char_count = len(ai_bio.primary_bio)
        
        print(f"📐 {length.title()} ({word_count} words, {char_count} chars):")
        print(f'   "{ai_bio.primary_bio[:100]}..."')
        print()

def main():
    """Run the complete AI bio demo."""
    try:
        print("🚀 RepoReadme AI LinkedIn Bio Generator")
        print("Advanced AI-Powered Professional Bio Creation")
        print("=" * 80)
        print()
        
        # Run demos
        demo_ai_bio_generation()
        demo_bio_components()
        demo_customization_options()
        
        print("🎉 Demo Complete!")
        print("=" * 80)
        print()
        print("✨ Key Features Demonstrated:")
        print("   • AI analysis of GitHub repositories")
        print("   • Multiple bio styles (Professional, Creative, Technical, Startup)")
        print("   • Customizable tone and length")
        print("   • Component-based bio assembly")
        print("   • Quality metrics and optimization")
        print("   • Authenticity and uniqueness scoring")
        print()
        print("🚀 How to Use:")
        print("   1. Launch: python main_unified.py")
        print("   2. Navigate to: '🤖 AI Bio' tab")
        print("   3. Configure your preferences")
        print("   4. Click 'Generate AI Bio'")
        print("   5. Choose from multiple versions")
        print("   6. Copy and optimize for LinkedIn")
        print()
        print("💡 The AI analyzes ALL your repositories to create authentic,")
        print("   data-driven bios that showcase your real skills and impact!")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()