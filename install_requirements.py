#!/usr/bin/env python3
"""
Safe requirements installer for IMS Backend
This script installs requirements in a way that avoids build issues
"""

import subprocess
import sys
import os

def run_pip_command(command, description=""):
    """Run a pip command safely"""
    print(f"\n{'='*50}")
    print(f"Running: {description or command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return False

def install_requirements():
    """Install requirements in stages to avoid build issues"""
    
    # Stage 1: Core Django packages
    core_packages = [
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.3.1",
        "django-filter==23.3",
        "python-decouple==3.8",
        "python-dotenv==1.0.0",
        "dj-database-url==2.1.0"
    ]
    
    print("📦 Installing core Django packages...")
    for package in core_packages:
        if not run_pip_command(f"pip install {package}", f"Installing {package}"):
            print(f"❌ Failed to install {package}")
            return False
    
    # Stage 2: Database and authentication
    auth_packages = [
        "djangorestframework-simplejwt==5.3.0",
        "django-allauth==0.57.0",
        "psycopg2-binary==2.9.7"
    ]
    
    print("\n🔐 Installing authentication packages...")
    for package in auth_packages:
        if not run_pip_command(f"pip install {package}", f"Installing {package}"):
            print(f"⚠️ Warning: Failed to install {package}")
    
    # Stage 3: File handling (avoiding problematic packages)
    file_packages = [
        "Pillow==10.0.1",
        "pandas==2.0.3",
        "openpyxl==3.1.2",
        "xlrd==2.0.1"
    ]
    
    print("\n📁 Installing file handling packages...")
    for package in file_packages:
        if not run_pip_command(f"pip install {package}", f"Installing {package}"):
            print(f"⚠️ Warning: Failed to install {package}")
    
    # Stage 4: Install remaining packages from requirements_fixed.txt
    print("\n📦 Installing remaining packages...")
    if not run_pip_command("pip install -r requirements_fixed.txt", "Installing remaining requirements"):
        print("⚠️ Some packages may have failed to install")
    
    print("\n✅ Installation process completed!")
    print("\nNote: If some packages failed, you can install them individually:")
    print("- For OCR: pip install easyocr (may require additional setup)")
    print("- For computer vision: pip install opencv-python")
    print("- Check the error messages above for specific issues")

def main():
    """Main installation function"""
    print("🚀 IMS Backend Requirements Installer")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ Warning: You're not in a virtual environment!")
        print("It's recommended to use a virtual environment.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            sys.exit(1)
    
    # Upgrade pip first
    print("📦 Upgrading pip...")
    run_pip_command("pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    install_requirements()

if __name__ == "__main__":
    main()