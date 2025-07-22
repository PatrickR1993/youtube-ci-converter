#!/usr/bin/env python3
"""
Unit tests for progress_tracker module
Tests progress tracking functionality and download hooks.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

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
        self.assertIsNone(self.tracker.pbar)
        self.assertEqual(self.tracker.current_step, 0)
        self.assertEqual(self.tracker.total_steps, 3)
        
        # Check step weights
        expected_weights = {
            'download': 10,
            'translation': 40,
            'audio_gen': 50
        }
        self.assertEqual(self.tracker.step_weights, expected_weights)
        
        # Check initial progress
        expected_progress = {
            'download': 0,
            'translation': 0,
            'audio_gen': 0
        }
        self.assertEqual(self.tracker.step_progress, expected_progress)

    @patch('progress_tracker.tqdm')
    def test_start(self, mock_tqdm):
        """Test starting the progress bar."""
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        
        self.tracker.start("Test Description")
        
        mock_tqdm.assert_called_once_with(
            total=100,
            desc="Test Description",
            unit='%',
            bar_format='{l_bar}{bar}| {n:.0f}% [{elapsed}<{remaining}]'
        )
        self.assertEqual(self.tracker.pbar, mock_pbar)

    def test_update_step_without_pbar(self):
        """Test updating step when no progress bar is active."""
        # Should not raise an exception and should not update progress
        # since the implementation requires pbar to be active
        self.tracker.update_step('download', 50)
        # Progress should remain 0 since pbar is None
        self.assertEqual(self.tracker.step_progress['download'], 0)

    @patch('progress_tracker.tqdm')
    def test_update_step_with_pbar(self, mock_tqdm):
        """Test updating step with active progress bar."""
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        
        self.tracker.start("Test")
        self.tracker.update_step('download', 50, "Downloading")
        
        # Check that progress was updated
        self.assertEqual(self.tracker.step_progress['download'], 50)
        
        # Check total progress calculation (50% of 10% = 5%)
        expected_total = 5.0
        self.assertEqual(mock_pbar.n, expected_total)
        mock_pbar.set_description.assert_called_with("Downloading")
        mock_pbar.refresh.assert_called()

    def test_update_step_progress_bounds(self):
        """Test that progress is bounded between 0 and 100."""
        # Start the tracker so pbar is not None
        self.tracker.start("Test")
        
        self.tracker.update_step('download', -10)
        self.assertEqual(self.tracker.step_progress['download'], 0)
        
        self.tracker.update_step('download', 150)
        self.assertEqual(self.tracker.step_progress['download'], 100)
        
        self.tracker.finish()

    @patch('progress_tracker.tqdm')
    def test_total_progress_calculation(self, mock_tqdm):
        """Test total progress calculation with multiple steps."""
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        
        self.tracker.start("Test")
        
        # Set progress for all steps
        self.tracker.update_step('download', 100)      # 10% of total
        self.tracker.update_step('translation', 50)    # 20% of total (50% of 40%)
        self.tracker.update_step('audio_gen', 25)      # 12.5% of total (25% of 50%)
        
        # Total should be 10 + 20 + 12.5 = 42.5%
        expected_total = 42.5
        self.assertEqual(mock_pbar.n, expected_total)

    @patch('progress_tracker.tqdm')
    def test_finish(self, mock_tqdm):
        """Test finishing the progress bar."""
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        
        self.tracker.start("Test")
        self.tracker.finish("Complete")
        
        # Check that progress bar was set to 100% and closed
        self.assertEqual(mock_pbar.n, 100)
        mock_pbar.set_description.assert_called_with("Complete")
        mock_pbar.refresh.assert_called()
        mock_pbar.close.assert_called()
        self.assertIsNone(self.tracker.pbar)

    def test_finish_without_pbar(self):
        """Test finishing when no progress bar is active."""
        # Should not raise an exception
        self.tracker.finish("Complete")


class TestDownloadProgressHook(unittest.TestCase):
    """Test cases for DownloadProgressHook class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_tracker = Mock()
        self.hook = progress_tracker.DownloadProgressHook(self.mock_tracker)

    def test_downloading_status(self):
        """Test download progress during downloading."""
        download_data = {
            'status': 'downloading',
            'total_bytes': 1000,
            'downloaded_bytes': 500
        }
        
        self.hook(download_data)
        
        # Should update download progress to 40% (50% * 80% scaling)
        self.mock_tracker.update_step.assert_called_with(
            'download', 40.0, "Downloading video"
        )

    def test_downloading_with_estimate(self):
        """Test download progress with byte estimate."""
        download_data = {
            'status': 'downloading',
            'total_bytes_estimate': 2000,
            'downloaded_bytes': 1000
        }
        
        self.hook(download_data)
        
        # Should use estimate when total_bytes not available (50% * 80% scaling = 40%)
        self.mock_tracker.update_step.assert_called_with(
            'download', 40.0, "Downloading video"
        )

    def test_downloading_without_total(self):
        """Test download progress without total bytes."""
        download_data = {
            'status': 'downloading',
            'downloaded_bytes': 500
        }
        
        self.hook(download_data)
        
        # Should not call update_step when total is unknown
        self.mock_tracker.update_step.assert_not_called()

    def test_finished_status(self):
        """Test download completion."""
        download_data = {
            'status': 'finished'
        }
        
        self.hook(download_data)
        
        # Should set download to 80% and update status
        self.mock_tracker.update_step.assert_called_with(
            'download', 80, "Converting to MP3..."
        )

    def test_other_status(self):
        """Test other download statuses."""
        download_data = {
            'status': 'error'
        }
        
        self.hook(download_data)
        
        # Should not call update_step for unknown status
        self.mock_tracker.update_step.assert_not_called()


if __name__ == "__main__":
    unittest.main()
