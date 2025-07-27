#!/usr/bin/env python3
"""
Integration tests for ytcc functionality
Tests the integration between different modules and core functionality.
"""

import unittest
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestYtccIntegration(unittest.TestCase):
    """Integration tests for ytcc CLI tool functionality."""

    def test_ytcc_help_command(self):
        """Test that ytcc --help works correctly."""
        try:
            result = subprocess.run(
                [sys.executable, str(project_root / "ytcc"), "--help"],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("YouTube CI Converter", result.stdout)
            self.assertIn("--url", result.stdout)
            self.assertIn("--file", result.stdout)
        except Exception as e:
            self.fail(f"Failed to run ytcc --help: {e}")

    def test_setup_module_availability(self):
        """Test that setup module is available and has required functions."""
        try:
            import setup
            self.assertTrue(hasattr(setup, 'run_setup'))
            self.assertTrue(callable(setup.run_setup))
        except ImportError as e:
            self.fail(f"Failed to import setup module: {e}")

    def test_core_modules_import(self):
        """Test that all core modules can be imported."""
        modules_to_test = [
            'utils',
            'progress_tracker', 
            'youtube_downloader',
            'translator_interface',
            'audio_translator'
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")

    def test_utils_functions(self):
        """Test that utils module has required functions."""
        try:
            import utils
            required_functions = [
                'sanitize_filename',
                'is_valid_youtube_url',
                'get_output_directory'
            ]
            for func_name in required_functions:
                with self.subTest(function=func_name):
                    self.assertTrue(hasattr(utils, func_name))
                    self.assertTrue(callable(getattr(utils, func_name)))
        except ImportError as e:
            self.fail(f"Failed to import utils module: {e}")

    def test_progress_tracker_functionality(self):
        """Test that progress tracker can be instantiated and used."""
        try:
            import progress_tracker
            tracker = progress_tracker.UnifiedProgressTracker()
            self.assertIsNotNone(tracker)
            
            # Test basic progress tracking methods
            self.assertTrue(hasattr(tracker, 'start'))
            self.assertTrue(hasattr(tracker, 'update_step'))
            self.assertTrue(hasattr(tracker, 'finish'))
        except ImportError as e:
            self.fail(f"Failed to import progress_tracker module: {e}")

    def test_youtube_url_validation(self):
        """Test YouTube URL validation functionality."""
        try:
            import utils
            
            # Test valid URLs
            valid_urls = [
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'https://youtu.be/dQw4w9WgXcQ',
                'https://youtube.com/watch?v=dQw4w9WgXcQ'
            ]
            
            for url in valid_urls:
                with self.subTest(url=url):
                    self.assertTrue(utils.is_valid_youtube_url(url))
            
            # Test invalid URLs
            invalid_urls = [
                'https://example.com',
                'not_a_url',
                'https://vimeo.com/12345'
            ]
            
            for url in invalid_urls:
                with self.subTest(url=url):
                    self.assertFalse(utils.is_valid_youtube_url(url))
                    
        except ImportError as e:
            self.fail(f"Failed to import utils module: {e}")

    def test_translator_interface_availability(self):
        """Test that translator interface is available."""
        try:
            import translator_interface
            self.assertTrue(hasattr(translator_interface, 'get_audio_translator_class'))
            self.assertTrue(hasattr(translator_interface, 'run_translation_with_progress'))
        except ImportError as e:
            self.fail(f"Failed to import translator_interface module: {e}")


def run_integration_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestYtccIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    unittest.main()
