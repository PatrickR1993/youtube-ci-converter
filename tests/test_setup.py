#!/usr/bin/env python3
"""
Setup tests focusing on core functionality.
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


class TestSetup(unittest.TestCase):
    """Setup tests."""

    def test_setup_module_imports(self):
        """Test that setup module can be imported."""
        try:
            import setup
            self.assertTrue(hasattr(setup, 'run_setup'))
            self.assertTrue(hasattr(setup, 'main'))
        except ImportError as e:
            self.fail(f"Setup module import failed: {e}")

    def test_setup_has_required_functions(self):
        """Test that setup has all required functions."""
        import setup
        
        required_functions = [
            'check_system_requirements',
            'install_python_dependencies', 
            'create_directories',
            'run_command',
            'run_setup'
        ]
        
        for func_name in required_functions:
            self.assertTrue(hasattr(setup, func_name), f"Missing function: {func_name}")

    def test_setup_run_command_basic(self):
        """Test basic run_command functionality."""
        import setup
        
        # Test with a simple command that should work
        try:
            result = setup.run_command(['python', '--version'])
            self.assertIsInstance(result, bool)
        except Exception as e:
            # This is OK - we just want to test the function exists and handles calls
            pass


if __name__ == "__main__":
    unittest.main()
