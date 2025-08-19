from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()


class UploadSession(models.Model):
    """Track file upload sessions"""
    
    UPLOAD_TYPES = [
        ('EXCEL', 'Excel File'),
        ('IMAGE', 'Image File'),
        ('CSV', 'CSV File'),
    ]
    
    STATUS_CHOICES = [
        ('UPLOADING', 'Uploading'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('ERROR', 'Error'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_sessions')
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='upload_sessions')
    
    # File information
    upload_type = models.CharField(max_length=10, choices=UPLOAD_TYPES)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # Size in bytes
    file_path = models.CharField(max_length=500)
    
    # Processing status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='UPLOADING')
    progress = models.IntegerField(default=0)  # Progress percentage
    
    # Results
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.upload_type} upload by {self.user.email} - {self.status}"
    
    @property
    def duration(self):
        """Calculate processing duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class ExtractedProduct(models.Model):
    """Products extracted from files before being saved to inventory"""
    
    upload_session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, related_name='extracted_products')
    
    # Product data (as extracted from file)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    supplier = models.CharField(max_length=255, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Inventory
    quantity = models.IntegerField(blank=True, null=True)
    min_stock_level = models.IntegerField(blank=True, null=True)
    
    # Additional info
    weight = models.CharField(max_length=50, blank=True, null=True)
    origin = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    
    # Halal information
    halal_certified = models.BooleanField(default=False)
    halal_certification_body = models.CharField(max_length=255, blank=True, null=True)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Row information
    row_number = models.IntegerField()
    raw_data = models.JSONField(default=dict, blank=True)  # Original row data
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['row_number']
    
    def __str__(self):
        return f"{self.name} (Row {self.row_number})"


class FileProcessingLog(models.Model):
    """Log file processing activities"""
    
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    upload_session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    row_number = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.level}: {self.message[:50]}"


class ImageProcessingResult(models.Model):
    """Results from image OCR processing"""
    
    upload_session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, related_name='image_results')
    
    # Image information
    image_path = models.CharField(max_length=500)
    image_size = models.BigIntegerField()  # Size in bytes
    image_dimensions = models.CharField(max_length=50, blank=True, null=True)  # e.g., "1920x1080"
    
    # OCR results
    extracted_text = models.TextField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    
    # Structured data extraction
    detected_products = models.JSONField(default=list, blank=True)
    detected_prices = models.JSONField(default=list, blank=True)
    detected_barcodes = models.JSONField(default=list, blank=True)
    
    # Processing details
    ocr_engine = models.CharField(max_length=50, default='tesseract')
    processing_time = models.FloatField(blank=True, null=True)  # Time in seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image processing result for {self.upload_session.file_name}"


class ProcessingTemplate(models.Model):
    """Templates for processing different file formats"""
    
    TEMPLATE_TYPES = [
        ('EXCEL', 'Excel Template'),
        ('CSV', 'CSV Template'),
    ]
    
    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=10, choices=TEMPLATE_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processing_templates')
    
    # Column mappings
    column_mappings = models.JSONField(default=dict)  # Maps file columns to product fields
    
    # Processing rules
    validation_rules = models.JSONField(default=dict, blank=True)
    transformation_rules = models.JSONField(default=dict, blank=True)
    
    # Settings
    has_header_row = models.BooleanField(default=True)
    start_row = models.IntegerField(default=1)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class BatchOperation(models.Model):
    """Batch operations on extracted products"""
    
    OPERATION_TYPES = [
        ('IMPORT', 'Import to Inventory'),
        ('UPDATE', 'Update Existing'),
        ('DELETE', 'Delete Products'),
        ('VALIDATE', 'Validate Data'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    upload_session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, related_name='batch_operations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    operation_type = models.CharField(max_length=15, choices=OPERATION_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    # Progress tracking
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    successful_items = models.IntegerField(default=0)
    failed_items = models.IntegerField(default=0)
    
    # Results
    result_summary = models.JSONField(default=dict, blank=True)
    error_details = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.operation_type} operation - {self.status}"
    
    @property
    def progress_percentage(self):
        if self.total_items > 0:
            return (self.processed_items / self.total_items) * 100
        return 0