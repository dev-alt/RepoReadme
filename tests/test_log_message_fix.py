#!/usr/bin/env python3
"""
Simple test to verify log_message errors are fixed.
"""

import sys
import os

def test_log_message_fix():
    """Test that log_message has been replaced with logger.info."""
    print("🔧 Testing log_message Fix")
    print("=" * 30)
    
    # Read the source file and check for log_message
    gui_file = os.path.join(os.path.dirname(__file__), 'src', 'unified_gui.py')
    
    if not os.path.exists(gui_file):
        print(f"❌ File not found: {gui_file}")
        return False
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for log_message calls
    log_message_count = content.count('.log_message(')
    print(f"📝 Found {log_message_count} instances of '.log_message('")
    
    if log_message_count > 0:
        print("❌ Still has log_message calls")
        
        # Show lines with log_message
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '.log_message(' in line:
                print(f"   Line {i}: {line.strip()}")
        
        return False
    else:
        print("✅ No log_message calls found")
    
    # Check for logger.info calls
    logger_info_count = content.count('.logger.info(')
    print(f"📝 Found {logger_info_count} instances of '.logger.info('")
    
    if logger_info_count > 0:
        print("✅ Logger.info calls are being used")
    
    # Check specific lines that were fixed
    ai_bio_save_fixed = "✅ AI bio versions saved to output directory" in content
    ai_bio_export_fixed = "✅ AI bio guide exported to" in content
    
    print(f"📝 AI bio save message fixed: {'✅ YES' if ai_bio_save_fixed else '❌ NO'}")
    print(f"📝 AI bio export message fixed: {'✅ YES' if ai_bio_export_fixed else '❌ NO'}")
    
    return log_message_count == 0 and ai_bio_save_fixed and ai_bio_export_fixed

if __name__ == "__main__":
    success = test_log_message_fix()
    
    if success:
        print(f"\n🎉 **SUCCESS!**")
        print("All log_message calls have been replaced with logger.info!")
        print("The AI bio save and export functions should now work without errors.")
    else:
        print(f"\n❌ **ISSUES DETECTED**")
        print("There may still be log_message calls that need fixing.")