# Output Directory

This directory contains the processed bilingual audio files and transcription data.

## File Types

### Bilingual Audio Files
- `*_bilingual.mp3` - Audio with English translations before each Japanese segment
- Format: English translation → pause → Original Japanese → pause → repeat

### Transcript Files  
- `*_transcript.json` - Detailed timing and translation data
- Contains: Original Japanese text, English translations, timestamps

## Example Output Structure
```
output/
├── Video_Title_bilingual.mp3
├── Video_Title_transcript.json
├── Podcast_Episode_bilingual.mp3
└── Podcast_Episode_transcript.json
```

**Note**: This directory is excluded from version control (.gitignore) as it contains processed content.
