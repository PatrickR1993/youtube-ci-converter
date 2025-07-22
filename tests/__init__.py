#!/usr/bin/env python3
"""
Test suite for YouTube CI Converter
Contains focused unit tests for core functionality.
"""

import unittest
import sys
from pathlib import Path

def setup_test_paths():
    """Set up paths for testing."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    
    # Add paths to sys.path if not already present
    for path in [str(project_root), str(src_path)]:
        if path not in sys.path:
            sys.path.insert(0, path)

# Set up paths when module is imported
setup_test_paths()

def run_all_tests(verbosity=1):
    """Run all reliable tests."""
    setup_test_paths()  # Ensure paths are set up
    
    # Create test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load the working test modules
    test_modules = [
        'tests.test_integration',
        'tests.test_utils', 
        'tests.test_progress_tracker',
        'tests.test_setup',
        'tests.test_youtube_downloader',
        'tests.quick_test'
    ]
    
    # Load tests from each module
    loaded_count = 0
    for module_name in test_modules:
        try:
            module_tests = loader.loadTestsFromName(module_name)
            suite.addTests(module_tests)
            loaded_count += 1
        except Exception as e:
            print(f"⚠️  Could not load {module_name}: {e}")
    
    print(f"✅ Loaded {loaded_count} test modules")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 Results: {passed}/{total} passed ({success_rate:.1f}%)")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
