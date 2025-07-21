#!/usr/bin/env python3
"""
YouTube to MP3 Converter CLI Tool
A simple command-line tool to convert YouTube videos to MP3 audio files.
"""

import os
import sys
import re
import argparse
from pathlib import Path
import subprocess
try:
    import yt_dlp
    from tqdm import tqdm
except ImportError:
    print("Error: yt-dlp is required but not installed.")
    print("Please install it using: pip install yt-dlp")
    sys.exit(1)


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


def get_output_directory():
    """
    Get or create the output directory for downloaded MP3 files.
    
    Returns:
        Path: Path object for the output directory
    """
    # Create downloads directory in the same folder as the script
    script_dir = Path(__file__).parent
    output_dir = script_dir / "downloads"
    output_dir.mkdir(exist_ok=True)
    return output_dir


class UnifiedProgressTracker:
    """Unified progress bar for the entire YouTube to MP3 + Translation operation."""
    
    def __init__(self):
        self.pbar = None
        self.current_step = 0
        self.total_steps = 3  # Download, Translation, Audio Generation
        self.step_weights = {
            'download': 30,      # 30% of total progress
            'translation': 40,   # 40% of total progress
            'audio_gen': 30      # 30% of total progress
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
    """Simple download progress hook for yt-dlp that works with UnifiedProgressTracker."""
    
    def __init__(self, progress_tracker):
        self.progress_tracker = progress_tracker
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            
            if total_bytes and downloaded_bytes:
                progress = (downloaded_bytes / total_bytes) * 100
                self.progress_tracker.update_step('download', progress, "Downloading video")
                
        elif d['status'] == 'finished':
            self.progress_tracker.update_step('download', 100, "Converting to MP3")


def download_youtube_video(url, output_dir, progress_tracker=None):
    """
    Download YouTube video and convert to MP3.
    
    Args:
        url (str): YouTube video URL
        output_dir (Path): Directory to save the MP3 file
        progress_tracker (UnifiedProgressTracker): Progress tracker instance
        
    Returns:
        Path: Path to downloaded MP3 file if successful, None otherwise
    """
    try:
        # Get file count before download to identify the new file
        existing_files = set(output_dir.glob("*.mp3"))
        
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
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'noplaylist': True,  # Only download single video, not playlist
            'quiet': True,       # Minimize yt-dlp output
        }
        
        # Add progress hook if available
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and convert
            ydl.download([url])
        
        # Find the new file that was created
        current_files = set(output_dir.glob("*.mp3"))
        new_files = current_files - existing_files
        
        if new_files:
            # Return the newly created file
            return list(new_files)[0]
        else:
            # Fallback: use the most recently created file
            mp3_files = list(output_dir.glob("*.mp3"))
            if mp3_files:
                return max(mp3_files, key=lambda f: f.stat().st_ctime)
            else:
                return None
        
    except yt_dlp.DownloadError as e:
        if progress_tracker:
            progress_tracker.finish("Download failed")
        print(f"❌ Download error: {e}")
        return None
    except Exception as e:
        if progress_tracker:
            progress_tracker.finish("Download failed")
        print(f"❌ Unexpected error: {e}")
        return None


def run_translation_with_progress(translator, input_file, output_dir, progress_tracker):
    """Run audio translation with progress tracking."""
    try:
        # Extract sentences with Whisper (0-30% of translation step)
        sentences = translator.extract_sentences_whisper(input_file, progress_tracker)
        
        if not sentences:
            return False
        
        # Translate sentences with GPT (30-100% of translation step)  
        translated_sentences = translator.translate_sentences(sentences, progress_tracker)
        progress_tracker.update_step('translation', 100, "Translation complete")
        
        if not translated_sentences:
            return False
        
        # Start audio generation phase
        progress_tracker.update_step('audio_gen', 0, "Generating bilingual audio")
        
        # Create bilingual audio with progress updates
        output_file = translator.create_bilingual_audio_with_progress(
            input_file, translated_sentences, output_dir, progress_tracker
        )
        
        if output_file:
            progress_tracker.update_step('audio_gen', 100, "Audio generation complete")
            return output_file  # Return the actual output file path
        else:
            return None
            
    except Exception as e:
        print(f"Translation error: {e}")
        return None


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


