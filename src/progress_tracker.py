#!/usr/bin/env python3
"""
Simple notification system for YouTube CI Converter
Provides simple text notifications instead of complex progress bars.
"""

import time


class UnifiedProgressTracker:
    """Simple notification system for the entire YouTube CI Converter operation."""
    
    def __init__(self):
        self.start_time = None
        self.current_step = None
        
    def start(self, description="Processing"):
        """Start the process with initial notification."""
        self.start_time = time.time()
        print(f"\n🔄 {description}")
        print("=" * (len(description) + 3))
    
    def update_step(self, step_name: str, progress: float, status: str = None):
        """Show a simple notification for the current step.
        
        Args:
            step_name: 'download', 'translation', or 'audio_gen'
            progress: Progress percentage (0-100) for this step (ignored)
            status: Status message to display
        """
        if status and self.current_step != (step_name, status):
            # Only print if it's a new status to avoid spam
            self.current_step = (step_name, status)
            
            # Add step-specific icons
            icon_map = {
                'download': '📥',
                'translation': '🎌',
                'audio_gen': '🎵'
            }
            icon = icon_map.get(step_name, '🔄')
            
            elapsed = time.time() - self.start_time if self.start_time else 0
            print(f"{icon} [{elapsed:.0f}s] {status}")
    
    def finish(self, message="Complete"):
        """Show completion notification."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n✅ {message} (completed in {elapsed:.0f}s)")
        else:
            print(f"\n✅ {message}")


class DownloadProgressHook:
    """Simple download notifications for yt-dlp that works with UnifiedProgressTracker."""
    
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
        self.conversion_started = False
        self.download_completed = False
        self.last_notification_time = 0
    
    def __call__(self, d):
        import time
        current_time = time.time()
        
        if d['status'] == 'downloading':
            # Only update every 5 seconds to avoid spam
            if current_time - self.last_notification_time < 5:
                return
                
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            
            if total_bytes and downloaded_bytes:
                percentage = (downloaded_bytes / total_bytes) * 100
                size_mb = downloaded_bytes / (1024 * 1024)
                total_mb = total_bytes / (1024 * 1024)
                
                self.progress_tracker.update_step('download', percentage, 
                    f"Downloading: {percentage:.0f}% ({size_mb:.1f}MB/{total_mb:.1f}MB)")
                self.last_notification_time = current_time
                
        elif d['status'] == 'finished' and not self.download_completed:
            # Download complete, now converting
            self.progress_tracker.update_step('download', 90, "Converting to MP3...")
            self.conversion_started = True
            self.download_completed = True
            
    def finish_conversion(self):
        """Call this when conversion is definitely complete."""
        if self.progress_tracker:
            self.progress_tracker.update_step('download', 100, "Download and conversion complete")
