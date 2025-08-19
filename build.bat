@echo off
REM Build script for Windows deployment

echo 🚀 Starting build process...

REM Upgrade pip to latest version
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install wheel and setuptools first
echo 🔧 Installing build tools...
pip install wheel setuptools

REM Set pip to prefer binary wheels and avoid building from source
echo 📦 Installing requirements with binary preference...
pip install --only-binary=all -r requirements_deploy.txt
if %errorlevel% neq 0 (
    echo ⚠️ Some packages failed with binary-only, trying with fallback...
    pip install -r requirements_deploy.txt
)

REM Collect static files
echo 📁 Collecting static files...
python manage.py collectstatic --noinput

echo ✅ Build completed successfully!