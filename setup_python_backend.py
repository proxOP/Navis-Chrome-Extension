#!/usr/bin/env python3
"""
Setup script for Navis Python Backend
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_virtual_environment():
    """Create virtual environment for the backend"""
    backend_dir = Path("navis-backend")
    venv_dir = backend_dir / "venv"
    
    if venv_dir.exists():
        print("✅ Virtual environment already exists")
        return True
    
    backend_dir.mkdir(exist_ok=True)
    return run_command(
        f"python -m venv {venv_dir}",
        "Creating virtual environment"
    )

def get_activation_command():
    """Get the correct activation command for the platform"""
    if platform.system() == "Windows":
        return "navis-backend\\venv\\Scripts\\activate"
    else:
        return "source navis-backend/venv/bin/activate"

def install_dependencies():
    """Install Python dependencies"""
    backend_dir = Path("navis-backend")
    
    if platform.system() == "Windows":
        pip_command = "navis-backend\\venv\\Scripts\\pip"
    else:
        pip_command = "navis-backend/venv/bin/pip"
    
    return run_command(
        f"{pip_command} install -r navis-backend/requirements.txt",
        "Installing Python dependencies"
    )

def create_env_file():
    """Create .env file for configuration"""
    env_file = Path("navis-backend/.env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_content = """# Navis Backend Configuration

# OpenAI API Key (required for intent parsing and planning)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Anthropic API Key (alternative to OpenAI)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Backend Configuration
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

# Logging Level
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("⚠️  Please edit navis-backend/.env and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_chrome_driver():
    """Check if Chrome is available for Selenium"""
    try:
        import subprocess
        if platform.system() == "Windows":
            subprocess.run(["where", "chrome"], check=True, capture_output=True)
        else:
            subprocess.run(["which", "google-chrome"], check=True, capture_output=True)
        print("✅ Chrome browser detected")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Chrome browser not found - Selenium may not work properly")
        print("   Please install Google Chrome for DOM analysis features")
        return False

def create_startup_scripts():
    """Create startup scripts for easy running"""
    
    # Windows batch file
    windows_script = """@echo off
echo Starting Navis Backend...
cd navis-backend
call venv\\Scripts\\activate
python main.py
pause
"""
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting Navis Backend..."
cd navis-backend
source venv/bin/activate
python main.py
"""
    
    try:
        with open("start_navis_backend.bat", 'w') as f:
            f.write(windows_script)
        
        with open("start_navis_backend.sh", 'w') as f:
            f.write(unix_script)
        
        # Make shell script executable on Unix
        if platform.system() != "Windows":
            os.chmod("start_navis_backend.sh", 0o755)
        
        print("✅ Created startup scripts")
        return True
    except Exception as e:
        print(f"❌ Failed to create startup scripts: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Navis Python Backend")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Setup steps
    steps = [
        create_virtual_environment,
        install_dependencies,
        create_env_file,
        check_chrome_driver,
        create_startup_scripts
    ]
    
    for step in steps:
        if not step():
            print(f"\n❌ Setup failed at step: {step.__name__}")
            return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit navis-backend/.env and add your OpenAI API key")
    print("2. Run the backend:")
    
    if platform.system() == "Windows":
        print("   - Double-click start_navis_backend.bat")
        print("   - Or run: navis-backend\\venv\\Scripts\\activate && cd navis-backend && python main.py")
    else:
        print("   - Run: ./start_navis_backend.sh")
        print("   - Or run: source navis-backend/venv/bin/activate && cd navis-backend && python main.py")
    
    print("3. Load the Chrome extension from the 'extension' folder")
    print("4. Start using Navis!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)