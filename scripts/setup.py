#!/usr/bin/env python3
"""
Navis Chrome Extension - Development Setup Script
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None


def main():
    """Main setup function."""
    print("🚀 Setting up Navis Chrome Extension development environment...")

    # Check if we're in a virtual environment
    if not hasattr(sys, "real_prefix") and not (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("⚠️  Warning: Not running in a virtual environment")
        print(
            "   Run: navis-env\\Scripts\\activate (Windows) or source navis-env/bin/activate (Linux/Mac)"
        )
        return

    # Create necessary directories
    directories = [
        "extension/src",
        "extension/assets/icons",
        "extension/popup",
        "extension/content",
        "extension/background",
        "tests",
        "docs",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

    # Install additional development dependencies
    dev_packages = [
        "pytest-asyncio",
        "aiohttp",
        "openai",  # For LLM integration testing
    ]

    for package in dev_packages:
        run_command(f"pip install {package}", f"Installing {package}")

    # Create .env template
    env_template = """# Navis Chrome Extension - Environment Variables
# Copy this to .env and fill in your values

# LLM API Keys (for development/testing)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Development Settings
DEBUG=true
LOG_LEVEL=debug

# Chrome Extension Settings
EXTENSION_ID=your_extension_id_here
"""

    with open(".env.template", "w") as f:
        f.write(env_template)
    print("📝 Created .env.template")

    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Copy .env.template to .env and fill in your API keys")
    print("2. Run: python scripts/test.py to run tests")
    print("3. Start building the Chrome extension!")


if __name__ == "__main__":
    main()
