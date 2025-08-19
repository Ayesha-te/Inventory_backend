# IMS Backend - Inventory Management System

A comprehensive Django REST API backend for inventory management with Excel/image processing, POS integration, and real-time notifications.

## 🚀 Features

### Core Features
- **User Authentication & Authorization** - JWT-based auth with 30-day token expiry
- **Multi-Supermarket Support** - Manage multiple stores/locations
- **Product Management** - Complete CRUD with categories, suppliers, barcodes
- **Inventory Tracking** - Stock movements, alerts, expiry management
- **File Processing** - Excel/CSV import and image OCR processing
- **POS Integration** - Square, Shopify, and custom API support
- **Analytics & Reporting** - Dashboard metrics and custom reports
- **Real-time Notifications** - Email, push, and in-app notifications

### Advanced Features
- **Halal Certification Tracking** - For halal product management
- **Barcode Generation & Scanning** - Multiple barcode format support
- **Automated Alerts** - Low stock, expiry, and out-of-stock notifications
- **Bulk Operations** - Import/export and batch updates
- **Multi-language Support** - Internationalization ready
- **Performance Monitoring** - System metrics and analytics
- **Task Queue** - Django-Q for background processing

## 🛠️ Technology Stack

- **Framework**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Task Queue**: Django-Q with Redis
- **File Processing**: Pandas, OpenPyXL, EasyOCR
- **Image Processing**: OpenCV, Pillow, Tesseract
- **Authentication**: JWT (Simple JWT)
- **API Documentation**: DRF Spectacular (OpenAPI 3.0)
- **Caching**: Redis
- **Storage**: Local/AWS S3 support

## 📋 Prerequisites

- Python 3.8+
- Redis Server
- Tesseract OCR
- PostgreSQL (for production)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
cd backend
python setup.py
```

### 2. Manual Setup (Alternative)
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

### 3. Start Services
```bash
# Start Django server
python manage.py runserver

# Start Django-Q worker (in another terminal)
python manage.py qcluster

# Start Redis (if not running)
redis-server
```

## 📁 Project Structure

```
backend/
├── ims_backend/           # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── accounts/             # User management
├── inventory/            # Product & inventory management
├── supermarkets/         # Store/location management
├── file_processing/      # Excel/image processing
├── pos_integration/      # POS system integration
├── analytics/            # Reports & analytics
├── notifications/        # Notification system
├── requirements.txt      # Python dependencies
├── setup.py             # Setup script
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Frontend
FRONTEND_URL=http://localhost:3000

# OCR
TESSERACT_CMD=tesseract
```

## 📚 API Documentation

Once the server is running, visit:
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/
- **Admin Panel**: http://localhost:8000/admin/

### Key API Endpoints

#### Authentication
- `POST /api/auth/token/` - Login
- `POST /api/auth/token/refresh/` - Refresh token
- `POST /api/accounts/register/` - Register user

#### Inventory
- `GET /api/inventory/products/` - List products
- `POST /api/inventory/products/` - Create product
- `GET /api/inventory/products/{id}/` - Get product details
- `POST /api/inventory/products/{id}/stock/` - Update stock

#### File Processing
- `POST /api/files/upload/` - Upload Excel/image files
- `GET /api/files/sessions/` - List upload sessions
- `POST /api/files/import/` - Import processed products

#### POS Integration
- `GET /api/pos/integrations/` - List POS integrations
- `POST /api/pos/integrations/{id}/sync/` - Trigger sync

## 🔄 File Processing

### Excel Import
Supports automatic column mapping for:
- Product name, barcode, category, supplier
- Pricing (cost, selling, current price)
- Inventory (quantity, min stock level)
- Product details (weight, origin, expiry date)
- Halal certification information

### Image Processing
Uses OCR to extract:
- Product names and descriptions
- Prices and barcodes
- Structured product information

## 🔌 POS Integration

### Supported Systems
- **Square POS** - Full product and inventory sync
- **Shopify** - Product catalog synchronization
- **Custom API** - Configurable endpoint integration

### Sync Features
- Automatic scheduled synchronization
- Manual sync triggers
- Bidirectional data flow
- Error handling and retry logic

## 📊 Analytics & Reporting

### Dashboard Metrics
- Total products and inventory value
- Low stock and expiry alerts
- Stock movement trends
- Category and supplier analytics

### Custom Reports
- Inventory reports
- Stock movement reports
- Expiry reports
- Supplier performance reports

## 🔔 Notifications

### Notification Types
- Low stock alerts
- Expiry warnings
- POS sync updates
- File processing status
- System notifications

### Delivery Channels
- In-app notifications
- Email notifications
- Push notifications (web)
- SMS notifications (configurable)

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deployment

### Production Settings
1. Set `DEBUG=False` in .env
2. Configure PostgreSQL database
3. Set up Redis server
4. Configure email settings
5. Set up static file serving
6. Configure CORS for frontend

### Docker Deployment
```bash
# Build image
docker build -t ims-backend .

# Run with docker-compose
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation
- Review the setup guide

## 🔄 Updates & Maintenance

### Regular Tasks
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Run migrations: `python manage.py migrate`
- Clear cache: `python manage.py clear_cache`
- Backup database regularly

### Monitoring
- Check Django-Q worker status
- Monitor Redis memory usage
- Review error logs
- Monitor API performance

---

**Happy Coding! 🎉**