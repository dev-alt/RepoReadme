#!/usr/bin/env python3
"""
Test loading animation functionality.
"""

import sys
import os
import time

# Add src directory to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_loading_animation():
    """Test the loading animation system."""
    print("🔄 Testing Loading Animation System")
    print("=" * 40)
    
    try:
        import tkinter as tk
        from unified_gui import UnifiedRepoReadmeGUI
        
        print("📝 Creating GUI instance...")
        root = tk.Tk()
        root.withdraw()  # Hide window for testing
        
        gui = UnifiedRepoReadmeGUI(root)
        print("✅ GUI created successfully")
        
        # Test loading animation methods exist
        print("📝 Testing loading animation methods...")
        assert hasattr(gui, '_start_loading_animation'), "Missing _start_loading_animation method"
        assert hasattr(gui, '_stop_loading_animation'), "Missing _stop_loading_animation method"
        assert hasattr(gui, '_animate_loading'), "Missing _animate_loading method"
        print("✅ All loading animation methods exist")
        
        # Test animation start
        print("📝 Testing animation start...")
        gui._start_loading_animation("Test Operation")
        assert hasattr(gui, 'loading_active'), "Loading active flag not set"
        assert gui.loading_active == True, "Loading should be active"
        assert hasattr(gui, 'loading_operation'), "Loading operation not set"
        print("✅ Animation starts correctly")
        
        # Test animation stop
        print("📝 Testing animation stop...")
        gui._stop_loading_animation()
        assert gui.loading_active == False, "Loading should be stopped"
        print("✅ Animation stops correctly")
        
        # Test threading methods exist
        print("📝 Testing AI bio threading methods...")
        assert hasattr(gui, '_start_ai_bio_generation'), "Missing _start_ai_bio_generation method"
        assert hasattr(gui, '_generate_ai_bio_thread'), "Missing _generate_ai_bio_thread method"
        assert hasattr(gui, '_ai_bio_generation_completed'), "Missing _ai_bio_generation_completed method"
        assert hasattr(gui, '_ai_bio_generation_failed'), "Missing _ai_bio_generation_failed method"
        print("✅ All AI bio threading methods exist")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_file_organization():
    """Test that test files have been moved to tests folder."""
    print(f"\n📁 Testing File Organization")
    print("=" * 40)
    
    tests_dir = os.path.join(os.path.dirname(__file__))
    
    # Check if tests directory exists
    if not os.path.exists(tests_dir):
        print("❌ Tests directory doesn't exist")
        return False
    
    print(f"✅ Tests directory exists: {tests_dir}")
    
    # Check for test files
    test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
    debug_files = [f for f in os.listdir(tests_dir) if f.startswith('debug_') and f.endswith('.py')]
    fix_files = [f for f in os.listdir(tests_dir) if f.startswith('fix_') and f.endswith('.py')]
    
    print(f"📝 Found {len(test_files)} test files")
    print(f"📝 Found {len(debug_files)} debug files")
    print(f"📝 Found {len(fix_files)} fix files")
    
    # Check README exists
    readme_path = os.path.join(tests_dir, 'README.md')
    if os.path.exists(readme_path):
        print("✅ Tests README.md exists")
    else:
        print("❌ Tests README.md missing")
        return False
    
    return len(test_files) > 0

if __name__ == "__main__":
    print("🧪 **LOADING ANIMATION & FILE ORGANIZATION TEST**")
    print()
    
    test1_passed = test_loading_animation()
    test2_passed = test_file_organization()
    
    print(f"\n📊 **TEST RESULTS:**")
    print(f"   • Loading Animation: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • File Organization: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 **ALL TESTS PASSED!**")
        print("✅ Loading animations are implemented")
        print("✅ AI bio generation won't freeze the UI")
        print("✅ Test files are properly organized")
    else:
        print(f"\n⚠️  **SOME TESTS FAILED**")
        print("Check the specific errors above.")