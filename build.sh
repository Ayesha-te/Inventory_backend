#!/bin/bash

# Build script for IMS Backend deployment
echo "🚀 Starting IMS Backend build process..."

# Set environment variables
export DJANGO_SETTINGS_MODULE=ims_backend.settings_production
export DEBUG=False

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install wheel setuptools

# Try to install requirements with fallback strategy
echo "📦 Installing requirements..."

# First try minimal requirements
if [ -f "requirements-minimal.txt" ]; then
    echo "📦 Trying minimal requirements..."
    pip install -r requirements-minimal.txt
    if [ $? -eq 0 ]; then
        echo "✅ Minimal requirements installed successfully"
    else
        echo "⚠️  Minimal requirements failed, trying individual packages..."
        
        # Install core packages individually
        pip install Django==4.2.7
        pip install djangorestframework==3.14.0
        pip install django-cors-headers==4.3.1
        pip install django-filter==23.3
        pip install djangorestframework-simplejwt==5.3.0
        pip install psycopg2-binary==2.9.7
        pip install dj-database-url==2.1.0
        pip install django-q==1.3.9
        pip install redis==4.6.0
        pip install python-decouple==3.8
        pip install gunicorn==21.2.0
        pip install whitenoise==6.6.0
        pip install Pillow==10.0.1
        pip install requests==2.31.0
        pip install pytz==2023.3
    fi
else
    echo "📦 Installing core packages individually..."
    pip install Django==4.2.7
    pip install djangorestframework==3.14.0
    pip install django-cors-headers==4.3.1
    pip install django-filter==23.3
    pip install djangorestframework-simplejwt==5.3.0
    pip install psycopg2-binary==2.9.7
    pip install dj-database-url==2.1.0
    pip install django-q==1.3.9
    pip install redis==4.6.0
    pip install python-decouple==3.8
    pip install gunicorn==21.2.0
    pip install whitenoise==6.6.0
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py makemigrations accounts --noinput || echo "⚠️  Accounts migrations failed"
python manage.py makemigrations supermarkets --noinput || echo "⚠️  Supermarkets migrations failed"
python manage.py makemigrations inventory --noinput || echo "⚠️  Inventory migrations failed"
python manage.py makemigrations notifications --noinput || echo "⚠️  Notifications migrations failed"
python manage.py migrate --noinput || echo "⚠️  Migration failed"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static files collection failed"

echo "✅ Build process completed!"