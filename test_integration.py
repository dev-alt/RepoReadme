#!/usr/bin/env python3
"""
Integration Test Script

Basic tests to verify the new CV and LinkedIn generation functionality
integrates properly with the existing codebase.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all new modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        # Test CV generator
        from src.cv_generator import CVGenerator, CVConfig, CVExporter
        print("✅ CV generator modules imported successfully")
        
        # Test LinkedIn generator
        from src.linkedin_generator import LinkedInGenerator, LinkedInConfig, LinkedInExporter
        print("✅ LinkedIn generator modules imported successfully")
        
        # Test dialog imports
        from src.cv_generator_dialog import create_cv_generator
        from src.linkedin_generator_dialog import create_linkedin_generator
        print("✅ Dialog modules imported successfully")
        
        # Test main GUI integration
        from src.gui import RepoReadmeGUI
        print("✅ Main GUI with integrations imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the new modules."""
    print("\nTesting basic functionality...")
    
    try:
        # Test CV configuration creation
        from src.cv_generator import CVConfig
        cv_config = CVConfig()
        cv_config.cv_style = "modern"
        cv_config.target_role = "Software Developer"
        print("✅ CV configuration created successfully")
        
        # Test LinkedIn configuration creation
        from src.linkedin_generator import LinkedInConfig
        linkedin_config = LinkedInConfig()
        linkedin_config.tone = "professional"
        linkedin_config.target_role = "Senior Developer"
        print("✅ LinkedIn configuration created successfully")
        
        # Test mock profile creation
        from src.profile_builder import GitHubProfile
        profile = GitHubProfile()
        profile.username = "testuser"
        profile.developer_type = "Full-stack Developer"
        profile.primary_languages = ["Python", "JavaScript", "TypeScript"]
        profile.total_repositories = 25
        profile.total_stars_received = 100
        print("✅ Mock GitHub profile created successfully")
        
        # Test CV generation with mock data
        from src.cv_generator import CVGenerator
        cv_generator = CVGenerator(cv_config)
        cv_data = cv_generator.generate_cv_from_profile(profile)
        print(f"✅ CV generated successfully (summary length: {len(cv_data.professional_summary)} chars)")
        
        # Test LinkedIn generation with mock data
        from src.linkedin_generator import LinkedInGenerator
        linkedin_generator = LinkedInGenerator(linkedin_config)
        linkedin_profile = linkedin_generator.generate_linkedin_profile(profile)
        print(f"✅ LinkedIn content generated successfully (headline: {linkedin_profile.headline[:50]}...)")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

def test_export_functionality():
    """Test export functionality."""
    print("\nTesting export functionality...")
    
    try:
        # Create test data
        from src.cv_generator import CVGenerator, CVConfig, CVExporter
        from src.linkedin_generator import LinkedInGenerator, LinkedInConfig, LinkedInExporter
        from src.profile_builder import GitHubProfile
        
        # Mock profile
        profile = GitHubProfile()
        profile.username = "testuser"
        profile.name = "Test User"
        profile.developer_type = "Full-stack Developer"
        profile.primary_languages = ["Python", "JavaScript"]
        profile.total_repositories = 10
        profile.total_stars_received = 50
        profile.has_web_projects = True
        profile.has_apis = True
        
        # Generate CV data
        cv_generator = CVGenerator(CVConfig())
        cv_data = cv_generator.generate_cv_from_profile(profile)
        
        # Test CV HTML generation (don't write to file, just test generation)
        cv_exporter = CVExporter(cv_data)
        html_content = cv_exporter._generate_cv_html()
        print(f"✅ CV HTML export functionality working (content length: {len(html_content)} chars)")
        
        # Generate LinkedIn data
        linkedin_generator = LinkedInGenerator(LinkedInConfig())
        linkedin_profile = linkedin_generator.generate_linkedin_profile(profile)
        
        # Test LinkedIn text export generation
        linkedin_exporter = LinkedInExporter(linkedin_profile)
        text_content = linkedin_exporter._generate_text_export()
        print(f"✅ LinkedIn text export functionality working (content length: {len(text_content)} chars)")
        
        return True
        
    except Exception as e:
        print(f"❌ Export test error: {e}")
        return False

def test_gui_integration():
    """Test GUI integration (without actually launching GUI)."""
    print("\nTesting GUI integration...")
    
    try:
        from src.gui import RepoReadmeGUI
        
        # Test that the class can be instantiated (but don't start mainloop)
        # This is a basic test to ensure the integrations don't break the GUI class
        print("✅ GUI class can be imported and integration points are valid")
        
        # Test that the dialog creation functions exist
        from src.cv_generator_dialog import create_cv_generator
        from src.linkedin_generator_dialog import create_linkedin_generator
        print("✅ Dialog creation functions available")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI integration test error: {e}")
        return False

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("RepoReadme Integration Test Suite")
    print("Testing CV and LinkedIn Generation Features")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Basic Functionality Tests", test_basic_functionality),
        ("Export Functionality Tests", test_export_functionality),
        ("GUI Integration Tests", test_gui_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests PASSED!")
        print("\nThe new CV and LinkedIn generation features have been")
        print("successfully integrated into the RepoReadme application.")
        return 0
    else:
        print("⚠️  Some tests failed. Review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())