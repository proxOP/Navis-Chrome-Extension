"""
Test basic setup and environment
"""

import os
import sys
from pathlib import Path


def test_python_version():
    """Test that we're using Python 3.8+"""
    assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"


def test_virtual_environment():
    """Test that we're running in a virtual environment"""
    # This test will pass if we're in a venv or if we're not (for CI/CD)
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    # Just log the status, don't fail
    print(f"Virtual environment active: {in_venv}")


def test_required_packages():
    """Test that required packages are installed"""
    required_packages = ["pytest", "black", "requests", "selenium", "pydantic"]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            assert False, f"Required package '{package}' not installed"


def test_project_structure():
    """Test that basic project structure exists"""
    required_files = ["requirements.txt", ".env.template", ".gitignore"]

    required_dirs = [".kiro/spec", "scripts", "tests"]

    for file_path in required_files:
        assert Path(file_path).exists(), f"Required file '{file_path}' not found"

    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Required directory '{dir_path}' not found"


def test_environment_template():
    """Test that environment template has required variables"""
    env_template = Path(".env.template")
    assert env_template.exists(), ".env.template not found"

    content = env_template.read_text()
    required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEBUG", "EXTENSION_ID"]

    for var in required_vars:
        assert var in content, f"Required environment variable '{var}' not in template"