def main():
    """Main function to run the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Download YouTube videos and translate Japanese audio to English with bilingual output",
        epilog="Examples:\n"
               "  python youtube_ci_converter.py --url https://youtu.be/VIDEO_ID\n"
               "  python youtube_ci_converter.py --file podcast.mp3"
    )
    parser.add_argument(
        '--url', '-u',
        help='YouTube URL to convert'
    )
    parser.add_argument(
        '--file', '-f',
        help='Existing MP3 file to process (alternative to --url)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output directory for MP3 files (default: ./downloads/)'
    )
    parser.add_argument(
        '--openai-key',
        help='OpenAI API key for translation and natural TTS (required)'
    )
    
    args = parser.parse_args()
    
    # Validate that either --url or --file is provided, but not both
    if not args.url and not args.file:
        parser.error("Either --url or --file must be provided")
    if args.url and args.file:
        parser.error("Cannot use both --url and --file at the same time")
    
    print("🎌 YouTube Japanese Audio Translator")
    print("=" * 45)
    
    # Check for FFmpeg dependency
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Warning: FFmpeg not found. Required for audio conversion.")
        print("   Install: https://ffmpeg.org/download.html")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    # Get output directory
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = get_output_directory()
    
    # Initialize unified progress tracker
    progress_tracker = UnifiedProgressTracker()
    
    # Handle input: either YouTube URL or existing file
    if args.file:
        # Process existing file
        input_file = Path(args.file)
        if not input_file.exists():
            print(f"❌ File not found: {input_file}")
            sys.exit(1)
        if not input_file.suffix.lower() == '.mp3':
            print(f"❌ File must be an MP3: {input_file}")
            sys.exit(1)
        
        print(f"📁 Processing: {input_file.name}")
        progress_tracker.start("Processing audio file")
        progress_tracker.update_step('download', 100, "File ready")  # Skip download step
        success = True
        
    else:
        # Download from YouTube URL
        if not is_valid_youtube_url(args.url):
            print("❌ Error: Invalid YouTube URL provided.")
            sys.exit(1)
        url = args.url
        
        # Start progress tracking
        progress_tracker.start("YouTube to MP3 + Translation")
        
        # Download and convert
        downloaded_file = download_youtube_video(url, output_dir, progress_tracker)
        
        if downloaded_file:
            input_file = downloaded_file
            success = True
        else:
            progress_tracker.finish("❌ Download failed")
            print("❌ Could not download or find MP3 file")
            sys.exit(1)
    
    # Always translate after successful download/file validation
    if success:
        try:
            # Import and run audio translator with progress tracking
            from audio_translator import AudioTranslator
            
            # Initialize translator
            api_key = args.openai_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                progress_tracker.finish("❌ Missing API key")
                print("❌ OpenAI API key required. Set OPENAI_API_KEY env var or use --openai-key")
                sys.exit(1)
            
            translator = AudioTranslator(api_key)
            
            # Create output directory
            output_dir_path = Path("output")
            output_dir_path.mkdir(exist_ok=True)
            
            # Run translation with progress tracking
            output_file = run_translation_with_progress(translator, input_file, output_dir_path, progress_tracker)
            
            if output_file:
                progress_tracker.finish("✅ Complete")
                
                # Show output file information after progress bar completes
                transcript_file = output_dir_path / f"{input_file.stem}_transcript.json"
                print(f"\n🎉 Translation completed successfully!")
                print(f"📄 Transcript: {transcript_file}")
                print(f"🎵 Bilingual audio: {output_file}")
            else:
                progress_tracker.finish("❌ Translation failed")
                sys.exit(1)
                
        except ImportError:
            progress_tracker.finish("❌ Translation module missing")
            print("❌ Could not import audio_translator module")
            sys.exit(1)
        except Exception as e:
            progress_tracker.finish("❌ Translation failed")
            print(f"❌ Translation error: {e}")
            sys.exit(1)
    else:
        print("\n❌ Processing failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
