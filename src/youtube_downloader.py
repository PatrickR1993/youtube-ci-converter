#!/usr/bin/env python3
"""
YouTube video downloader module
Handles downloading and converting YouTube videos to MP3 format.
"""

import sys
import time
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp is required but not installed.")
    print("Please install it using: pip install yt-dlp")
    sys.exit(1)

from progress_tracker import DownloadProgressHook
from utils import sanitize_filename


def download_youtube_video(url, output_dir, progress_tracker=None):
    """
    Download YouTube video and convert to MP3.
    
    Args:
        url (str): YouTube video URL
        output_dir (Path): Directory to save the MP3 file
        progress_tracker (UnifiedProgressTracker): Progress tracker instance
        
    Returns:
        tuple: (Path to downloaded MP3 file, video title, channel name) if successful, (None, None, None) otherwise
    """
    try:
        # First, extract video info to get the title and channel
        info_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            video_info = ydl.extract_info(url, download=False)
            video_title = video_info.get('title', 'Unknown Video')
            channel_name = video_info.get('uploader', video_info.get('channel', 'Unknown Channel'))
        
        # Sanitize the channel name and video title for use as folder names
        sanitized_channel = sanitize_filename(channel_name)
        sanitized_title = sanitize_filename(video_title)
        
        # Create channel directory structure: output/channel_name/
        channel_output_dir = output_dir / sanitized_channel
        channel_output_dir.mkdir(exist_ok=True)
        
        # Files go directly in the channel folder
        video_output_dir = channel_output_dir
        
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
        
        # Simple download without complex threading
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and convert
            ydl.download([url])
        
        # Mark conversion as complete
        if progress_hook:
            progress_hook.finish_conversion()
        
        # Find the new file that was created
        current_files = set(video_output_dir.glob("*.mp3"))
        new_files = current_files - existing_files
        
        if new_files:
            # Return the newly created file, video title, and channel name
            return list(new_files)[0], video_title, channel_name
        else:
            # Fallback: use the most recently created file
            mp3_files = list(video_output_dir.glob("*.mp3"))
            if mp3_files:
                return max(mp3_files, key=lambda f: f.stat().st_ctime), video_title, channel_name
            else:
                return None, None, None
        
    except yt_dlp.DownloadError as e:
        if progress_tracker:
            progress_tracker.finish("Download failed")
        print(f"❌ Download error: {e}")
        return None, None, None
    except Exception as e:
        if progress_tracker:
            progress_tracker.finish("Download failed")
        print(f"❌ Unexpected error: {e}")
        return None, None, None
