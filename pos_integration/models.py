from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class POSSystem(models.Model):
    """POS System configurations"""
    
    POS_TYPES = [
        ('SQUARE', 'Square'),
        ('SHOPIFY', 'Shopify'),
        ('CUSTOM', 'Custom API'),
    ]
    
    name = models.CharField(max_length=100)
    pos_type = models.CharField(max_length=20, choices=POS_TYPES)
    api_endpoint = models.URLField()
    api_version = models.CharField(max_length=20, default='v1')
    documentation_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.pos_type})"


class POSIntegration(models.Model):
    """POS Integration for supermarkets"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ERROR', 'Error'),
        ('SYNCING', 'Syncing'),
    ]
    
    supermarket = models.OneToOneField('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='pos_integration')
    pos_system = models.ForeignKey(POSSystem, on_delete=models.CASCADE)
    
    # API Credentials
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    store_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Configuration
    auto_sync_enabled = models.BooleanField(default=True)
    sync_interval = models.IntegerField(default=60, help_text="Minutes between syncs")
    sync_products = models.BooleanField(default=True)
    sync_inventory = models.BooleanField(default=True)
    sync_prices = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INACTIVE')
    last_sync = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.supermarket.name} - {self.pos_system.name}"


class POSSyncLog(models.Model):
    """Log POS synchronization activities"""
    
    SYNC_TYPES = [
        ('FULL', 'Full Sync'),
        ('INCREMENTAL', 'Incremental Sync'),
        ('PRODUCT', 'Product Sync'),
        ('INVENTORY', 'Inventory Sync'),
        ('PRICE', 'Price Sync'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('PARTIAL', 'Partial Success'),
        ('FAILED', 'Failed'),
    ]
    
    pos_integration = models.ForeignKey(POSIntegration, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Statistics
    total_items = models.IntegerField(default=0)
    successful_items = models.IntegerField(default=0)
    failed_items = models.IntegerField(default=0)
    
    # Details
    error_message = models.TextField(blank=True, null=True)
    sync_details = models.JSONField(default=dict, blank=True)
    
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    duration = models.DurationField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.pos_integration.supermarket.name} - {self.sync_type} - {self.status}"