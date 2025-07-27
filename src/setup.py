#!/usr/bin/env python3
"""
Setup script for YouTube CI Converter with Audio Translation
Installs all required dependencies and checks system requirements
"""

import subprocess
import sys
import os
import shutil
import stat
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

def get_ytcc_install_dir():
    """Get the platform-appropriate installation directory for ytcc."""
    if os.name == 'nt':  # Windows
        # Use %LOCALAPPDATA%\Programs\ytcc
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        install_dir = Path(appdata) / 'Programs' / 'ytcc'
    else:  # Unix-like systems (macOS, Linux)
        # Use ~/.local/bin (standard for user-local binaries)
        install_dir = Path.home() / '.local' / 'bin'
    
    return install_dir

def get_ytcc_support_dir():
    """Get the platform-appropriate support/data directory for ytcc."""
    if os.name == 'nt':  # Windows
        # Use %LOCALAPPDATA%\Programs\ytcc (same as install dir)
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        support_dir = Path(appdata) / 'Programs' / 'ytcc'
    else:  # Unix-like systems (macOS, Linux)
        # Use ~/.local/share/ytcc
        support_dir = Path.home() / '.local' / 'share' / 'ytcc'
    
    return support_dir

def install_ytcc_to_path():
    """Install ytcc script to system PATH."""
    print("🔗 Installing ytcc to system PATH...")
    
    try:
        # Get installation directories
        install_dir = get_ytcc_install_dir()
        support_dir = get_ytcc_support_dir()
        project_root = Path(__file__).parent.parent
        
        # Create directories
        install_dir.mkdir(parents=True, exist_ok=True)
        support_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the main ytcc script
        ytcc_source = project_root / 'ytcc'
        ytcc_dest = install_dir / 'ytcc'
        
        if not ytcc_source.exists():
            print("❌ ytcc script not found in project root")
            return False
        
        # Copy ytcc script
        shutil.copy2(ytcc_source, ytcc_dest)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(ytcc_dest, os.stat(ytcc_dest).st_mode | stat.S_IEXEC)
        
        # Copy src directory
        src_source = project_root / 'src'
        src_dest = support_dir / 'src'
        
        if src_dest.exists():
            shutil.rmtree(src_dest)
        shutil.copytree(src_source, src_dest)
        
        # Platform-specific PATH setup
        if os.name == 'nt':  # Windows
            return _install_windows_path(install_dir)
        else:  # Unix-like systems
            return _install_unix_path(install_dir)
            
    except Exception as e:
        print(f"❌ Failed to install ytcc to PATH: {e}")
        return False

def _install_windows_path(install_dir):
    """Add directory to Windows PATH via registry."""
    try:
        import winreg
        
        # Open registry key for user environment variables
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                # Get current PATH
                current_path, _ = winreg.QueryValueEx(key, 'PATH')
            except FileNotFoundError:
                current_path = ""
            
            # Check if already in PATH
            install_dir_str = str(install_dir)
            if install_dir_str.lower() in current_path.lower():
                print(f"✅ {install_dir} already in PATH")
                return True
            
            # Add to PATH
            new_path = f"{current_path};{install_dir_str}" if current_path else install_dir_str
            winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)
            
            print(f"✅ Added {install_dir} to Windows PATH")
            print("⚠️  Restart your terminal or VS Code for PATH changes to take effect")
            return True
            
    except ImportError:
        print("❌ Windows registry access not available")
        return False
    except Exception as e:
        print(f"❌ Failed to update Windows PATH: {e}")
        return False

def _install_unix_path(install_dir):
    """Add directory to Unix PATH via shell profiles."""
    install_dir_str = str(install_dir)
    
    # Check if already in PATH
    current_path = os.environ.get('PATH', '')
    if install_dir_str in current_path:
        print(f"✅ {install_dir} already in PATH")
        return True
    
    # Common shell profile files
    home = Path.home()
    profile_files = [
        home / '.bashrc',
        home / '.zshrc',
        home / '.profile'
    ]
    
    export_line = f'export PATH="$PATH:{install_dir_str}"\n'
    updated_files = []
    
    for profile_file in profile_files:
        if profile_file.exists():
            try:
                # Check if already added
                content = profile_file.read_text()
                if install_dir_str in content:
                    continue
                
                # Add export line
                with open(profile_file, 'a') as f:
                    f.write(f'\n# Added by ytcc installer\n{export_line}')
                updated_files.append(str(profile_file))
                
            except Exception as e:
                print(f"⚠️  Could not update {profile_file}: {e}")
    
    if updated_files:
        print(f"✅ Added {install_dir} to PATH in: {', '.join(updated_files)}")
        print("⚠️  Restart your terminal or run 'source ~/.bashrc' (or ~/.zshrc) for changes to take effect")
        return True
    else:
        print(f"⚠️  Could not automatically update PATH. Manually add to your shell profile:")
        print(f"   {export_line.strip()}")
        return False

