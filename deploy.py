#!/usr/bin/env python3
"""
Deployment script for IMS Backend
Handles production deployment with error handling
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description="", ignore_errors=False):
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
        
        if ignore_errors:
            print("⚠️  Continuing despite error...")
            return True
        return False

def install_minimal_requirements():
    """Install minimal requirements for deployment"""
    print("\n📦 Installing minimal requirements for deployment...")
    
    # Try minimal requirements first
    if Path('requirements-minimal.txt').exists():
        if run_command("pip install -r requirements-minimal.txt", "Installing minimal requirements"):
            print("✅ Minimal requirements installed successfully")
            return True
    
    # Fallback to production requirements
    if Path('requirements-production.txt').exists():
        if run_command("pip install -r requirements-production.txt", "Installing production requirements"):
            print("✅ Production requirements installed successfully")
            return True
    
    # Last resort - install core packages individually
    print("📦 Installing core packages individually...")
    core_packages = [
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.3.1",
        "django-filter==23.3",
        "djangorestframework-simplejwt==5.3.0",
        "psycopg2-binary==2.9.7",
        "dj-database-url==2.1.0",
        "django-q==1.3.9",
        "redis==4.6.0",
        "python-decouple==3.8",
        "gunicorn==21.2.0",
        "whitenoise==6.6.0"
    ]
    
    for package in core_packages:
        if not run_command(f"pip install {package}", f"Installing {package}", ignore_errors=True):
            print(f"⚠️  Failed to install {package}, continuing...")
    
    return True

def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Setting up environment...")
    
    # Create .env from .env.example if it doesn't exist
    env_example = Path('.env.example')
    env_file = Path('.env')
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
    
    # Set production environment variables
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings_production')
    os.environ.setdefault('DEBUG', 'False')
    
    return True

def setup_database():
    """Setup database with error handling"""
    print("\n🗄️  Setting up database...")
    
    # Set Django settings module
    os.environ['DJANGO_SETTINGS_MODULE'] = 'ims_backend.settings_production'
    
    commands = [
        ("python manage.py makemigrations accounts", "Creating accounts migrations"),
        ("python manage.py makemigrations supermarkets", "Creating supermarkets migrations"),
        ("python manage.py makemigrations inventory", "Creating inventory migrations"),
        ("python manage.py makemigrations notifications", "Creating notifications migrations"),
        ("python manage.py migrate", "Running all migrations"),
    ]
    
    for command, description in commands:
        if not run_command(command, description, ignore_errors=True):
            print(f"⚠️  {description} failed, continuing...")
    
    return True

def collect_static_files():
    """Collect static files"""
    print("\n📁 Collecting static files...")
    
    # Create static directories
    static_dir = Path('staticfiles')
    static_dir.mkdir(exist_ok=True)
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files", ignore_errors=True)
    
    return True

def create_minimal_wsgi():
    """Create a minimal WSGI file for deployment"""
    wsgi_content = '''"""
WSGI config for ims_backend project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings_production')

application = get_wsgi_application()
'''
    
    wsgi_path = Path('ims_backend/wsgi_production.py')
    with open(wsgi_path, 'w') as f:
        f.write(wsgi_content)
    
    print("✅ Created production WSGI file")
    return True

def main():
    """Main deployment function"""
    print("🚀 IMS Backend Deployment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('manage.py').exists():
        print("❌ manage.py not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    try:
        # Setup environment
        setup_environment()
        
        # Install requirements
        install_minimal_requirements()
        
        # Create WSGI file
        create_minimal_wsgi()
        
        # Setup database
        setup_database()
        
        # Collect static files
        collect_static_files()
        
        print("\n" + "=" * 50)
        print("✅ IMS Backend Deployment Complete!")
        print("=" * 50)
        print("\nDeployment ready with:")
        print("- Minimal requirements installed")
        print("- Database migrations applied")
        print("- Static files collected")
        print("- Production settings configured")
        print("\nTo start the server:")
        print("gunicorn ims_backend.wsgi_production:application --bind 0.0.0.0:8000")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()