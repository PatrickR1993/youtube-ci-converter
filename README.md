# YouTube CI Converter

A powerful CLI tool that downloads YouTube videos and creates bilingual audio files with English translations spoken before each Japanese sentence.

## ✨ Features

- 🎵 **YouTube Download**: Convert Japanese YouTube videos to bilingual audio + original audio in one file
- 🎌 **Japanese Speech Recognition**: OpenAI Whisper API for accurate transcription
- 🌐 **AI Translation**: GPT models for natural English translations
- 📦 **Batch Processing**: Process multiple YouTube URLs and local files in one command
- 📁 **Smart File Organization**: Videos organized by channel with upload dates (YYYY-MM-DD format)
- 🎙️ **Bilingual Audio**: English→Japanese pattern with timing preservation
- 🔊 **Natural Text-to-Speech**: OpenAI TTS for human-like English voice
- 📄 **Optional Transcript Export**: JSON output with timing and translations

## 🚀 Quick Start

### 1. Basic Usage
```bash
# Download and translate a YouTube video
python main.py --url "https://youtu.be/VIDEO_ID"

# Process an existing MP3 file
python main.py --file "your_podcast.mp3"

# With API key (if not set as environment variable)
python main.py --url "https://youtu.be/VIDEO_ID" --openai-key YOUR_API_KEY
```

### 2. Batch Processing
```bash
# Interactive mode - prompts for multiple URLs/files
python main.py

# Mix URLs and files
python main.py --url "https://youtu.be/VIDEO_ID" --file "local_audio.mp3"
```

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.6+**
- **FFmpeg** (for audio processing)
- **OpenAI API Key** (for translation and TTS)

### 1. Clone & Install
```bash
git clone https://github.com/PatrickR1993/youtube-ci-converter.git
cd youtube-ci-converter
python main.py --setup  # Installs dependencies and tests system
```

### 2. Install FFmpeg
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

### 3. Get OpenAI API Key
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set environment variable:

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

**For permanent storage**: Add to system environment variables or your shell profile (`~/.bashrc`, `~/.zshrc`)

## ⚙️ Advanced Options

| Option | Description | Example |
|--------|-------------|---------|
| `--output` | Custom output directory | `--output "/custom/path"` |
| `--keep-transcript` | Keep JSON transcript files | `--keep-transcript` |
| `--separate-files` | Keep bilingual and original audio separate | `--separate-files` |
| `--no-parallel` | Disable parallel processing (slower, more stable) | `--no-parallel` |
| `--short-segments` | Keep Whisper segments short instead of merging into longer sentences | `--short-segments` |

## 📁 Output Structure

**Default location**: `~/Downloads/YouTube CI Converter/`

```
YouTube CI Converter/
└── [Channel Name]/
    ├── 2024-03-15_VideoTitle_complete.mp3     # 🎯 Combined: bilingual + original (default)
    ├── 2024-03-15_VideoTitle.mp3              # 📼 Original audio (with --separate-files)
    ├── 2024-03-15_VideoTitle_bilingual.mp3    # 🗣️ EN→JP audio (with --separate-files)
    └── 2024-03-15_VideoTitle_transcript.json  # 📄 Timing + translations (with --keep-transcript)
```

### 🎵 Combined Audio Format (Default)

The `_complete.mp3` file contains:

1. **🗣️ Bilingual Section**: English translation → Japanese original (for each sentence)
2. **🔔 Audio Cue**: Brief silence + gentle beep + silence (separates sections)  
3. **📼 Original Section**: Complete original Japanese audio

## 💰 Cost & Performance

| Service | Usage | Cost |
|---------|-------|------|
| **OpenAI Whisper** | Transcription | ~$0.006 per minute |
| **GPT-3.5-turbo** | Translation | ~$0.001 per sentence |
| **OpenAI TTS** | Text-to-Speech | ~$15 per 1M characters |

**Typical costs**: $0.50-$2.00 for a 30-minute video

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **FFmpeg not found** | Install FFmpeg and add to system PATH |
| **OpenAI API errors** | Check API key: `echo $OPENAI_API_KEY`<br>Verify credits at [OpenAI Usage](https://platform.openai.com/usage) |
| **Permission errors** | Run from a directory with write permissions |
| **Rate limiting** | Use `--no-parallel` for more conservative API usage |
| **Large files fail Whisper** | Tool automatically splits files and retries (up to 4 attempts)<br>Supports files up to 16x original Whisper limit |

## 🧪 Testing

```bash
# Run comprehensive test suite
python main.py --test

# Quick functional test
python tests/quick_test.py

# View all available options
python main.py --help
```

## 📜 License

Educational use only. Please respect YouTube's Terms of Service and copyright laws.

---

**Made with ❤️ for Japanese language learners**
