#!/usr/bin/env python3
"""
Quick functional test to verify core functionality works.
This is a simple test that doesn't require complex mocking.
"""

import sys
import os
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import utils
from progress_tracker import UnifiedProgressTracker


class QuickFunctionalTest(unittest.TestCase):
    """Quick tests for core functionality."""
    
    def test_youtube_url_validation(self):
        """Test YouTube URL validation works."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        invalid_urls = [
            "https://www.google.com",
            "not-a-url",
            "",
            "https://www.youtube.com"  # Missing video ID
        ]
        
        for url in valid_urls:
            self.assertTrue(utils.is_valid_youtube_url(url), f"Should be valid: {url}")
            
        for url in invalid_urls:
            self.assertFalse(utils.is_valid_youtube_url(url), f"Should be invalid: {url}")
    
    def test_filename_sanitization(self):
        """Test filename sanitization."""
        test_cases = [
            ("Normal File", "Normal File"),
            ("File<>:\"/\\|?*Name", "File_________Name"),
            ("   Spaces   ", "Spaces"),
            ("File...Name", "File...Name"),
        ]
        
        for input_name, expected in test_cases:
            result = utils.sanitize_filename(input_name)
            self.assertEqual(result, expected, f"Input: '{input_name}' -> Expected: '{expected}', Got: '{result}'")
    
    def test_progress_tracker_basic(self):
        """Test basic progress tracker functionality."""
        tracker = UnifiedProgressTracker()
        
        # Test initialization
        self.assertIsNone(tracker.start_time)
        self.assertIsNone(tracker.current_step)
        
        # Test start functionality
        tracker.start("Test Process")
        self.assertIsNotNone(tracker.start_time)
        
        # Test step update functionality
        tracker.update_step('download', 50, 'Downloading video...')
        self.assertEqual(tracker.current_step, ('download', 'Downloading video...'))
        
        # Test finish functionality
        tracker.finish("Test Complete")
        # Should not raise any exceptions


def run_quick_test():
    """Run the quick test suite."""
    print("🧪 YouTube CI Converter - Quick Functional Test")
    print("=" * 50)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(QuickFunctionalTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All quick tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed!")
        return False


if __name__ == "__main__":
    success = run_quick_test()
    sys.exit(0 if success else 1)
