# Changelog

All notable changes to YouTube Japanese Audio Translator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-22

### Added
- **Tests**: Run unittests with python main.py --test

### Refactored
- **Project Structure**: Moved scripts to modules in /src, interact through main.py

---

## [1.0.0] - 2025-07-21

### Added
- **YouTube Download & Conversion**: Download YouTube videos and convert to MP3
- **Japanese Audio Translation**: Automatic translation of Japanese speech to English
- **Bilingual Audio Generation**: Create audio with English translation before each Japanese segment
- **Unified Progress Tracking**: Single progress bar for entire workflow (download → translation → audio generation)
- **OpenAI Integration**: 
  - Whisper API for speech recognition
  - GPT for natural language translation  
  - TTS for human-like English voice synthesis
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility
- **JSON Transcript Export**: Detailed timing and translation data
- **Command Line Interface**: Simple CLI with comprehensive options
- **Setup Script**: Automated dependency installation and verification

### Features
- **Progress Weighting**: Intelligent progress distribution (30% download, 40% translation, 30% audio generation)
- **Error Handling**: Graceful error handling with user-friendly messages
- **File Processing**: Support for both YouTube URLs and existing MP3 files
- **Custom Output**: Configurable output directories
- **API Key Management**: Environment variable and parameter support

### Technical Details
- Built with Python 3.6+
- Uses yt-dlp for YouTube downloads
- Leverages pydub for audio processing
- Implements tqdm for progress visualization
- Requires FFmpeg for audio conversion

### Dependencies
- `yt-dlp>=2023.12.30` - YouTube video downloading
- `openai>=1.0.0` - AI-powered translation and TTS
- `pydub>=0.25.1` - Audio processing and manipulation
- `tqdm>=4.64.0` - Progress bar visualization

### System Requirements
- Python 3.6 or higher
- FFmpeg installed and accessible
- OpenAI API key for translation features
- Internet connection for YouTube downloads and API calls

---

## Future Roadmap

### Planned Features
- **Multi-language Support**: Extend beyond Japanese to other languages
- **Batch Processing**: Handle playlists and multiple files
- **Quality Settings**: Configurable audio quality and translation options
- **Web Interface**: Optional web-based GUI
- **Caching System**: Cache translations to reduce API costs

### Performance Improvements
- **Parallel Processing**: Concurrent translation and audio generation
- **Memory Optimization**: Reduce memory usage for large files
- **Speed Enhancements**: Faster audio processing algorithms

### Developer Experience
- **CI/CD Pipeline**: Automated testing and releases
