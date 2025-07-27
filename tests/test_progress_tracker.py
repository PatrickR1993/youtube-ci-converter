#!/usr/bin/env python3
"""
Unit tests for progress_tracker module
Tests progress tracking functionality and download hooks.
"""

import unittest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import progress_tracker


class TestUnifiedProgressTracker(unittest.TestCase):
    """Test cases for UnifiedProgressTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = progress_tracker.UnifiedProgressTracker()

    def test_initialization(self):
        """Test tracker initialization."""
        self.assertIsNone(self.tracker.start_time)
        self.assertIsNone(self.tracker.current_step)

    @patch('sys.stdout', new_callable=StringIO)
    def test_start(self, mock_stdout):
        """Test starting the tracker."""
        self.tracker.start("Test Process")
        
        # Check that start_time is set
        self.assertIsNotNone(self.tracker.start_time)
        
        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("🔄 Test Process", output)
        self.assertIn("===============", output)  # Should have multiple equal signs

    @patch('sys.stdout', new_callable=StringIO)
    def test_update_step(self, mock_stdout):
        """Test step updates."""
        self.tracker.start("Test Process")
        
        # Test first update
        self.tracker.update_step('download', 50, 'Downloading video...')
        self.assertEqual(self.tracker.current_step, ('download', 'Downloading video...'))
        
        # Check output
        output = mock_stdout.getvalue()
        self.assertIn("📥", output)  # download icon
        self.assertIn("Downloading video...", output)
        
        # Test that same step doesn't repeat
        mock_stdout.seek(0)
        mock_stdout.truncate(0)
        self.tracker.update_step('download', 60, 'Downloading video...')
        
        # Should be no new output since it's the same status
        output = mock_stdout.getvalue()
        self.assertEqual(output, "")

    @patch('sys.stdout', new_callable=StringIO)
    def test_step_icons(self, mock_stdout):
        """Test that correct icons are used for different steps."""
        self.tracker.start("Test Process")
        
        # Test download icon
        self.tracker.update_step('download', 50, 'Download status')
        output = mock_stdout.getvalue()
        self.assertIn("📥", output)
        
        # Test translation icon
        mock_stdout.seek(0)
        mock_stdout.truncate(0)
        self.tracker.update_step('translation', 50, 'Translation status')
        output = mock_stdout.getvalue()
        self.assertIn("🎌", output)
        
        # Test audio generation icon
        mock_stdout.seek(0)
        mock_stdout.truncate(0)
        self.tracker.update_step('audio_gen', 50, 'Audio status')
        output = mock_stdout.getvalue()
        self.assertIn("🎵", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_finish(self, mock_stdout):
        """Test finishing the tracker."""
        self.tracker.start("Test Process")
        time.sleep(0.1)  # Small delay to test elapsed time
        self.tracker.finish("Test Complete")
        
        output = mock_stdout.getvalue()
        self.assertIn("✅ Test Complete", output)
        self.assertIn("completed in", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_finish_without_start(self, mock_stdout):
        """Test finishing without starting."""
        self.tracker.finish("Test Complete")
        
        output = mock_stdout.getvalue()
        self.assertIn("✅ Test Complete", output)
        self.assertNotIn("completed in", output)


class TestDownloadProgressHook(unittest.TestCase):
    """Test cases for DownloadProgressHook class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = Mock()
        self.hook = progress_tracker.DownloadProgressHook(self.tracker)

    def test_initialization(self):
        """Test hook initialization."""
        self.assertEqual(self.hook.progress_tracker, self.tracker)
        self.assertFalse(self.hook.conversion_started)
        self.assertFalse(self.hook.download_completed)
        self.assertEqual(self.hook.last_notification_time, 0)

    def test_downloading_status(self):
        """Test downloading status updates."""
        # Set the hook's initial time to allow the update
        self.hook.last_notification_time = 0
        
        # Mock download progress data
        d = {
            'status': 'downloading',
            'downloaded_bytes': 5000000,  # 5MB
            'total_bytes': 10000000,      # 10MB
        }
        
        # Call the hook (should update since enough time has passed)
        self.hook(d)
        
        # Should call update_step with calculated percentage
        self.tracker.update_step.assert_called()
        call_args = self.tracker.update_step.call_args
        
        self.assertEqual(call_args[0][0], 'download')  # step name
        self.assertEqual(call_args[0][1], 50.0)        # percentage
        self.assertIn('50%', call_args[0][2])          # status message

    def test_downloading_throttling(self):
        """Test that download updates are throttled."""
        d = {
            'status': 'downloading',
            'downloaded_bytes': 1000000,
            'total_bytes': 10000000,
        }
        
        # First call should work (enough time has passed)
        import time
        current_time = time.time()
        self.hook.last_notification_time = current_time - 6  # 6 seconds ago
        
        self.hook(d)
        self.tracker.update_step.assert_called()
        
        # Second call immediately after should be throttled
        self.tracker.reset_mock()
        self.hook(d)  # last_notification_time was just updated
        self.tracker.update_step.assert_not_called()

    def test_finished_status(self):
        """Test download finished status."""
        d = {'status': 'finished'}
        
        self.hook(d)
        
        # Should update to conversion status
        self.tracker.update_step.assert_called_once_with(
            'download', 90, 'Converting to MP3...'
        )
        self.assertTrue(self.hook.conversion_started)
        self.assertTrue(self.hook.download_completed)

    def test_finish_conversion(self):
        """Test finish_conversion method."""
        self.hook.finish_conversion()
        
        self.tracker.update_step.assert_called_once_with(
            'download', 100, 'Download and conversion complete'
        )

    def test_multiple_finished_calls(self):
        """Test that multiple finished calls don't duplicate messages."""
        d = {'status': 'finished'}
        
        # First call
        self.hook(d)
        self.tracker.update_step.assert_called_once()
        
        # Second call should be ignored
        self.tracker.reset_mock()
        self.hook(d)
        self.tracker.update_step.assert_not_called()


if __name__ == '__main__':
    unittest.main()
