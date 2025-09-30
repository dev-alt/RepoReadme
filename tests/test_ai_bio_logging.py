#!/usr/bin/env python3
"""
Test script to verify AI bio logging methods work correctly.
"""

import sys
import os
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ai_bio_logging():
    """Test that AI bio logging methods exist and work."""
    print("🤖 Testing AI Bio Logging Methods")
    print("=" * 40)
    
    try:
        # Import the GUI class
        from src.unified_gui import UnifiedRepoReadmeGUI
        import tkinter as tk
        
        print("📝 Creating test GUI instance...")
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        gui = UnifiedRepoReadmeGUI(root)
        print("✅ GUI instance created successfully")
        
        # Test that the logger exists
        print("📝 Testing logger exists...")
        assert hasattr(gui, 'logger'), "GUI should have logger attribute"
        print("✅ Logger attribute exists")
        
        # Test that logger has info method
        print("📝 Testing logger.info exists...")
        assert hasattr(gui.logger, 'info'), "Logger should have info method"
        print("✅ Logger.info method exists")
        
        # Test logging
        print("📝 Testing actual logging...")
        gui.logger.info("✅ Test log message from AI bio functionality")
        print("✅ Logging works correctly")
        
        # Cleanup
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_method_removal():
    """Test that log_message method is not present."""
    print(f"\n🔍 Testing log_message Method Removal")
    print("=" * 40)
    
    try:
        from src.unified_gui import UnifiedRepoReadmeGUI
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        gui = UnifiedRepoReadmeGUI(root)
        
        # Test that log_message method doesn't exist
        has_log_message = hasattr(gui, 'log_message')
        print(f"📝 log_message method exists: {'❌ YES (should be NO)' if has_log_message else '✅ NO (correct)'}")
        
        root.destroy()
        
        return not has_log_message  # Success if method doesn't exist
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 **AI BIO LOGGING FIX VERIFICATION**")
    print()
    
    test1_passed = test_ai_bio_logging()
    test2_passed = test_method_removal()
    
    print(f"\n📊 **TEST RESULTS:**")
    print(f"   • Logger functionality: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   • log_message removal: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 **ALL TESTS PASSED!**")
        print("The AI bio save and export functions should now work correctly!")
        print("No more 'object has no attribute log_message' errors.")
    else:
        print(f"\n⚠️  **SOME TESTS FAILED**")
        print("There may still be issues with the AI bio logging.")