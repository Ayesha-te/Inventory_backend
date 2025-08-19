# Django IMS Backend - Deployment Guide

## 🚨 Build Error Fix

If you're encountering the `KeyError: '__version__'` error during deployment, this is caused by problematic packages in the requirements.txt file. Here's how to fix it:

## 🔧 Quick Fix

### Option 1: Use Minimal Requirements (Recommended)

Replace your `requirements.txt` with the minimal requirements:

```bash
# Copy the minimal requirements
cp requirements-minimal.txt requirements.txt
```

### Option 2: Use the Deployment Script

Run the deployment script that handles errors gracefully:

```bash
python deploy.py
```

### Option 3: Manual Build Process

If you're on a platform like Render, Heroku, or similar:

1. **Use the build script**:
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

2. **Or install packages individually**:
   ```bash
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
   ```

## 📋 Deployment Files Created

1. **requirements-minimal.txt** - Core packages only
2. **requirements-production.txt** - Production-ready packages
3. **settings_production.py** - Production Django settings
4. **deploy.py** - Automated deployment script
5. **build.sh** - Build script for deployment platforms
6. **Procfile** - Process file for Heroku/Render
7. **runtime.txt** - Python version specification

## 🚀 Platform-Specific Instructions

### Render.com

1. **Build Command**:
   ```bash
   ./build.sh
   ```

2. **Start Command**:
   ```bash
   gunicorn ims_backend.wsgi_production:application
   ```

3. **Environment Variables**:
   ```
   DJANGO_SETTINGS_MODULE=ims_backend.settings_production
   DEBUG=False
   DATABASE_URL=your_database_url
   SECRET_KEY=your_secret_key
   ALLOWED_HOSTS=your_domain.com
   ```

### Heroku

1. **Procfile** (already created):
   ```
   web: gunicorn ims_backend.wsgi_production:application --bind 0.0.0.0:$PORT
   worker: python manage.py qcluster
   ```

2. **Environment Variables**:
   ```bash
   heroku config:set DJANGO_SETTINGS_MODULE=ims_backend.settings_production
   heroku config:set DEBUG=False
   heroku config:set SECRET_KEY=your_secret_key
   ```

### Railway

1. **Build Command**:
   ```bash
   pip install -r requirements-minimal.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```

2. **Start Command**:
   ```bash
   gunicorn ims_backend.wsgi_production:application --bind 0.0.0.0:$PORT
   ```

## 🔍 Troubleshooting

### Common Issues and Solutions

1. **Build fails with version errors**:
   - Use `requirements-minimal.txt` instead of `requirements.txt`
   - Install packages individually as shown above

2. **Database connection errors**:
   - Ensure `DATABASE_URL` environment variable is set
   - Check database credentials and connectivity

3. **Static files not loading**:
   - Run `python manage.py collectstatic --noinput`
   - Ensure `STATIC_ROOT` is properly configured

4. **Redis connection errors**:
   - Ensure Redis is available (most platforms provide Redis add-ons)
   - Update `REDIS_URL` environment variable

5. **Import errors for disabled apps**:
   - The production settings disable problematic apps by default
   - Re-enable them only after installing their dependencies

## 📦 Package Issues

The following packages are known to cause build issues and are excluded from minimal requirements:

- `easyocr` - Heavy dependencies, complex build process
- `opencv-python` - Large package with system dependencies
- `pytesseract` - Requires system-level Tesseract installation
- `scipy` - Heavy scientific computing package
- `numpy` (newer versions) - Can have build issues

## 🎯 Minimal Feature Set

The minimal deployment includes:

✅ **Core Django functionality**
✅ **REST API endpoints**
✅ **Authentication system**
✅ **Database operations**
✅ **Reminder system** (fully functional)
✅ **Basic inventory management**
✅ **User management**
✅ **Django admin**

❌ **OCR/Image processing** (requires additional setup)
❌ **Advanced file processing** (requires additional packages)
❌ **POS integrations** (requires API keys and setup)

## 🔄 Adding Features Later

After successful deployment, you can add features incrementally:

1. **Deploy with minimal requirements first**
2. **Verify core functionality works**
3. **Add packages one by one**:
   ```bash
   pip install easyocr
   # Test deployment
   pip install opencv-python
   # Test deployment
   # etc.
   ```

## 🌐 Environment Variables

Required environment variables for production:

```bash
# Core Django
DJANGO_SETTINGS_MODULE=ims_backend.settings_production
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis (for Django-Q)
REDIS_URL=redis://user:password@host:port/0

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# CORS (optional)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 🧪 Testing Deployment

After deployment, test these endpoints:

1. **Health check**: `GET /api/`
2. **Admin panel**: `/admin/`
3. **API documentation**: `/api/schema/swagger-ui/`
4. **Reminder endpoints**: `/api/notifications/reminders/`

## 📞 Support

If you continue to have deployment issues:

1. Check the deployment logs for specific error messages
2. Ensure all environment variables are set correctly
3. Verify database connectivity
4. Test with minimal requirements first
5. Add features incrementally after basic deployment works

The reminder system will work perfectly with the minimal requirements - all core functionality is preserved!