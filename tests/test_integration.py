#!/usr/bin/env python3
"""
Integration tests for main functionality
Tests the integration between different modules and main.py functionality.
"""

import unittest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestMainIntegration(unittest.TestCase):
    """Integration tests for main.py functionality."""

    def test_main_module_imports(self):
        """Test that main.py can be imported successfully."""
        try:
            import main
            self.assertTrue(hasattr(main, 'argparse'))
        except ImportError as e:
            self.fail(f"Failed to import main module: {e}")

    def test_argument_parser_creation(self):
        """Test basic argument parser functionality."""
        import main
        
        # Test that we can create a parser
        parser = main.argparse.ArgumentParser(description="Test parser")
        parser.add_argument('--url', help='Test URL')
        parser.add_argument('--file', help='Test file')
        
        # Test parsing valid arguments
        args = parser.parse_args(['--url', 'https://test.com'])
        self.assertEqual(args.url, 'https://test.com')

    def test_setup_module_availability(self):
        """Test that setup module is available and has required functions."""
        try:
            import setup
            self.assertTrue(hasattr(setup, 'run_setup'))
            self.assertTrue(hasattr(setup, 'main'))
        except ImportError:
            self.fail("Setup module should be importable")

    def test_all_required_modules_import(self):
        """Test that all required modules can be imported."""
        modules_to_test = ['utils', 'progress_tracker', 'youtube_downloader', 'translator_interface', 'setup']
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_basic_utils_functionality(self):
        """Test basic utils functions work."""
        import utils
        
        # Test URL validation
        self.assertTrue(utils.is_valid_youtube_url("https://www.youtube.com/watch?v=test"))
        self.assertFalse(utils.is_valid_youtube_url("not-a-url"))
        
        # Test filename sanitization
        result = utils.sanitize_filename("Test<>File")
        self.assertIsInstance(result, str)
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)

    def test_progress_tracker_basic_functionality(self):
        """Test basic progress tracker functionality."""
        import progress_tracker
        
        # Test tracker creation
        tracker = progress_tracker.UnifiedProgressTracker()
        self.assertIsInstance(tracker.step_weights, dict)
        self.assertIsInstance(tracker.step_progress, dict)
        
        # Test download hook creation
        hook = progress_tracker.DownloadProgressHook(tracker)
        self.assertIsNotNone(hook)


class TestModuleInteraction(unittest.TestCase):
    """Test interaction between different modules."""

    def test_progress_tracker_with_download_hook(self):
        """Test progress tracker works with download hook."""
        import progress_tracker
        
        tracker = progress_tracker.UnifiedProgressTracker()
        hook = progress_tracker.DownloadProgressHook(tracker)
        
        # Test with basic download data - should not raise exceptions
        test_data = {'status': 'downloading', 'downloaded_bytes': 100, 'total_bytes': 1000}
        try:
            hook(test_data)
        except Exception as e:
            self.fail(f"Download hook should handle basic data without error: {e}")

    def test_utils_and_youtube_downloader_compatibility(self):
        """Test utils functions work with youtube downloader context."""
        import utils
        import youtube_downloader
        
        # Test that utils functions return expected types
        output_dir = utils.get_output_directory()
        self.assertIsInstance(output_dir, Path)
        
        # Test filename sanitization for video titles
        test_title = "Video: Test (HD)"
        sanitized = utils.sanitize_filename(test_title)
        self.assertIsInstance(sanitized, str)
        self.assertGreater(len(sanitized), 0)

    def test_translator_interface_basic_structure(self):
        """Test translator interface has expected structure."""
        try:
            import translator_interface
            
            # Check that required functions exist
            self.assertTrue(hasattr(translator_interface, 'get_audio_translator_class'))
            self.assertTrue(hasattr(translator_interface, 'run_translation_with_progress'))
            
        except ImportError:
            self.fail("Translator interface should be importable")


if __name__ == "__main__":
    unittest.main()
