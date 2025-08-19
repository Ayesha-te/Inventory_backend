from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Notification(models.Model):
    """User notifications"""
    
    NOTIFICATION_TYPES = [
        ('LOW_STOCK', 'Low Stock Alert'),
        ('EXPIRY', 'Expiry Alert'),
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('POS_SYNC', 'POS Sync Update'),
        ('REPORT_READY', 'Report Ready'),
        ('FILE_PROCESSED', 'File Processed'),
        ('SYSTEM', 'System Notification'),
        ('WELCOME', 'Welcome Message'),
        ('SUBSCRIPTION', 'Subscription Update'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    
    # Notification content
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    
    # Related objects
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'product', 'report'
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Action data
    action_url = models.CharField(max_length=500, blank=True, null=True)
    action_data = models.JSONField(default=dict, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Delivery channels
    send_email = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)
    send_sms = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class NotificationTemplate(models.Model):
    """Templates for notifications"""
    
    name = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    
    # Template content
    title_template = models.CharField(max_length=255)
    message_template = models.TextField()
    email_subject_template = models.CharField(max_length=255, blank=True, null=True)
    email_body_template = models.TextField(blank=True, null=True)
    
    # Default settings
    default_priority = models.CharField(max_length=10, choices=Notification.PRIORITY_LEVELS, default='MEDIUM')
    default_send_email = models.BooleanField(default=False)
    default_send_push = models.BooleanField(default=True)
    default_send_sms = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'notification_type']
    
    def __str__(self):
        return f"{self.name} ({self.notification_type})"


class EmailNotification(models.Model):
    """Email notification tracking"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('BOUNCED', 'Bounced'),
    ]
    
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='email_notification')
    
    # Email details
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    opened_at = models.DateTimeField(blank=True, null=True)
    clicked_at = models.DateTimeField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Email to {self.to_email} - {self.status}"


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Global settings
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Specific notification types
    low_stock_alerts = models.BooleanField(default=True)
    expiry_alerts = models.BooleanField(default=True)
    out_of_stock_alerts = models.BooleanField(default=True)
    pos_sync_alerts = models.BooleanField(default=True)
    report_alerts = models.BooleanField(default=True)
    file_processing_alerts = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    
    # Timing preferences
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Frequency settings
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIATE', 'Immediate'),
            ('HOURLY', 'Hourly'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
        ],
        default='IMMEDIATE'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class NotificationDigest(models.Model):
    """Notification digests for batched delivery"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_digests')
    
    # Digest details
    digest_type = models.CharField(
        max_length=20,
        choices=[
            ('HOURLY', 'Hourly'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
        ]
    )
    
    # Content
    subject = models.CharField(max_length=255)
    content = models.TextField()
    notification_count = models.IntegerField(default=0)
    
    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # Period covered
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.digest_type} digest for {self.user.email}"


class PushNotificationDevice(models.Model):
    """Push notification device tokens"""
    
    DEVICE_TYPES = [
        ('WEB', 'Web Browser'),
        ('ANDROID', 'Android'),
        ('IOS', 'iOS'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_devices')
    
    # Device info
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_token = models.TextField(unique=True)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'device_token']
    
    def __str__(self):
        return f"{self.device_type} device for {self.user.email}"


class Reminder(models.Model):
    """Reminder system for various events"""
    
    REMINDER_TYPES = [
        ('EXPIRY', 'Product Expiry'),
        ('LOW_STOCK', 'Low Stock Alert'),
        ('REORDER', 'Reorder Point'),
        ('CUSTOM', 'Custom Reminder'),
        ('MAINTENANCE', 'System Maintenance'),
        ('REPORT', 'Report Generation'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    FREQUENCY_CHOICES = [
        ('ONCE', 'One Time'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='reminders', blank=True, null=True)
    
    # Reminder details
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Related object (e.g., product for expiry reminder)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Scheduling
    remind_at = models.DateTimeField()  # When to send the reminder
    target_date = models.DateTimeField(blank=True, null=True)  # The actual event date (e.g., expiry date)
    days_before = models.IntegerField(default=30)  # Days before target_date to remind
    
    # Recurrence
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ONCE')
    is_recurring = models.BooleanField(default=False)
    next_reminder = models.DateTimeField(blank=True, null=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # Django-Q task tracking
    task_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Email settings
    send_email = models.BooleanField(default=True)
    email_subject = models.CharField(max_length=255, blank=True, null=True)
    email_body = models.TextField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reminder_type', 'remind_at']),
            models.Index(fields=['status', 'remind_at']),
            models.Index(fields=['task_id']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.remind_at}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate remind_at if target_date and days_before are provided
        if self.target_date and self.days_before and not self.remind_at:
            from datetime import timedelta
            self.remind_at = self.target_date - timedelta(days=self.days_before)
        
        super().save(*args, **kwargs)


class ReminderLog(models.Model):
    """Log of reminder executions"""
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    ]
    
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name='logs')
    
    # Execution details
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Email tracking
    email_sent = models.BooleanField(default=False)
    email_recipient = models.EmailField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    # Task info
    task_id = models.CharField(max_length=100, blank=True, null=True)
    execution_time = models.FloatField(blank=True, null=True)  # Execution time in seconds
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.reminder.title} - {self.status} at {self.executed_at}"