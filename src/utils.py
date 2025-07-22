#!/usr/bin/env python3
"""
Utility functions for YouTube CI Converter
Contains common helper functions used across the application.
"""

import re
from pathlib import Path


def is_valid_youtube_url(url):
    """
    Validate if the provided URL is a valid YouTube URL.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if valid YouTube URL, False otherwise
    """
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
        r'(https?://)?youtu\.be/',
        r'(https?://)?(www\.)?youtube\.com/watch\?v=',
        r'(https?://)?(www\.)?youtube\.com/embed/',
        r'(https?://)?(www\.)?youtube\.com/v/',
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)


def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename (str): The original filename
        
    Returns:
        str: Sanitized filename safe for filesystem use
    """
    # Remove or replace invalid characters for Windows/Unix filesystems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length to avoid filesystem issues
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def get_output_directory():
    """
    Get or create the output directory for processed files.
    
    Returns:
        Path: Path object for the output directory
    """
    # Create output directory in the same folder as the main script
    script_dir = Path(__file__).parent.parent  # Go up from src/ to root
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def prompt_for_url():
    """
    Prompt user for YouTube URL with validation.
    
    Returns:
        str: Valid YouTube URL
    """
    while True:
        url = input("\n🎬 Enter YouTube URL: ").strip()
        
        if not url:
            print("❌ Please enter a URL.")
            continue
            
        if not is_valid_youtube_url(url):
            print("❌ Invalid YouTube URL. Please enter a valid YouTube link.")
            print("   Examples:")
            print("   - https://www.youtube.com/watch?v=VIDEO_ID")
            print("   - https://youtu.be/VIDEO_ID")
            continue
            
        return url
