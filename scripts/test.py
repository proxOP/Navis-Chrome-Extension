#!/usr/bin/env python3
"""
Navis Chrome Extension - Test Runner
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests for the Navis project."""
    print("🧪 Running Navis Chrome Extension tests...")

    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Please run this script from the project root directory")
        return False

    # Run pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], check=True
        )
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Some tests failed")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Run: pip install pytest")
        return False


def run_linting():
    """Run code linting."""
    print("🔍 Running code linting...")

    try:
        # Run black formatter check
        subprocess.run([sys.executable, "-m", "black", "--check", "."], check=True)
        print("✅ Code formatting is correct")
        return True
    except subprocess.CalledProcessError:
        print("❌ Code formatting issues found. Run: python -m black .")
        return False
    except FileNotFoundError:
        print("❌ black not found. Run: pip install black")
        return False


def main():
    """Main test function."""
    print("🚀 Navis Chrome Extension - Test Suite")
    print("=" * 50)

    # Run linting first
    lint_passed = run_linting()

    # Run tests
    tests_passed = run_tests()

    print("\n" + "=" * 50)
    if lint_passed and tests_passed:
        print("🎉 All checks passed!")
        return 0
    else:
        print("❌ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
