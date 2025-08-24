# IMS Backend - Django REST API

## Overview

This is the Django REST API backend for the Inventory Management System (IMS). It provides a comprehensive API for managing inventory, users, supermarkets, and multi-store operations.

## 🏗️ Architecture

### Django Apps Structure

```
backend/
├── ims_backend/          # Main Django project settings
├── accounts/             # User authentication & management
├── inventory/            # Product & inventory management
├── supermarkets/         # Store/supermarket management
├── notifications/        # Email notifications & reminders
├── pos_integration/      # POS system integration
├── file_processing/      # Excel/CSV import processing
├── analytics/            # Analytics and reporting
├── templates/            # Email templates
└── logs/                 # Application logs
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip
- Virtual environment (recommended)

### Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## 🔧 Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=sqlite:///db.sqlite3

# Security
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
```

## 📚 API Documentation

### Authentication Endpoints

```
POST /api/auth/register/     # User registration
POST /api/auth/login/        # User login
POST /api/auth/logout/       # User logout
POST /api/auth/refresh/      # Refresh JWT token
GET  /api/auth/user/         # Get current user
PUT  /api/auth/user/         # Update user profile
```

### Inventory Endpoints

```
GET    /api/inventory/products/              # List products
POST   /api/inventory/products/              # Create product
GET    /api/inventory/products/{id}/         # Get product
PUT    /api/inventory/products/{id}/         # Update product
DELETE /api/inventory/products/{id}/         # Delete product
POST   /api/inventory/products/bulk/         # Bulk create products
POST   /api/inventory/products/import/       # Import from Excel/CSV

GET    /api/inventory/categories/            # List categories
POST   /api/inventory/categories/            # Create category
GET    /api/inventory/suppliers/             # List suppliers
POST   /api/inventory/suppliers/             # Create supplier
```

### Supermarket Endpoints

```
GET    /api/supermarkets/                    # List supermarkets
POST   /api/supermarkets/                    # Create supermarket
GET    /api/supermarkets/{id}/               # Get supermarket
PUT    /api/supermarkets/{id}/               # Update supermarket
DELETE /api/supermarkets/{id}/               # Delete supermarket
POST   /api/supermarkets/{id}/sub-stores/    # Create sub-store
```

### File Processing Endpoints

```
POST   /api/file-processing/upload/         # Upload Excel/CSV file
GET    /api/file-processing/mappings/       # Get name-to-ID mappings
POST   /api/file-processing/convert/        # Convert names to IDs
```

### Notification Endpoints

```
GET    /api/notifications/                  # List notifications
POST   /api/notifications/send-reminders/   # Send reminder emails
GET    /api/notifications/settings/         # Get notification settings
PUT    /api/notifications/settings/         # Update notification settings
```

## 🏪 Multi-Store Support

The backend fully supports multi-store operations:

### Store Hierarchy
- **Main Store**: Primary store for each user
- **Sub-Stores**: Additional locations under main store
- **Store Isolation**: Products are properly isolated by store

### Multi-Store Features
- Store-specific product management
- Cross-store product copying/moving
- Store-level analytics and reporting
- Bulk operations across stores
- Store-specific user permissions

### API Examples

**Create Sub-Store:**
```json
POST /api/supermarkets/
{
  "name": "Downtown Branch",
  "is_sub_store": true,
  "parent_store_id": "main-store-id",
  "location": "123 Downtown Ave",
  "phone": "+1-555-0123",
  "email": "downtown@store.com"
}
```

**Copy Product to Multiple Stores:**
```json
POST /api/inventory/products/bulk-copy/
{
  "product_ids": ["prod-1", "prod-2"],
  "target_store_ids": ["store-2", "store-3"],
  "update_pricing": true
}
```

## 🔐 Authentication & Security

### JWT Authentication
- Access tokens (15 minutes expiry)
- Refresh tokens (7 days expiry)
- Automatic token refresh on frontend

### Security Features
- CORS protection
- Rate limiting
- Input validation
- SQL injection protection
- XSS protection
- CSRF protection

### User Management
- Email-based authentication
- User profiles with subscription tiers
- Password reset functionality
- Account activation via email

## 📊 Database Models

### Core Models

