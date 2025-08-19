# Django Reminder System Documentation

## Overview

This reminder system is built using Django's built-in functions and Django-Q for task scheduling (no Celery required). It provides a comprehensive solution for creating, managing, and executing reminders with email notifications.

## Features

- ✅ **30-day advance reminders** (configurable)
- ✅ **Email notifications** with HTML templates
- ✅ **REST API endpoints** for full CRUD operations
- ✅ **Django-Q integration** for reliable task scheduling
- ✅ **Recurring reminders** support
- ✅ **Multiple reminder types** (Expiry, Low Stock, Custom, etc.)
- ✅ **Comprehensive logging** and error handling
- ✅ **Django Admin integration**
- ✅ **Bulk operations** for creating multiple reminders

## Architecture

### Models

1. **Reminder** - Main reminder model with scheduling and metadata
2. **ReminderLog** - Execution logs for tracking and debugging
3. **Notification** - In-app notifications (existing, extended)
4. **NotificationPreference** - User notification preferences

### Services

- **ReminderService** - Core business logic for reminder management
- **Django-Q Tasks** - Background task execution
- **Email Templates** - HTML email formatting

## Installation & Setup

### 1. Dependencies

The system uses these packages (already in your requirements.txt):
```
Django==4.2.7
djangorestframework==3.14.0
django-q==1.3.9
redis==5.0.1
```

### 2. Django Settings

Your settings are already configured with:
```python
# Django-Q Configuration
Q_CLUSTER = {
    'name': 'ims_backend',
    'workers': 4,
    'recycle': 500,
    'timeout': 60,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
    }
}
```

### 3. Start Django-Q Cluster

To process reminders, start the Django-Q cluster:
```bash
python manage.py qcluster
```

## API Endpoints

### Base URL: `/api/notifications/`

### Reminder Endpoints

#### 1. List Reminders
```
GET /api/notifications/reminders/
```

**Query Parameters:**
- `status` - Filter by status (ACTIVE, COMPLETED, CANCELLED, FAILED)
- `type` - Filter by reminder type (EXPIRY, LOW_STOCK, CUSTOM, etc.)
- `start_date` - Filter reminders from date (ISO format)
- `end_date` - Filter reminders to date (ISO format)
- `upcoming=true` - Show only upcoming active reminders

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/notifications/reminders/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid-here",
      "title": "Product Expiry Alert: Milk",
      "reminder_type": "EXPIRY",
      "status": "ACTIVE",
      "remind_at": "2024-01-15T10:00:00Z",
      "target_date": "2024-02-14T00:00:00Z",
      "days_before": 30,
      "is_sent": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### 2. Create Reminder
```
POST /api/notifications/reminders/create/
```

