from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class DashboardMetrics(models.Model):
    """Daily dashboard metrics for supermarkets"""
    
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    
    # Product metrics
    total_products = models.IntegerField(default=0)
    active_products = models.IntegerField(default=0)
    low_stock_products = models.IntegerField(default=0)
    out_of_stock_products = models.IntegerField(default=0)
    expired_products = models.IntegerField(default=0)
    expiring_soon_products = models.IntegerField(default=0)
    
    # Inventory value
    total_inventory_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_cost_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    potential_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Stock movements
    stock_in_count = models.IntegerField(default=0)
    stock_out_count = models.IntegerField(default=0)
    adjustments_count = models.IntegerField(default=0)
    
    # Categories and suppliers
    active_categories = models.IntegerField(default=0)
    active_suppliers = models.IntegerField(default=0)
    
    # Alerts
    total_alerts = models.IntegerField(default=0)
    unread_alerts = models.IntegerField(default=0)
    critical_alerts = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['supermarket', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.supermarket.name} on {self.date}"


class ReportTemplate(models.Model):
    """Report templates for generating custom reports"""
    
    REPORT_TYPES = [
        ('INVENTORY', 'Inventory Report'),
        ('SALES', 'Sales Report'),
        ('STOCK_MOVEMENT', 'Stock Movement Report'),
        ('EXPIRY', 'Expiry Report'),
        ('SUPPLIER', 'Supplier Report'),
        ('CATEGORY', 'Category Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
        ('ON_DEMAND', 'On Demand'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_templates')
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='report_templates')
    
    # Report configuration
    filters = models.JSONField(default=dict, blank=True)
    columns = models.JSONField(default=list, blank=True)
    sorting = models.JSONField(default=dict, blank=True)
    grouping = models.JSONField(default=dict, blank=True)
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ON_DEMAND')
    is_scheduled = models.BooleanField(default=False)
    next_run = models.DateTimeField(blank=True, null=True)
    
    # Email settings
    email_recipients = models.JSONField(default=list, blank=True)
    email_subject = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.report_type}"


class GeneratedReport(models.Model):
    """Generated reports"""
    
    STATUS_CHOICES = [
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='generated_reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    
    # Report details
    title = models.CharField(max_length=255)
    date_from = models.DateField()
    date_to = models.DateField()
    
    # Generation info
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATING')
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    
    # Statistics
    total_records = models.IntegerField(default=0)
    generation_time = models.DurationField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class UserActivity(models.Model):
    """Track user activities for analytics"""
    
    ACTIVITY_TYPES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PRODUCT_CREATE', 'Product Created'),
        ('PRODUCT_UPDATE', 'Product Updated'),
        ('PRODUCT_DELETE', 'Product Deleted'),
        ('STOCK_UPDATE', 'Stock Updated'),
        ('REPORT_GENERATE', 'Report Generated'),
        ('FILE_UPLOAD', 'File Uploaded'),
        ('POS_SYNC', 'POS Sync'),
        ('ALERT_VIEW', 'Alert Viewed'),
        ('SETTINGS_UPDATE', 'Settings Updated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='activities', blank=True, null=True)
    
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"


class PerformanceMetrics(models.Model):
    """System performance metrics"""
    
    date = models.DateField()
    
    # API performance
    avg_response_time = models.FloatField(default=0.0)
    total_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    # Database performance
    avg_query_time = models.FloatField(default=0.0)
    total_queries = models.IntegerField(default=0)
    slow_queries = models.IntegerField(default=0)
    
    # File processing
    files_processed = models.IntegerField(default=0)
    processing_errors = models.IntegerField(default=0)
    avg_processing_time = models.FloatField(default=0.0)
    
    # POS sync
    pos_syncs = models.IntegerField(default=0)
    pos_sync_errors = models.IntegerField(default=0)
    
    # User activity
    active_users = models.IntegerField(default=0)
    new_registrations = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Performance metrics for {self.date}"