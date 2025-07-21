# Contributing to YouTube Japanese Audio Translator

Thank you for your interest in contributing! This project helps users download YouTube videos and translate Japanese audio content with bilingual output.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YouTube-Japanese-Audio-Translator.git
   cd YouTube-Japanese-Audio-Translator
   ```
3. **Set up the development environment**:
   ```bash
   python setup.py
   ```

## Development Setup

### Prerequisites
- Python 3.6+
- FFmpeg installed on your system
- OpenAI API key for testing translation features

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python youtube_ci_converter.py --help
```

## Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following these guidelines:
   - Keep code clean and well-commented
   - Follow existing code style and naming conventions
   - Add progress tracking for long-running operations
   - Handle errors gracefully with user-friendly messages

3. **Test your changes**:
   ```bash
   # Test basic functionality
   python youtube_ci_converter.py --url https://youtu.be/SHORT_VIDEO_ID
   
   # Test with existing file
   python youtube_ci_converter.py --file test.mp3
   ```

## Code Style Guidelines

- Use descriptive variable and function names
- Add docstrings to all functions and classes
- Keep functions focused on single responsibilities
- Use type hints where helpful
- Follow PEP 8 style guidelines

## Areas for Contribution

### High Priority
- **Error handling improvements**: Better error messages and recovery
- **Performance optimization**: Faster audio processing
- **Language support**: Add support for other languages besides Japanese
- **Testing**: Unit tests and integration tests

### Medium Priority
- **UI improvements**: Better progress indicators and status messages
- **Configuration**: Settings file for default options
- **Batch processing**: Handle multiple files or playlists
- **Audio quality**: Enhanced audio processing options

### Documentation
- **Examples**: More usage examples and tutorials
- **API documentation**: Document classes and methods
- **Troubleshooting**: Common issues and solutions

## Submitting Changes

1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear description of changes
   - Any relevant issue numbers
   - Screenshots if UI changes
   - Test results

## Reporting Issues

When reporting bugs or requesting features:

1. **Search existing issues** first
2. **Use the issue templates** when available
3. **Provide detailed information**:
   - Python version
   - Operating system
   - Error messages (full stack trace)
   - Steps to reproduce
   - Expected vs actual behavior

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Respect different perspectives and experiences

## Questions?

Feel free to open an issue for questions about:
- How to implement a feature
- Project architecture decisions
- Best practices for this codebase

Thank you for contributing! 🎉
