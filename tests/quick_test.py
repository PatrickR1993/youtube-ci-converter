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
        self.assertEqual(len(tracker.step_weights), 3)
        self.assertIn('download', tracker.step_weights)
        self.assertIn('translation', tracker.step_weights)
        self.assertIn('audio_gen', tracker.step_weights)
        
        # Test that weights sum to 100
        total_weights = sum(tracker.step_weights.values())
        self.assertEqual(total_weights, 100)
        
        # Test step progress initialization
        self.assertEqual(len(tracker.step_progress), 3)
        for step in tracker.step_progress:
            self.assertEqual(tracker.step_progress[step], 0)


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
