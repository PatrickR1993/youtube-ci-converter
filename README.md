# YouTube CI Converter

A powerful CLI tool that downloads YouTube videos and creates bilingual audio with English translations spoken before each Japanese sentence.

## Features

- 🎵 **YouTube Download**: Convert Japanese YouTube videos to bilingual audio + original audio in one file
- 🎌 **Japanese Speech Recognition**: OpenAI Whisper API for accurate transcription
- 🌐 **AI Translation**: GPT models for natural English translations
- 📁 **Smart File Organization**: Videos organized by channel with upload dates (YYYY-MM-DD format)
- 🎙️ **Bilingual Audio**: EN→JP pattern with timing preservation
- �🔊 **Natural Text-to-Speech**: OpenAI TTS for human-like English voice
- 📄 **Optional Transcript Export**: JSON output with timing and translations (optional)

## First Time Setup

### 1. Run Setup Script
```bash
python main.py --setup
```

This will:
- Check system requirements (Python 3.6+, FFmpeg)
- Install all Python dependencies
- Create necessary directories
- Test the installation

### 2. Install FFmpeg

**System requirements:**
- **Windows**: Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

### 3. Get OpenAI API Key

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set environment variable (or, just add it as an argument, see below):

   **Windows (PowerShell):**
   ```powershell
   $env:OPENAI_API_KEY="your_api_key_here"
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   set OPENAI_API_KEY=your_api_key_here
   ```
   
   **macOS/Linux:**
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
   
   **Permanent Storage (recommended):**
   - **Windows**: Add to system environment variables via Control Panel → System → Advanced → Environment Variables
   - **macOS/Linux**: Add `export OPENAI_API_KEY=your_api_key_here` to your `~/.bashrc` or `~/.zshrc` file

## Basic Usage

### Download and Translate YouTube Video
```bash
python main.py --url "https://youtu.be/VIDEO_ID"
```

### Process Existing MP3 File
```bash
python main.py --file "your_podcast.mp3"
```

### With API Key (if not set as environment variable)
```bash
python main.py --url "https://youtu.be/VIDEO_ID" --openai-key YOUR_API_KEY
```

## Advanced Options

### Custom Output Directory
By default, files are saved to `~/Downloads/YouTube CI Converter/`. To use a custom directory:
```bash
python main.py --url "https://youtu.be/VIDEO_ID" --output "/custom/path"
```

### Direct Audio Translation
Process MP3 files directly with the audio translator:
```bash
python main.py --file podcast.mp3
```

### Keep Transcript Files
By default, JSON transcript files are removed after processing to keep output clean. To keep them:
```bash
python main.py --url "https://youtu.be/VIDEO_ID" --keep-transcript
```

### Separate Audio Files
By default, the output is a single combined file with bilingual audio followed by the original (original standalone file is removed). To keep them separate:
```bash
python main.py --url "https://youtu.be/VIDEO_ID" --separate-files
```

### All Options
```bash
python main.py --help
```

## Output Structure

```
~/Downloads/YouTube CI Converter/
└── Youtube Channel/                                # Channel-specific folder
    ├── 2024-03-15 - Video_Title_complete.mp3       # Combined: bilingual + original (default)
    ├── 2024-03-15 - Video_Title.mp3                # Original audio (only with --separate-files)
    ├── 2024-03-15 - Video_Title_bilingual.mp3      # EN→JP→EN audio (only with --separate-files)
    └── 2024-03-15 - Video_Title_transcript.json    # Timing + translations (only with --keep-transcript)
```

### Combined Audio Format (Default)

By default, the tool creates a single `_complete.mp3` file containing:

1. **Bilingual Section**: English translation → Japanese original (for each sentence)
2. **Audio Cue**: Brief silence + gentle beep + silence (separates sections)
3. **Original Section**: Complete original Japanese audio

The original standalone file is automatically removed to keep output clean.

This format allows you to:
- Practice with translations first
- Hear the original after for comparison
- Have everything in one convenient file
- Keep output folder organized

## Text-to-Speech

Uses **OpenAI TTS** with natural "alloy" voice for human-like English speech quality. Cost: ~$15 per 1M characters.

## Common Issues

**FFmpeg not found**: Install FFmpeg and add to system PATH

**OpenAI API errors**: 
- Check API key: `echo $OPENAI_API_KEY`
- Verify account credits at [OpenAI Usage](https://platform.openai.com/usage)

**Permission errors**: Run from a directory with write permissions

## Testing

The project includes a comprehensive test suite to ensure functionality and reliability.

### Run All Tests
```bash
python main.py --test
```

### Quick Functional Test
For a fast verification of core functionality:
```bash
python tests/quick_test.py
```

## License

Educational use only. Respect YouTube's Terms of Service and copyright laws.
