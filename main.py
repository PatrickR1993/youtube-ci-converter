#!/usr/bin/env python3
"""
YouTube CI Converter - Main Entry Point
A command-line tool to download YouTube videos and translate Japanese audio to English with bilingual output.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import modules from src
import progress_tracker as pt
import utils
import youtube_downloader
import translator_interface


def check_dependencies():
    """Check for required system dependencies."""
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


def process_existing_file(args, output_dir, progress_tracker):
    """Process an existing MP3 file."""
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    if not input_file.suffix.lower() == '.mp3':
        print(f"❌ File must be an MP3: {input_file}")
        sys.exit(1)
    
    # For existing files, use "Local Files" as the channel name
    channel_name = "Local Files"
    video_title = input_file.stem
    sanitized_channel = utils.sanitize_filename(channel_name)
    sanitized_title = utils.sanitize_filename(video_title)
    
    # Create channel directory structure
    channel_output_dir = output_dir / sanitized_channel
    channel_output_dir.mkdir(exist_ok=True)
    video_output_dir = channel_output_dir
    
    # Copy the file to the channel output directory if it's not already there
    if input_file.parent != video_output_dir:
        new_input_file = video_output_dir / input_file.name
        if not new_input_file.exists():
            import shutil
            shutil.copy2(input_file, new_input_file)
        input_file = new_input_file
    
    print(f"📁 Processing: {input_file.name}")
    print(f"📂 Channel folder: {channel_name}")
    progress_tracker.start("Processing audio file")
    progress_tracker.update_step('download', 100, "File ready")  # Skip download step
    
    return input_file, video_title, video_output_dir


def process_youtube_url(args, output_dir, progress_tracker):
    """Download and process a YouTube URL."""
    if not utils.is_valid_youtube_url(args.url):
        print("❌ Error: Invalid YouTube URL provided.")
        sys.exit(1)
    
    url = args.url
    
    # Start progress tracking
    progress_tracker.start("YouTube to MP3 + Translation")
    
    # Download and convert
    downloaded_file, video_title, channel_name = youtube_downloader.download_youtube_video(url, output_dir, progress_tracker)
    
    if downloaded_file and video_title and channel_name:
        input_file = downloaded_file
        video_output_dir = downloaded_file.parent  # This is already the channel directory
        print(f"📂 Channel: {channel_name}")
        print(f"📁 Video: {video_title}")
        return input_file, video_title, video_output_dir
    else:
        progress_tracker.finish("❌ Download failed")
        print("❌ Could not download or find MP3 file")
        sys.exit(1)


def run_translation(input_file, video_output_dir, progress_tracker, api_key):
    """Run the translation process."""
    # Get the AudioTranslator class
    AudioTranslator = translator_interface.get_audio_translator_class()
    if not AudioTranslator:
        progress_tracker.finish("❌ Translation module missing")
        sys.exit(1)
    
    # Initialize translator
    translator = AudioTranslator(api_key)
    
    # Run translation with progress tracking
    output_file = translator_interface.run_translation_with_progress(translator, input_file, video_output_dir, progress_tracker)
    
    if output_file:
        progress_tracker.finish("✅ Complete")
        
        # Show output file information after progress bar completes
        transcript_file = video_output_dir / f"{input_file.stem}_transcript.json"
        print(f"\n🎉 Translation completed successfully!")
        print(f"� Channel folder: {video_output_dir}")
        print(f"🎵 Original audio: {input_file}")
        print(f"📄 Transcript: {transcript_file}")
        print(f"🎵 Bilingual audio: {output_file}")
        return True
    else:
        progress_tracker.finish("❌ Translation failed")
        return False


def main():
    """Main function to run the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Download YouTube videos and translate Japanese audio to English with bilingual output",
        epilog="Examples:\n"
               "  python main.py --url https://youtu.be/VIDEO_ID\n"
               "  python main.py --file podcast.mp3\n"
               "  python main.py --setup\n"
               "  python main.py --test\n\n"
               "Output: Creates a folder structure in ./output/:\n"
               "  - output/[Channel Name]/\n"
               "    - Original MP3 file\n"
               "    - JSON transcript file\n"
               "    - Bilingual MP3 file\n"
               "  (Local files use 'Local Files' as channel name)",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        help='Output directory for processed files (default: ./output/)'
    )
    parser.add_argument(
        '--openai-key',
        help='OpenAI API key for translation and natural TTS (required)'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run the setup process to install dependencies and configure the environment'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run the test suite to verify functionality'
    )
    
    args = parser.parse_args()
    
    # Handle setup command
    if args.setup:
        import setup
        sys.exit(0 if setup.run_setup() else 1)
    
    # Handle test command
    if args.test:
        sys.path.insert(0, str(Path(__file__).parent / "tests"))
        import tests
        print("🧪 Running test suite...")
        success = tests.run_all_tests()
        sys.exit(0 if success else 1)
    
    # Validate that either --url or --file is provided, but not both (unless --setup or --test is used)
    if not args.setup and not args.test:
        if not args.url and not args.file:
            parser.error("Either --url or --file must be provided")
        if args.url and args.file:
            parser.error("Cannot use both --url and --file at the same time")
    
    # Check dependencies
    check_dependencies()
    
    # Get output directory
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = utils.get_output_directory()
    
    # Initialize unified progress tracker
    tracker = pt.UnifiedProgressTracker()
    
    # Process input: either YouTube URL or existing file
    try:
        if args.file:
            input_file, video_title, video_output_dir = process_existing_file(args, output_dir, tracker)
        else:
            input_file, video_title, video_output_dir = process_youtube_url(args, output_dir, tracker)
        
        # Get API key
        api_key = args.openai_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            tracker.finish("❌ Missing API key")
            print("❌ OpenAI API key required. Set OPENAI_API_KEY env var or use --openai-key")
            sys.exit(1)
        
        # Run translation
        success = run_translation(input_file, video_output_dir, tracker, api_key)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        if 'tracker' in locals():
            tracker.finish("❌ Cancelled by user")
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        if 'tracker' in locals():
            tracker.finish("❌ Error occurred")
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
