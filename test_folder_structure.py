#!/usr/bin/env python3
"""
Test script to demonstrate the new channel-based folder structure
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utils import sanitize_filename

def test_folder_structure():
    """Test the new channel-based folder structure."""
    print("🧪 Testing Channel-Based Folder Structure")
    print("=" * 45)
    
    # Test cases
    test_cases = [
        {
            "channel": "TED Talks",
            "video": "How to speak so that people want to listen",
            "expected_path": "output/TED Talks/How to speak so that people want to listen_bilingual.mp3"
        },
        {
            "channel": "NHK World-Japan",
            "video": "Documentary: Life in Tokyo",
            "expected_path": "output/NHK World-Japan/Documentary_ Life in Tokyo_bilingual.mp3"
        },
        {
            "channel": "Local Files",
            "video": "my-podcast-episode",
            "expected_path": "output/Local Files/my-podcast-episode_bilingual.mp3"
        }
    ]
    
    base_output_dir = Path("output")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📂 Test {i}: {test_case['channel']}")
        
        # Sanitize names
        sanitized_channel = sanitize_filename(test_case['channel'])
        sanitized_video = sanitize_filename(test_case['video'])
        
        # Create expected folder structure
        channel_dir = base_output_dir / sanitized_channel
        bilingual_file = channel_dir / f"{sanitized_video}_bilingual.mp3"
        transcript_file = channel_dir / f"{sanitized_video}_transcript.json"
        
        print(f"   📁 Channel folder: {channel_dir}")
        print(f"   🎵 Bilingual audio: {bilingual_file}")
        print(f"   📄 Transcript: {transcript_file}")
        
        # Show what would be created
        print(f"   ✓ Files would be organized under: {sanitized_channel}/")

    print(f"\n💡 Benefits of the new structure:")
    print(f"   • Files are organized by YouTube channel")
    print(f"   • Easy to find content from specific creators")
    print(f"   • Local files go in 'Local Files' folder")
    print(f"   • Clean, hierarchical organization")
    
    print(f"\n📋 Example output structure:")
    print(f"   output/")
    print(f"   ├── TED Talks/")
    print(f"   │   ├── video1_bilingual.mp3")
    print(f"   │   ├── video1_transcript.json")
    print(f"   │   └── video2_bilingual.mp3")
    print(f"   ├── NHK World-Japan/")
    print(f"   │   └── documentary_bilingual.mp3")
    print(f"   └── Local Files/")
    print(f"       └── podcast_bilingual.mp3")

if __name__ == "__main__":
    test_folder_structure()
