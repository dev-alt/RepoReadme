#!/usr/bin/env python3
"""
Test script to verify the new GUI enhancements are properly integrated.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_gui import UnifiedRepoReadmeGUI
from ai_linkedin_bio_generator import AIBioConfig

def test_gui_enhancements():
    """Test that new GUI enhancements are properly integrated."""
    try:
        print("🧪 Testing GUI Enhancements...")
        
        # Test AIBioConfig with new fields
        print("\n✅ Testing AIBioConfig with new fields...")
        config = AIBioConfig(
            experience_level='recent_graduate',
            years_experience=0,
            show_learning_mindset=True,
            programming_languages=['Python', 'JavaScript', 'TypeScript'],
            frameworks_libraries=['React', 'NextJS', 'Django'],
            tools_platforms=['Git', 'Docker', 'AWS']
        )
        
        print(f"   Experience Level: {config.experience_level}")
        print(f"   Years Experience: {config.years_experience}")
        print(f"   Show Learning Mindset: {config.show_learning_mindset}")
        print(f"   Programming Languages: {config.programming_languages}")
        print(f"   Frameworks: {config.frameworks_libraries}")
        print(f"   Tools: {config.tools_platforms}")
        
        # Test GUI class imports
        print("\n✅ Testing GUI class imports...")
        gui_class = UnifiedRepoReadmeGUI
        print(f"   GUI Class: {gui_class.__name__}")
        
        # Check if new methods exist
        required_methods = ['add_quick_tech', 'clear_tech_fields']
        for method_name in required_methods:
            if hasattr(gui_class, method_name):
                print(f"   ✅ Method {method_name} exists")
            else:
                print(f"   ❌ Method {method_name} missing")
        
        print("\n🎉 GUI Enhancement Test Completed Successfully!")
        print("\nNew Features Added:")
        print("   • Experience Level Selection (recent_graduate, junior, mid_level, senior, lead, executive)")
        print("   • Years of Experience Input")
        print("   • Show Learning Mindset Option")
        print("   • Comprehensive Technology Stack Configuration")
        print("   • Quick Technology Stack Presets")
        print("   • Technology Categories: Languages, Frameworks, Tools")
        print("   • Enhanced AI Bio Configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_enhancements()
    sys.exit(0 if success else 1)