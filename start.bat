@echo off
echo Starting IMS Backend Server...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Setup database
echo Setting up database...
python manage.py makemigrations
python manage.py migrate

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Start server
echo.
echo ========================================
echo IMS Backend Server Starting...
echo API: http://localhost:8000/api/
echo Admin: http://localhost:8000/admin/
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver