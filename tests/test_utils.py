#!/usr/bin/env python3
"""
Unit tests for utils module
Tests utility functions like URL validation, filename sanitization, etc.
"""

import unittest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import utils


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def test_is_valid_youtube_url(self):
        """Test YouTube URL validation."""
        # Valid URLs
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "youtube.com/watch?v=dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ",
            "https://youtube-nocookie.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(utils.is_valid_youtube_url(url), f"Should be valid: {url}")
        
        # Invalid URLs
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "not_a_url",
            "",
            "https://facebook.com/video",
            "https://www.youtube.com",  # No video ID
            "youtube"
        ]
        
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(utils.is_valid_youtube_url(url), f"Should be invalid: {url}")

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        test_cases = [
            # (input, expected_output)
            ("Normal Filename", "Normal Filename"),
            ("File<>Name", "File__Name"),
            ('File"Name', "File_Name"),
            ("File/Path\\Name", "File_Path_Name"),
            ("File|Name", "File_Name"),
            ("File?Name", "File_Name"),
            ("File*Name", "File_Name"),
            ("File:Name", "File_Name"),
            ("  File  ", "File"),  # Strip spaces
            (".File.", "File"),    # Strip dots
            ("A" * 120, "A" * 100),  # Length limit
            ("", ""),
            ("ファイル名", "ファイル名"),  # Unicode should be preserved
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input=input_name):
                result = utils.sanitize_filename(input_name)
                self.assertEqual(result, expected)

    def test_get_output_directory(self):
        """Test output directory creation."""
        with patch('utils.Path') as mock_path_class:
            # Mock Path.home() to return a mock home directory
            mock_home = MagicMock()
            mock_path_class.home.return_value = mock_home
            
            # Mock the Downloads directory path
            mock_downloads = MagicMock()
            mock_home.__truediv__.return_value = mock_downloads
            
            # Mock the final output directory
            mock_output_dir = MagicMock()
            mock_downloads.__truediv__.return_value = mock_output_dir
            
            result = utils.get_output_directory()
            
            # Verify the path was constructed correctly
            mock_path_class.home.assert_called_once()
            mock_home.__truediv__.assert_called_once_with("Downloads")
            mock_downloads.__truediv__.assert_called_once_with("YouTube CI Converter")
            mock_output_dir.mkdir.assert_called_once_with(exist_ok=True)
            self.assertEqual(result, mock_output_dir)

    def test_prompt_for_url_valid_input(self):
        """Test URL prompting with valid input."""
        with patch('builtins.input', return_value="https://youtu.be/dQw4w9WgXcQ"):
            result = utils.prompt_for_url()
            self.assertEqual(result, "https://youtu.be/dQw4w9WgXcQ")

    def test_prompt_for_url_invalid_then_valid(self):
        """Test URL prompting with invalid input followed by valid input."""
        inputs = ["", "invalid_url", "https://youtu.be/dQw4w9WgXcQ"]
        with patch('builtins.input', side_effect=inputs):
            result = utils.prompt_for_url()
            self.assertEqual(result, "https://youtu.be/dQw4w9WgXcQ")

    def test_sanitize_filename_edge_cases(self):
        """Test edge cases for filename sanitization."""
        # Test with only invalid characters
        result = utils.sanitize_filename("<>:\"/\\|?*")
        self.assertEqual(result, "_________")  # 9 characters replaced
        
        # Test with only spaces and dots
        result = utils.sanitize_filename("   ...   ")
        self.assertEqual(result, "")
        
        # Test exact length limit
        long_name = "a" * 100
        result = utils.sanitize_filename(long_name)
        self.assertEqual(len(result), 100)
        self.assertEqual(result, long_name)
        
        # Test over length limit
        over_limit = "a" * 101
        result = utils.sanitize_filename(over_limit)
        self.assertEqual(len(result), 100)


if __name__ == "__main__":
    unittest.main()