**Request Body:**
```json
{
  "reminder_type": "EXPIRY",
  "title": "Product Expiry Alert: Bread",
  "description": "Bread will expire soon",
  "target_date": "2024-02-14T00:00:00Z",
  "days_before": 30,
  "send_email": true,
  "email_subject": "Urgent: Bread Expiring Soon",
  "metadata": {
    "product_name": "Bread",
    "product_id": "123"
  }
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "title": "Product Expiry Alert: Bread",
  "reminder_type": "EXPIRY",
  "status": "ACTIVE",
  "remind_at": "2024-01-15T00:00:00Z",
  "target_date": "2024-02-14T00:00:00Z",
  "days_before": 30,
  "task_id": "django-q-task-id",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 3. Get Reminder Details
```
GET /api/notifications/reminders/{id}/
```

#### 4. Update Reminder
```
PUT /api/notifications/reminders/{id}/
PATCH /api/notifications/reminders/{id}/
```

#### 5. Delete/Cancel Reminder
```
DELETE /api/notifications/reminders/{id}/
```

### Expiry Reminder Shortcuts

#### 1. Create Single Expiry Reminder
```
POST /api/notifications/reminders/expiry/create/
```

**Request Body:**
```json
{
  "product_name": "Milk",
  "expiry_date": "2024-02-14T00:00:00Z",
  "days_before": 30,
  "supermarket_id": "uuid-optional",
  "product_id": "123-optional",
  "custom_message": "Custom reminder message"
}
```

#### 2. Create Bulk Expiry Reminders
```
POST /api/notifications/reminders/expiry/bulk-create/
```

**Request Body:**
```json
{
  "products": [
    {
      "product_name": "Milk",
      "expiry_date": "2024-02-14T00:00:00Z",
      "days_before": 30,
      "product_id": "123"
    },
    {
      "product_name": "Bread",
      "expiry_date": "2024-02-10T00:00:00Z",
      "days_before": 7,
      "product_id": "124"
    }
  ]
}
```

### Statistics & Monitoring

#### 1. Reminder Statistics
```
GET /api/notifications/reminders/stats/
```

**Response:**
```json
{
  "total_reminders": 150,
  "active_reminders": 45,
  "completed_reminders": 90,
  "cancelled_reminders": 10,
  "failed_reminders": 5,
  "upcoming_reminders": 25,
  "overdue_reminders": 3,
  "expiry_reminders": 80,
  "low_stock_reminders": 40,
  "custom_reminders": 30,
  "reminders_sent_today": 5,
  "reminders_sent_this_week": 25,
  "reminders_sent_this_month": 100
}
```

#### 2. Upcoming Reminders
```
GET /api/notifications/reminders/upcoming/?days=7
```

#### 3. Reminder Execution Logs
```
GET /api/notifications/reminders/logs/
```

**Query Parameters:**
- `reminder_id` - Filter by specific reminder
- `status` - Filter by execution status (SUCCESS, FAILED, SKIPPED)

## Usage Examples

### Python/Django Code

```python
from notifications.services import ReminderService
from datetime import datetime, timedelta
from django.utils import timezone

# Create a simple expiry reminder
reminder = ReminderService.create_expiry_reminder(
    user=request.user,
    product_name="Milk",
    expiry_date=timezone.now() + timedelta(days=45),
    days_before=30
)

# Create a custom reminder
reminder = ReminderService.create_reminder(
    user=request.user,
    reminder_type='CUSTOM',
    title='Monthly Inventory Check',
    description='Time to perform monthly inventory audit',
    remind_at=timezone.now() + timedelta(days=7),
    frequency='MONTHLY',
    is_recurring=True
)

# Get user's upcoming reminders
upcoming = ReminderService.get_user_reminders(
    user=request.user,
    status='ACTIVE'
)
```

### JavaScript/Frontend

```javascript
// Create expiry reminder
const createExpiryReminder = async (productData) => {
  const response = await fetch('/api/notifications/reminders/expiry/create/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      product_name: productData.name,
      expiry_date: productData.expiryDate,
      days_before: 30,
      product_id: productData.id
    })
  });
  
  return response.json();
};

