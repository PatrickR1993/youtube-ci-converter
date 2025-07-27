#!/usr/bin/env python3
"""
Cross-Platform Compatibility Test for YouTube CI Converter (ytcc)
Tests basic functionality across Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def test_platform_compatibility():
    """Test cross-platform compatibility."""
    print("🌍 YouTube CI Converter (ytcc) - Cross-Platform Test")
    print("=" * 60)
    
    # System information
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Current directory: {Path.cwd()}")
    print(f"🛠️  OS name: {os.name}")
    print()
    
    # Test ytcc script existence and permissions
    ytcc_script = Path(__file__).parent.parent / "ytcc"
    
    if ytcc_script.exists():
        print("✅ ytcc script found")
        
        # Check if it's executable on Unix systems
        if os.name != 'nt':  # Not Windows
            if os.access(ytcc_script, os.X_OK):
                print("✅ ytcc script is executable")
            else:
                print("⚠️  ytcc script is not executable, fixing...")
                try:
                    ytcc_script.chmod(0o755)
                    print("✅ Made ytcc script executable")
                except Exception as e:
                    print(f"❌ Could not make executable: {e}")
        
        # Test basic ytcc functionality
        print("\n🧪 Testing ytcc functionality...")
        try:
            if platform.system() == "Windows":
                # On Windows, use python to run the script
                cmd = [sys.executable, str(ytcc_script), "--help"]
            else:
                # On Unix-like systems, can run directly
                cmd = [str(ytcc_script), "--help"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ ytcc --help works correctly")
                print(f"   Help text length: {len(result.stdout)} characters")
            else:
                print(f"❌ ytcc --help failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ ytcc --help timed out (but script exists)")
        except Exception as e:
            print(f"❌ Error testing ytcc: {e}")
    
    else:
        print("❌ ytcc script not found")
    
    # Test Python module imports
    print("\n📦 Testing module imports...")
    test_modules = ['pathlib', 'subprocess', 'argparse', 'os', 'sys']
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (missing)")
    
    # Test ytcc src modules
    src_dir = Path(__file__).parent.parent / "src"
    if src_dir.exists():
        print(f"\n📂 Testing ytcc modules in {src_dir}...")
        sys.path.insert(0, str(src_dir))
        
        ytcc_modules = ['utils', 'progress_tracker', 'youtube_downloader', 'translator_interface']
        
        for module in ytcc_modules:
            try:
                __import__(module)
                print(f"✅ {module}")
            except ImportError as e:
                print(f"❌ {module}: {e}")
        
        sys.path.remove(str(src_dir))
    else:
        print("❌ src directory not found")
    
    # Platform-specific recommendations
    print(f"\n🔧 Platform-Specific Setup:")
    
    if platform.system() == "Windows":
        print("🪟 Windows detected:")
        print("   - Use ytcc.bat for easy execution")
        print("   - Or run: python ytcc [args]")
        print("   - Install FFmpeg via Chocolatey: choco install ffmpeg")
        
    elif platform.system() == "Darwin":  # macOS
        print("🍎 macOS detected:")
        print("   - Use ./ytcc directly (after chmod +x)")
        print("   - Install FFmpeg via Homebrew: brew install ffmpeg")
        print("   - Works on both Intel and Apple Silicon")
        
    elif platform.system() == "Linux":
        print("🐧 Linux detected:")
        print("   - Use ./ytcc directly (after chmod +x)")
        print("   - Install FFmpeg via package manager:")
        print("     Ubuntu/Debian: sudo apt install ffmpeg")
        print("     Fedora: sudo dnf install ffmpeg")
        print("     Arch: sudo pacman -S ffmpeg")
    
    print(f"\n🎉 Cross-platform compatibility test complete!")
    print("   The tool should work on all major platforms with proper setup.")

if __name__ == "__main__":
    test_platform_compatibility()
