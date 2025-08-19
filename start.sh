#!/bin/bash

echo "Starting IMS Backend Server..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Setup database
echo "Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo
echo "========================================"
echo "IMS Backend Server Starting..."
echo "API: http://localhost:8000/api/"
echo "Admin: http://localhost:8000/admin/"
echo "========================================"
echo
echo "Press Ctrl+C to stop the server"
echo

python manage.py runserver