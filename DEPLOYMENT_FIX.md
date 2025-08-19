# Deployment Fix Guide

## Issues Fixed

### 1. Python Version Mismatch
- **Problem**: `runtime.txt` specified Python 3.10.14, but Render was using Python 3.13.4
- **Fix**: Updated `runtime.txt` to use Python 3.11.9 for better compatibility

### 2. Pillow Compatibility Issue
- **Problem**: Pillow 10.0.1 had build issues with Python 3.13
- **Fix**: Updated Pillow to version 10.4.0 which has better Python 3.11+ support

### 3. Missing Gunicorn Version
- **Problem**: `gunicorn` was listed without version pinning
- **Fix**: Added `gunicorn==21.2.0` with proper version

### 4. Package Version Updates
Updated several packages for better Python 3.11 compatibility:
- `redis==5.0.1` (was 4.6.0)
- `boto3==1.34.0` (was 1.29.7)
- `cryptography==42.0.8` (was 41.0.7)

### 5. Missing WSGI Production File
- **Problem**: Procfile referenced `wsgi_production.py` which didn't exist
- **Fix**: Created `ims_backend/wsgi_production.py` file

## Files Modified

1. `runtime.txt` - Updated Python version
2. `requirements.txt` - Updated package versions
3. `requirements-deploy.txt` - Created minimal deployment requirements
4. `ims_backend/wsgi_production.py` - Created production WSGI file

## Deployment Steps

1. **Use the fixed requirements**: The build script (`build.sh`) will use `requirements_deploy.txt`
2. **Environment Variables**: Ensure these are set in Render:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app-name.onrender.com`

3. **Build Command**: Use the existing build script:
   ```bash
   ./build.sh
   ```

4. **Start Command**: The Procfile is already configured:
   ```
   web: gunicorn ims_backend.wsgi_production:application --bind 0.0.0.0:$PORT
   ```

## Alternative Deployment Strategy

If you still encounter issues, try deploying with minimal requirements first:

1. Temporarily rename `requirements.txt` to `requirements-full.txt`
2. Rename `requirements-deploy.txt` to `requirements.txt`
3. Deploy with minimal dependencies
4. Once successful, gradually add back other dependencies

## Common Issues and Solutions

### If Pillow still fails:
```bash
# In build script, add before pip install:
export PILLOW_VERSION=10.4.0
pip install --upgrade Pillow==$PILLOW_VERSION
```

### If psycopg2-binary fails:
```bash
# Alternative: use psycopg2 instead
pip install psycopg2==2.9.7
```

### If Redis connection fails:
- Ensure Redis URL is properly configured in environment variables
- Check if Redis service is available on your hosting platform