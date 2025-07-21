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
python setup.py
```

### 2. Install FFmpeg

**System requirements:**
- **Windows**: Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`

### 3. Get OpenAI API Key

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set environment variable (or, just add it as an argument, see below):
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

## Basic Usage

### Download and Translate YouTube Video
```bash
python youtube_ci_converter.py --url "https://youtu.be/VIDEO_ID"
```

### Process Existing MP3 File
```bash
python youtube_ci_converter.py --file "your_podcast.mp3"
```

### With API Key (if not set as environment variable)
```bash
python youtube_ci_converter.py --url "https://youtu.be/VIDEO_ID" --openai-key YOUR_API_KEY
```

## Advanced Options

### Custom Output Directory
```bash
python youtube_ci_converter.py --url "https://youtu.be/VIDEO_ID" --output "/custom/path"
```

### Direct Audio Translation
Process MP3 files directly with the audio translator:
```bash
python audio_translator.py --file podcast.mp3
```

### All Options
```bash
python youtube_ci_converter.py --help
python audio_translator.py --help
```

## Output Structure

```
downloads/
├── Video_Title.mp3                    # Original download

output/
├── Video_Title_bilingual.mp3          # EN→JP→EN audio
└── Video_Title_transcript.json        # Timing + translations
```

## Text-to-Speech

Uses **OpenAI TTS** with natural "alloy" voice for human-like English speech quality. Cost: ~$15 per 1M characters.

## Common Issues

**FFmpeg not found**: Install FFmpeg and add to system PATH

**OpenAI API errors**: 
- Check API key: `echo $OPENAI_API_KEY`
- Verify account credits at [OpenAI Usage](https://platform.openai.com/usage)

**Permission errors**: Run from a directory with write permissions

## Cost Estimates

- **Whisper**: ~$0.006 per minute of audio
- **GPT Translation**: ~$0.002 per 1K tokens  
- **OpenAI TTS**: ~$15 per 1M characters

## License

Educational use only. Respect YouTube's Terms of Service and copyright laws.
