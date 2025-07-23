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
    progress_tracker.start("🎌 YouTube CI Converter")
    
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


def run_translation(input_file, video_output_dir, progress_tracker, api_key, keep_transcript=False, separate_files=False, use_parallel=True):
    """Run the translation process with optional parallel processing.
    
    Args:
        use_parallel: If True, uses parallel processing for faster translation and TTS generation
    """
    # Get the AudioTranslator class
    AudioTranslator = translator_interface.get_audio_translator_class()
    if not AudioTranslator:
        progress_tracker.finish("❌ Translation module missing")
        sys.exit(1)
    
    # Initialize translator
    translator = AudioTranslator(api_key)
    
    # Run translation with progress tracking (now with parallel processing option)
    output_file = translator_interface.run_translation_with_progress(
        translator, input_file, video_output_dir, progress_tracker, separate_files, use_parallel
    )
    
    if output_file:
        progress_tracker.finish("✅ Complete")
        
        # Handle transcript file
        transcript_file = video_output_dir / f"{input_file.stem}_transcript.json"
        
        if keep_transcript:
            # Show output file information including transcript
            print(f"\n🎉 Translation completed successfully!")
            print(f"📂 Channel folder: {video_output_dir}")
            if separate_files:
                print(f"🎵 Original audio: {input_file}")
                print(f"🎵 Bilingual audio: {output_file}")
            else:
                print(f"🎵 Complete audio: {output_file} (bilingual + original combined)")
            print(f"📄 Transcript: {transcript_file}")
        else:
            # Remove transcript file and don't mention it in output
            if transcript_file.exists():
                transcript_file.unlink()
                print(f"\n🎉 Translation completed successfully!")
                print(f"📂 Channel folder: {video_output_dir}")
                if separate_files:
                    print(f"🎵 Original audio: {input_file}")
                    print(f"🎵 Bilingual audio: {output_file}")
                else:
                    print(f"🎵 Complete audio: {output_file} (bilingual + original combined)")
                print("📄 Transcript file removed (use --keep-transcript to retain)")
            else:
                print(f"\n🎉 Translation completed successfully!")
                print(f"📂 Channel folder: {video_output_dir}")
                if separate_files:
                    print(f"🎵 Original audio: {input_file}")
                    print(f"🎵 Bilingual audio: {output_file}")
                else:
                    print(f"🎵 Complete audio: {output_file} (bilingual + original combined)")
        
        return True
    else:
        progress_tracker.finish("❌ Translation failed")
        return False


def main():
    """Main function to run the CLI tool."""
    parser = argparse.ArgumentParser(
        description="YouTube CI Converter - Download YouTube videos and translate Japanese audio to English with bilingual output",
        epilog="Examples:\n"
               "  python main.py --url https://youtu.be/VIDEO_ID\n"
               "  python main.py --file podcast.mp3\n"
               "  python main.py --url https://youtu.be/VIDEO_ID --keep-transcript\n"
               "  python main.py --url https://youtu.be/VIDEO_ID --separate-files\n"
               "  python main.py --url https://youtu.be/VIDEO_ID --no-parallel  # Slower but more compatible\n"
               "  python main.py --setup\n"
               "  python main.py --test\n\n"
               "Performance: Uses parallel processing by default for faster translation and TTS generation.\n"
               "Use --no-parallel if you experience API rate limiting or compatibility issues.\n\n"
               "Output: Creates a folder structure in ~/Downloads/YouTube CI Converter/:\n"
               "  - YouTube CI Converter/[Channel Name]/\n"
               "    - YYYY-MM-DD_VideoTitle_complete.mp3 (default: bilingual + original)\n"
               "    - YYYY-MM-DD_VideoTitle.mp3 (original, only with --separate-files)\n"
               "    - YYYY-MM-DD_VideoTitle_bilingual.mp3 (only with --separate-files)\n"
               "    - YYYY-MM-DD_VideoTitle_transcript.json (only with --keep-transcript)\n"
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
        help='Output directory for processed files (default: ~/Downloads/YouTube CI Converter/)'
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
    parser.add_argument(
        '--keep-transcript',
        action='store_true',
        help='Keep the JSON transcript file after processing (default: removed after use)'
    )
    parser.add_argument(
        '--separate-files',
        action='store_true',
        help='Keep bilingual and original audio as separate files (default: combined into one file)'
    )
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel processing for translation and TTS (slower but more compatible)'
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
        
        # Run translation with parallel processing option
        use_parallel = not args.no_parallel  # Default to parallel unless --no-parallel is specified
        success = run_translation(input_file, video_output_dir, tracker, api_key, args.keep_transcript, args.separate_files, use_parallel)
        
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