def uninstall_ytcc_from_path():
    """Remove ytcc from system PATH and clean up installed files."""
    print("🗑️  Uninstalling ytcc from system...")
    
    try:
        install_dir = get_ytcc_install_dir()
        support_dir = get_ytcc_support_dir()
        
        # Remove installed files
        if install_dir.exists():
            shutil.rmtree(install_dir)
            print(f"✅ Removed installation directory: {install_dir}")
        
        if support_dir.exists() and support_dir != install_dir:
            shutil.rmtree(support_dir)
            print(f"✅ Removed support directory: {support_dir}")
        
        # Platform-specific PATH cleanup
        if os.name == 'nt':  # Windows
            _uninstall_windows_path(install_dir)
        else:  # Unix-like systems
            _uninstall_unix_path(install_dir)
        
        print("✅ ytcc uninstalled successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to uninstall ytcc: {e}")
        return False

def _uninstall_windows_path(install_dir):
    """Remove directory from Windows PATH."""
    try:
        import winreg
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, 'PATH')
            except FileNotFoundError:
                return
            
            # Remove from PATH
            install_dir_str = str(install_dir)
            path_parts = [p.strip() for p in current_path.split(';') if p.strip()]
            new_path_parts = [p for p in path_parts if p.lower() != install_dir_str.lower()]
            
            if len(new_path_parts) != len(path_parts):
                new_path = ';'.join(new_path_parts)
                winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"✅ Removed {install_dir} from Windows PATH")
            
    except Exception as e:
        print(f"⚠️  Could not clean Windows PATH: {e}")

def _uninstall_unix_path(install_dir):
    """Remove directory from Unix shell profiles."""
    install_dir_str = str(install_dir)
    home = Path.home()
    profile_files = [
        home / '.bashrc',
        home / '.zshrc',
        home / '.profile'
    ]
    
    for profile_file in profile_files:
        if profile_file.exists():
            try:
                content = profile_file.read_text()
                lines = content.split('\n')
                
                # Remove lines containing the install directory
                new_lines = []
                skip_next = False
                
                for line in lines:
                    if skip_next and line.strip() == '':
                        skip_next = False
                        continue
                    
                    if install_dir_str in line:
                        skip_next = True
                        continue
                    elif line.strip() == '# Added by ytcc installer':
                        skip_next = True
                        continue
                    
                    new_lines.append(line)
                    skip_next = False
                
                if len(new_lines) != len(lines):
                    profile_file.write_text('\n'.join(new_lines))
                    print(f"✅ Cleaned PATH from {profile_file}")
                    
            except Exception as e:
                print(f"⚠️  Could not clean {profile_file}: {e}")

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
    """Main setup function - callable from ytcc CLI."""
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
    
    # Step 5: Install ytcc to system PATH
    if install_ytcc_to_path():
        success_steps.append("System PATH installation")
        print("✅ ytcc is now available system-wide!")
    else:
        print("⚠️  PATH installation failed - ytcc may not be available globally")
        print("   You can still run ytcc from the project directory")
    
    # Step 6: Test installation
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
    print("   ytcc --url https://youtu.be/VIDEO_ID")
    
    print("\n2. Process existing MP3 file:")
    print("   ytcc --file your_podcast.mp3")
    
    print("\n3. With custom output directory:")
    print("   ytcc --url https://youtu.be/VIDEO_ID --output /custom/path")
    
    print("\n4. With API key (if not set as environment variable):")
    print("   ytcc --url https://youtu.be/VIDEO_ID --openai-key YOUR_API_KEY")
    
    print("\n5. Run setup again:")
    print("   ytcc --setup")
    
    print("\n🔄 To uninstall ytcc from your system:")
    print("   python src/setup.py --uninstall")
    
    print(f"\n🔑 Required for translation:")
    print("   - OpenAI API key: https://platform.openai.com/api-keys")
    print("   - Set environment variable: export OPENAI_API_KEY=your_key")
    print("   - Or use --openai-key parameter")
    
    print(f"\n📁 Output files:")
    print("   - output/[Video Name]/: Organized by video with all files")
    print("     - Original MP3 + transcript JSON + bilingual audio")
    
    if "System PATH installation" in success_steps:
        print(f"\n🌟 ytcc is now installed system-wide!")
        print("   You can run 'ytcc' from any directory after restarting your terminal")
    
    return True

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--uninstall':
            print("🗑️  Uninstalling YouTube CI Converter...")
            success = uninstall_ytcc_from_path()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == '--help':
            print("YouTube CI Converter Setup Script")
            print("=" * 40)
            print("Usage:")
            print("  python src/setup.py         # Install and setup ytcc")
            print("  python src/setup.py --uninstall  # Remove ytcc from system")
            print("  python src/setup.py --help       # Show this help")
            sys.exit(0)
    
    # Run normal setup
    success = main()
    sys.exit(0 if success else 1)