**User Model:**
```python
class User(AbstractUser):
    email = EmailField(unique=True)
    subscription_tier = CharField(choices=SUBSCRIPTION_CHOICES)
    is_email_verified = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

**Product Model:**
```python
class Product(models.Model):
    name = CharField(max_length=200)
    category = ForeignKey(Category)
    supplier = ForeignKey(Supplier)
    supermarket = ForeignKey(Supermarket)
    barcode = CharField(unique=True)
    price = DecimalField(max_digits=10, decimal_places=2)
    quantity = IntegerField()
    halal_certified = BooleanField(default=False)
    expiry_date = DateField(null=True, blank=True)
```

**Supermarket Model:**
```python
class Supermarket(models.Model):
    name = CharField(max_length=200)
    owner = ForeignKey(User)
    is_sub_store = BooleanField(default=False)
    parent_store = ForeignKey('self', null=True, blank=True)
    location = TextField()
    is_active = BooleanField(default=True)
```

## 🔄 Data Processing

### Excel/CSV Import
- Supports .xlsx, .xls, and .csv files
- Automatic column mapping
- Name-to-ID conversion for categories, suppliers, supermarkets
- Bulk product creation
- Error handling and validation

### File Processing Pipeline
1. **Upload**: File uploaded to server
2. **Parse**: Extract data from Excel/CSV
3. **Validate**: Check required fields and data types
4. **Map**: Convert names to database IDs
5. **Create**: Bulk create products
6. **Report**: Return success/error summary

## 📧 Notification System

### Email Notifications
- Low stock alerts
- Expiry date reminders
- Welcome emails
- Password reset emails
- Bulk operation summaries

### Reminder System
- Automated daily/weekly reminders
- Customizable notification preferences
- Email templates with branding
- Batch processing for performance

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### API Testing Scripts
- `test_api_auth.py` - Authentication flow testing
- `test_complete_auth_flow.py` - End-to-end auth testing
- `test_barcode_system.py` - Barcode generation testing
- `test_reminder_system.py` - Email notification testing

## 🚀 Deployment

### Production Settings
- Use `settings_production.py` for production
- Set `DEBUG=False`
- Configure proper database (PostgreSQL recommended)
- Set up static file serving
- Configure email backend
- Set up logging

### Deployment Platforms
- **Render**: Configured with `Procfile` and `requirements.txt`
- **Heroku**: Compatible with existing configuration
- **Railway**: Works with current setup
- **DigitalOcean**: App Platform compatible

### Environment Setup
```bash
# Production environment
pip install -r requirements-production.txt
python manage.py collectstatic
python manage.py migrate
```

## 📝 API Response Formats

### Success Response
```json
{
  "success": true,
  "data": {
    "id": "product-123",
    "name": "Sample Product",
    "price": 19.99
  },
  "message": "Product created successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid product data",
    "details": {
      "name": ["This field is required"],
      "price": ["Must be a positive number"]
    }
  }
}
```

### Pagination Response
```json
{
  "success": true,
  "data": {
    "results": [...],
    "count": 150,
    "next": "http://api.example.com/products/?page=2",
    "previous": null
  }
}
```

## 🔍 Monitoring & Logging

### Logging Configuration
- Application logs in `logs/django.log`
- Separate logs for different components
- Configurable log levels
- Log rotation for production

### Health Checks
```
GET /api/health/         # Basic health check
GET /api/health/db/      # Database connectivity
GET /api/health/email/   # Email service status
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style
- Follow PEP 8
- Use Black for code formatting
- Add docstrings to functions and classes
- Write tests for new features

## 📞 Support

For backend-specific issues:
- Check logs in `logs/django.log`
- Run diagnostic scripts in root directory
- Review API documentation
- Check database migrations

## 🔄 Version History

### v2.0.0 - Multi-Store Release
- ✅ Multi-store support
- ✅ Enhanced API endpoints
- ✅ Improved authentication
- ✅ Better error handling
- ✅ Comprehensive logging

### v1.0.0 - Initial Release
- ✅ Basic inventory management
- ✅ User authentication
- ✅ Excel import functionality
- ✅ Email notifications
- ✅ REST API endpoints

---

**Backend API Ready! 🚀**