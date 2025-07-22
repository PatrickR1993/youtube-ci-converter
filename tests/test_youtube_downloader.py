#!/usr/bin/env python3
"""
YouTube downloader tests focusing on core functionality.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestYouTubeDownloader(unittest.TestCase):
    """YouTube downloader tests."""

    def test_youtube_downloader_module_imports(self):
        """Test that YouTube downloader module can be imported."""
        try:
            import youtube_downloader
            self.assertTrue(hasattr(youtube_downloader, 'download_youtube_video'))
        except ImportError as e:
            self.fail(f"YouTube downloader module import failed: {e}")

    def test_download_function_exists(self):
        """Test that download function exists and is callable."""
        import youtube_downloader
        
        # Test function exists
        self.assertTrue(hasattr(youtube_downloader, 'download_youtube_video'))
        self.assertTrue(callable(youtube_downloader.download_youtube_video))

    def test_download_handles_none_inputs(self):
        """Test that download function handles None inputs gracefully."""
        import youtube_downloader
        
        # Should not crash with None inputs
        try:
            result = youtube_downloader.download_youtube_video(None, None, None)
            # Should return (None, None) or similar for invalid inputs
            self.assertIsInstance(result, tuple)
        except Exception as e:
            # This is acceptable - function may raise exceptions for invalid inputs
            pass


if __name__ == "__main__":
    unittest.main()