// Get upcoming reminders
const getUpcomingReminders = async (days = 7) => {
  const response = await fetch(
    `/api/notifications/reminders/upcoming/?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return response.json();
};

// Get reminder statistics
const getReminderStats = async () => {
  const response = await fetch('/api/notifications/reminders/stats/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return response.json();
};
```

## Email Templates

The system includes HTML email templates located at:
`templates/notifications/reminder_email.html`

### Customizing Email Templates

You can customize the email template by modifying the HTML file. The template receives these context variables:

- `reminder` - The reminder object
- `user` - The user object
- `target_date` - The target date (if applicable)

## Management Commands

### Clean Up Old Reminders

```bash
# Clean up reminders older than 90 days (default)
python manage.py cleanup_reminders

# Clean up reminders older than 30 days
python manage.py cleanup_reminders --days 30

# Dry run to see what would be deleted
python manage.py cleanup_reminders --dry-run
```

## Django Admin

The reminder system is fully integrated with Django Admin:

1. **Reminders** - View, edit, and manage all reminders
2. **Reminder Logs** - View execution history and debug issues
3. **Notification Preferences** - Manage user preferences
4. **Notification Templates** - Create reusable templates

### Admin Actions

- **Cancel Reminders** - Bulk cancel selected reminders
- **Activate Reminders** - Bulk activate cancelled reminders

## Monitoring & Troubleshooting

### 1. Check Django-Q Status

```bash
# View Django-Q admin interface
python manage.py qmonitor
```

### 2. View Reminder Logs

```python
from notifications.models import ReminderLog

# Get recent failed executions
failed_logs = ReminderLog.objects.filter(
    status='FAILED'
).order_by('-executed_at')[:10]

for log in failed_logs:
    print(f"Reminder: {log.reminder.title}")
    print(f"Error: {log.error_message}")
    print("---")
```

### 3. Check Scheduled Tasks

```python
from django_q.models import Schedule

# View scheduled reminder tasks
scheduled_tasks = Schedule.objects.filter(
    name__startswith='reminder_'
)

for task in scheduled_tasks:
    print(f"Task: {task.name}")
    print(f"Next run: {task.next_run}")
    print("---")
```

## Error Handling

The system includes comprehensive error handling:

1. **Failed Reminders** - Marked as FAILED status with error logs
2. **Email Failures** - Logged but don't prevent notification creation
3. **Scheduling Failures** - Logged with detailed error messages
4. **Retry Logic** - Built into Django-Q for transient failures

## Performance Considerations

1. **Indexing** - Database indexes on frequently queried fields
2. **Pagination** - All list endpoints support pagination
3. **Bulk Operations** - Efficient bulk creation for multiple reminders
4. **Background Processing** - All heavy operations run in background
5. **Cleanup** - Regular cleanup of old logs and completed reminders

## Security

1. **Authentication** - All endpoints require authentication
2. **Authorization** - Users can only access their own reminders
3. **Input Validation** - Comprehensive validation on all inputs
4. **SQL Injection Protection** - Django ORM prevents SQL injection
5. **XSS Protection** - HTML email templates are properly escaped

## Testing

### Unit Tests

```python
from django.test import TestCase
from notifications.services import ReminderService
from django.contrib.auth import get_user_model

class ReminderServiceTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass'
        )
    
    def test_create_expiry_reminder(self):
        reminder = ReminderService.create_expiry_reminder(
            user=self.user,
            product_name='Test Product',
            expiry_date=timezone.now() + timedelta(days=45),
            days_before=30
        )
        
        self.assertEqual(reminder.reminder_type, 'EXPIRY')
        self.assertEqual(reminder.status, 'ACTIVE')
        self.assertIsNotNone(reminder.task_id)
```

### API Tests

```python
from rest_framework.test import APITestCase
from rest_framework import status

class ReminderAPITest(APITestCase):
    def test_create_reminder(self):
        self.client.force_authenticate(user=self.user)
        
        data = {
            'reminder_type': 'CUSTOM',
            'title': 'Test Reminder',
            'remind_at': (timezone.now() + timedelta(days=1)).isoformat()
        }
        
        response = self.client.post('/api/notifications/reminders/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

## Deployment Notes

1. **Redis** - Ensure Redis is running for Django-Q
2. **Django-Q Cluster** - Start qcluster process in production
3. **Email Settings** - Configure SMTP settings for email delivery
4. **Timezone** - Set appropriate timezone in Django settings
5. **Logging** - Configure logging for production monitoring

## Future Enhancements

Potential improvements for the system:

1. **SMS Notifications** - Add SMS delivery option
2. **Push Notifications** - Web push notifications
3. **Webhook Support** - HTTP callbacks for reminder events
4. **Advanced Scheduling** - Cron-like scheduling expressions
5. **Reminder Templates** - Predefined reminder templates
6. **Analytics Dashboard** - Visual analytics for reminder performance
7. **Multi-language Support** - Internationalization for emails
8. **Attachment Support** - File attachments in reminder emails

---

This reminder system provides a robust, scalable solution for managing reminders in your Django application without requiring Celery. It leverages Django's built-in capabilities and Django-Q for reliable background task processing.