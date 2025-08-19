#!/usr/bin/env python3
"""
IMS Backend Project Setup Script
This script sets up the Django backend for the Inventory Management System
Note: This is a project setup script, not a package setup file.
"""

__version__ = "1.0.0"

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Running: {description or command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def create_env_file():
    """Create .env file from .env.example"""
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
        print("⚠️  Please update the .env file with your actual configuration values")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ .env.example file not found")

def setup_database():
    """Setup database"""
    print("\n🗄️  Setting up database...")
    
    commands = [
        ("python manage.py makemigrations", "Creating migrations"),
        ("python manage.py migrate", "Running migrations"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def create_superuser():
    """Create superuser"""
    print("\n👤 Creating superuser...")
    print("Please enter superuser details:")
    
    if not run_command("python manage.py createsuperuser", "Creating superuser"):
        print("⚠️  Superuser creation skipped or failed")

def collect_static():
    """Collect static files"""
    print("\n📁 Collecting static files...")
    run_command("python manage.py collectstatic --noinput", "Collecting static files")

def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing Python requirements...")
    
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Requirements installed successfully")
    return True

def setup_redis():
    """Setup Redis for Django-Q"""
    print("\n🔴 Redis Setup Information")
    print("Django-Q requires Redis for task queue management.")
    print("Please ensure Redis is installed and running:")
    print("- Windows: Download from https://github.com/microsoftarchive/redis/releases")
    print("- macOS: brew install redis && brew services start redis")
    print("- Linux: sudo apt-get install redis-server")
    print("- Docker: docker run -d -p 6379:6379 redis:alpine")

def setup_ocr():
    """Setup OCR dependencies"""
    print("\n👁️  OCR Setup Information")
    print("For image processing, you need Tesseract OCR:")
    print("- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    print("- macOS: brew install tesseract")
    print("- Linux: sudo apt-get install tesseract-ocr")
    print("- Update TESSERACT_CMD in .env if needed")

def main():
    """Main setup function"""
    print("🚀 IMS Backend Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('manage.py').exists():
        print("❌ manage.py not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed at requirements installation")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Setup failed at database setup")
        sys.exit(1)
    
    # Create superuser
    create_superuser()
    
    # Collect static files
    collect_static()
    
    # Setup information
    setup_redis()
    setup_ocr()
    
    print("\n" + "=" * 50)
    print("✅ IMS Backend Setup Complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Update .env file with your configuration")
    print("2. Ensure Redis is running")
    print("3. Install Tesseract OCR for image processing")
    print("4. Start the development server: python manage.py runserver")
    print("5. Start Django-Q worker: python manage.py qcluster")
    print("\nAPI will be available at: http://localhost:8000/api/")
    print("Admin panel: http://localhost:8000/admin/")

if __name__ == "__main__":
    main()