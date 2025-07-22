#!/usr/bin/env python3
"""
Setup script for YouTube CI Converter with Audio Translation
Installs all required dependencies and checks system requirements
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False

def check_system_requirements():
    """Check if required system tools are installed."""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check FFmpeg - try multiple approaches for cross-platform compatibility
    ffmpeg_found = False
    
    # Try direct ffmpeg command
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ FFmpeg is installed")
        ffmpeg_found = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # If not found directly, try WSL (for Windows users with WSL)
    if not ffmpeg_found and os.name == 'nt':  # Windows
        try:
            subprocess.run(['wsl', 'ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print("✅ FFmpeg is installed in WSL")
            ffmpeg_found = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    if not ffmpeg_found:
        print("⚠️  FFmpeg not found - required for audio processing")
        print("   Install instructions:")
        print("   - Ubuntu/WSL: sudo apt update && sudo apt install ffmpeg")
        print("   - macOS: brew install ffmpeg")
        print("   - Windows: Download from https://ffmpeg.org/")
        print("   Note: If you have WSL with FFmpeg installed, this may still work")
        return False
    
    return True

def install_python_dependencies():
    """Install Python packages from requirements.txt."""
    print("📦 Installing Python dependencies...")
    
    # Look for requirements.txt in the parent directory (project root)
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    # Upgrade pip first
    if not run_command(f'"{sys.executable}" -m pip install --upgrade pip', "Upgrading pip"):
        return False
    
    # Install requirements - properly quote the path
    return run_command(
        f'"{sys.executable}" -m pip install -r "{requirements_file}"',
        "Installing Python packages"
    )

def install_system_audio_dependencies():
    """Install system-level audio dependencies."""
    print("🔊 Checking audio system dependencies...")
    
    # Detect OS and provide instructions
    if os.name == 'posix':  # Linux/macOS
        if sys.platform.startswith('linux'):
            print("📋 For Ubuntu/Debian, you may need to install:")
            print("   sudo apt update")
            print("   sudo apt install espeak espeak-data libespeak1 libespeak-dev")
        elif sys.platform == 'darwin':  # macOS
            print("📋 For macOS, dependencies should install automatically")
    else:  # Windows
        print("📋 For Windows, audio dependencies should install automatically")
        print("   If you encounter issues, you may need Visual C++ Build Tools")
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    # Create directories in the project root (parent of src)
    project_root = Path(__file__).parent.parent
    dirs_to_create = [
        project_root / "output"
    ]
    
    for directory in dirs_to_create:
        directory.mkdir(exist_ok=True)
        print(f"✅ Created: {directory}")
    
    return True

def test_installation():
    """Test if all components are working."""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        import yt_dlp
        print("✅ yt-dlp import successful")
        
        import pydub
        print("✅ pydub import successful")
        
        import tqdm
        print("✅ tqdm import successful")
        
        try:
            import openai
            print("✅ openai import successful")
        except ImportError:
            print("⚠️  openai not available (install with: pip install openai)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

def run_setup():
    """Main setup function - callable from main.py."""
    return main()


def main():
    """Main setup function."""
    print("🚀 YouTube CI Converter with Audio Translation Setup")
    print("=" * 60)
    
    success_steps = []
    
    # Step 1: Check system requirements
    if check_system_requirements():
        success_steps.append("System requirements")
    else:
        print("\n❌ Setup failed: System requirements not met")
        print("Please install missing dependencies and run setup again")
        return False
    
    # Step 2: Install system audio dependencies
    if install_system_audio_dependencies():
        success_steps.append("System audio setup")
    
    # Step 3: Install Python dependencies
    if install_python_dependencies():
        success_steps.append("Python packages")
    else:
        print("\n❌ Setup failed: Could not install Python packages")
        return False
    
    # Step 4: Create directories
    if create_directories():
        success_steps.append("Directory structure")
    
    # Step 5: Test installation
    if test_installation():
        success_steps.append("Installation test")
    else:
        print("\n⚠️  Setup completed but some tests failed")
        print("You may need to install additional dependencies")
    
    # Summary
    print(f"\n🎉 Setup Summary")
    print("=" * 30)
    for step in success_steps:
        print(f"✅ {step}")
    
    print(f"\n📖 Usage Examples:")
    print("1. Download YouTube video and translate Japanese audio:")
    print("   python main.py --url https://youtu.be/VIDEO_ID")
    
    print("\n2. Process existing MP3 file:")
    print("   python main.py --file your_podcast.mp3")
    
    print("\n3. With custom output directory:")
    print("   python main.py --url https://youtu.be/VIDEO_ID --output /custom/path")
    
    print("\n4. With API key (if not set as environment variable):")
    print("   python main.py --url https://youtu.be/VIDEO_ID --openai-key YOUR_API_KEY")
    
    print("\n5. Run setup again:")
    print("   python main.py --setup")
    
    print(f"\n🔑 Required for translation:")
    print("   - OpenAI API key: https://platform.openai.com/api-keys")
    print("   - Set environment variable: export OPENAI_API_KEY=your_key")
    print("   - Or use --openai-key parameter")
    
    print(f"\n📁 Output files:")
    print("   - output/[Video Name]/: Organized by video with all files")
    print("     - Original MP3 + transcript JSON + bilingual audio")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
