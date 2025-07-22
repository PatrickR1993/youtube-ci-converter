#!/usr/bin/env python3
"""
YouTube video downloader module
Handles downloading and converting YouTube videos to MP3 format.
"""

import sys
import time
import threading
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp is required but not installed.")
    print("Please install it using: pip install yt-dlp")
    sys.exit(1)

from progress_tracker import DownloadProgressHook
from utils import sanitize_filename


def simulate_conversion_progress(progress_hook, stop_event):
    """Simulate conversion progress while the actual conversion is happening."""
    if not progress_hook or not progress_hook.conversion_started:
        return
    
    # Simulate gradual progress from 80% to 95% over conversion time
    current_progress = 80
    increment = 1
    
    while not stop_event.is_set() and current_progress < 95:
        time.sleep(0.5)  # Update every 0.5 seconds
        current_progress += increment
        if progress_hook.progress_tracker:
            progress_hook.progress_tracker.update_step('download', current_progress, "Converting to MP3...")


def download_youtube_video(url, output_dir, progress_tracker=None):
    """
    Download YouTube video and convert to MP3.
    
    Args:
        url (str): YouTube video URL
        output_dir (Path): Directory to save the MP3 file
        progress_tracker (UnifiedProgressTracker): Progress tracker instance
        
    Returns:
        tuple: (Path to downloaded MP3 file, video title) if successful, (None, None) otherwise
    """
    try:
        # First, extract video info to get the title
        info_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            video_info = ydl.extract_info(url, download=False)
            video_title = video_info.get('title', 'Unknown Video')
        
        # Sanitize the video title for use as folder name
        sanitized_title = sanitize_filename(video_title)
        
        # Create video-specific directory
        video_output_dir = output_dir / sanitized_title
        video_output_dir.mkdir(exist_ok=True)
        
        # Get file count before download to identify the new file
        existing_files = set(video_output_dir.glob("*.mp3"))
        
        # Create progress hook if tracker provided
        progress_hook = None
        if progress_tracker:
            progress_hook = DownloadProgressHook(progress_tracker)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(video_output_dir / '%(title)s.%(ext)s'),
            'noplaylist': True,  # Only download single video, not playlist
            'quiet': True,       # Minimize yt-dlp output
        }
        
        # Add progress hook if available
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
        
        # Set up conversion progress simulation
        stop_conversion_simulation = threading.Event()
        conversion_thread = None
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download and convert
                ydl.download([url])
                
                # Start conversion progress simulation after download
                if progress_hook and progress_hook.conversion_started:
                    conversion_thread = threading.Thread(
                        target=simulate_conversion_progress, 
                        args=(progress_hook, stop_conversion_simulation)
                    )
                    conversion_thread.daemon = True
                    conversion_thread.start()
                    
                    # Give conversion some time to complete
                    time.sleep(1.0)
        
        finally:
            # Stop conversion simulation
            stop_conversion_simulation.set()
            if conversion_thread and conversion_thread.is_alive():
                conversion_thread.join(timeout=1.0)
        
        # Mark conversion as complete
        if progress_hook:
            progress_hook.finish_conversion()
        
        # Find the new file that was created
        current_files = set(video_output_dir.glob("*.mp3"))
        new_files = current_files - existing_files
        
        if new_files:
            # Return the newly created file and video title
            return list(new_files)[0], video_title
        else:
            # Fallback: use the most recently created file
            mp3_files = list(video_output_dir.glob("*.mp3"))
            if mp3_files:
                return max(mp3_files, key=lambda f: f.stat().st_ctime), video_title
            else:
                return None, None
        
    except yt_dlp.DownloadError as e:
        if progress_tracker:
            progress_tracker.finish("Download failed")
        print(f"❌ Download error: {e}")
        return None, None
    except Exception as e:
        if progress_tracker:
            progress_tracker.finish("Download failed")
        print(f"❌ Unexpected error: {e}")
        return None, None
