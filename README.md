# YouTube Japanese Audio Translator

A powerful CLI tool that downloads YouTube videos and creates bilingual audio with English translations spoken before each Japanese sentence.

## Features

- 🎵 **YouTube Download**: Extract high-quality MP3 from YouTube videos
- 🎌 **Japanese Speech Recognition**: OpenAI Whisper API for accurate transcription
- 🌐 **AI Translation**: GPT models for natural English translations
- � **Bilingual Audio**: EN→JP pattern with timing preservation
- � **Progress Tracking**: Real-time progress bars for all operations
- 🔊 **Natural Text-to-Speech**: OpenAI TTS for human-like English voice
- 📄 **Transcript Export**: JSON output with timing and translations

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
```bash
python main.py --url "https://youtu.be/VIDEO_ID" --output "/custom/path"
```

### Direct Audio Translation
Process MP3 files directly with the audio translator:
```bash
python main.py --file podcast.mp3
```

### All Options
```bash
python main.py --help
```

## Output Structure

```
output/
└── Youtube Channel/                   # Video-specific folder
    ├── Video_Title.mp3                # Original audio
    ├── Video_Title_transcript.json    # Timing + translations
    └── Video_Title_bilingual.mp3      # EN→JP→EN audio
```

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
