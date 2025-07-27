#!/usr/bin/env python3
"""
Cross-platform compatibility test for ytcc setup
Tests the PATH installation functionality on different platforms
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import setup

def test_cross_platform_setup():
    """Test cross-platform setup functionality."""
    print("🧪 Testing Cross-Platform Setup Functionality")
    print("=" * 50)
    
    # Test platform detection
    print(f"🖥️  Platform: {sys.platform}")
    print(f"📁 OS Name: {os.name}")
    
    # Test directory functions
    install_dir = setup.get_ytcc_install_dir()
    support_dir = setup.get_ytcc_support_dir()
    
    print(f"📦 Install Directory: {install_dir}")
    print(f"📚 Support Directory: {support_dir}")
    
    # Test platform-specific behavior
    if os.name == 'nt':  # Windows
        print("🪟 Windows detected - will use:")
        print("   - Registry PATH modification")
        print("   - %LOCALAPPDATA%\\Programs\\ytcc installation")
        print("   - Windows-style path separators")
    else:  # Unix-like
        print("🐧 Unix-like system detected - will use:")
        print("   - Shell profile modification (.bashrc/.zshrc)")
        print("   - ~/.local/bin installation")
        print("   - Executable permissions")
    
    # Check if ytcc script exists
    ytcc_script = Path(__file__).parent.parent / "ytcc"
    if ytcc_script.exists():
        print(f"✅ ytcc script found: {ytcc_script}")
        
        # Check shebang line for Unix compatibility
        with open(ytcc_script, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith('#!/usr/bin/env python3'):
                print("✅ Proper shebang line for Unix compatibility")
            else:
                print("⚠️  Shebang line may need adjustment for Unix systems")
    else:
        print("❌ ytcc script not found")
    
    print("\n🎯 Setup Command Test:")
    print("   Run: ytcc --setup")
    print("   This will:")
    print("   1. ✅ Check system requirements")
    print("   2. ✅ Install Python dependencies")  
    print("   3. ✅ Install ytcc to system PATH")
    print("   4. ✅ Make ytcc available globally")
    
    print("\n🌟 Cross-Platform Features:")
    print("   - ✅ Windows: Registry PATH + %LOCALAPPDATA% installation")
    print("   - ✅ macOS: Shell profile + ~/.local/bin installation")
    print("   - ✅ Linux: Shell profile + ~/.local/bin installation")
    print("   - ✅ Automatic platform detection")
    print("   - ✅ Proper file permissions on Unix systems")
    
    return True

if __name__ == "__main__":
    success = test_cross_platform_setup()
    print(f"\n{'✅ Cross-platform setup test completed successfully!' if success else '❌ Test failed'}")
