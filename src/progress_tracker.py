#!/usr/bin/env python3
"""
Progress tracking module for YouTube CI Converter
Provides unified progress tracking for download, translation, and audio generation phases.
"""

try:
    from tqdm import tqdm
except ImportError:
    print("Error: tqdm is required but not installed.")
    print("Please install it using: pip install tqdm")
    import sys
    sys.exit(1)


class UnifiedProgressTracker:
    """Unified progress bar for the entire YouTube to MP3 + Translation operation."""
    
    def __init__(self):
        self.pbar = None
        self.current_step = 0
        self.total_steps = 3  # Download, Translation, Audio Generation
        self.step_weights = {
            'download': 10,      # 10% of total progress
            'translation': 40,   # 40% of total progress
            'audio_gen': 50      # 50% of total progress
        }
        self.step_progress = {
            'download': 0,
            'translation': 0,
            'audio_gen': 0
        }
    
    def start(self, description="Processing"):
        """Start the unified progress bar."""
        self.pbar = tqdm(
            total=100,
            desc=description,
            unit='%',
            bar_format='{l_bar}{bar}| {n:.0f}% [{elapsed}<{remaining}]'
        )
    
    def update_step(self, step_name: str, progress: float, status: str = None):
        """Update progress for a specific step.
        
        Args:
            step_name: 'download', 'translation', or 'audio_gen'
            progress: Progress percentage (0-100) for this step
            status: Optional status message
        """
        if not self.pbar:
            return
            
        # Update step progress
        self.step_progress[step_name] = min(100, max(0, progress))
        
        # Calculate total progress
        total_progress = (
            (self.step_progress['download'] * self.step_weights['download'] / 100) +
            (self.step_progress['translation'] * self.step_weights['translation'] / 100) +
            (self.step_progress['audio_gen'] * self.step_weights['audio_gen'] / 100)
        )
        
        # Update progress bar
        self.pbar.n = total_progress
        if status:
            self.pbar.set_description(status)
        self.pbar.refresh()
    
    def finish(self, message="Complete"):
        """Complete the progress bar."""
        if self.pbar:
            self.pbar.n = 100
            self.pbar.set_description(message)
            self.pbar.refresh()
            self.pbar.close()
            self.pbar = None


class DownloadProgressHook:
    """Download progress hook for yt-dlp that works with UnifiedProgressTracker."""
    
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
        self.conversion_started = False
        self.download_completed = False
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            
            if total_bytes and downloaded_bytes:
                # Scale download to 80% of the download step (leaving 20% for conversion)
                download_progress = (downloaded_bytes / total_bytes) * 80
                self.progress_tracker.update_step('download', download_progress, "Downloading video")
                
        elif d['status'] == 'finished' and not self.download_completed:
            # Download complete, now converting
            self.progress_tracker.update_step('download', 80, "Converting to MP3...")
            self.conversion_started = True
            self.download_completed = True
            
    def finish_conversion(self):
        """Call this when conversion is definitely complete."""
        if self.progress_tracker:
            self.progress_tracker.update_step('download', 100, "Download complete")
