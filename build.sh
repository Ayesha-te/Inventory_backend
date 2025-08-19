#!/bin/bash

# Build script for deployment platforms (Render, Heroku, etc.)
set -o errexit  # Exit on error

echo "🚀 Starting build process..."

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install wheel and setuptools first
echo "🔧 Installing build tools..."
pip install wheel setuptools

# Set pip to prefer binary wheels and avoid building from source
echo "📦 Installing requirements with binary preference..."
pip install --only-binary=all -r requirements_deploy.txt || {
    echo "⚠️ Some packages failed with binary-only, trying with fallback..."
    pip install -r requirements_deploy.txt
}

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Build completed successfully!"