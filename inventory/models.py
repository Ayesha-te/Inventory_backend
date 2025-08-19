from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Category(models.Model):
    """Product categories"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_name(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Supplier(models.Model):
    """Product suppliers"""
    
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Main product model"""
    
    HALAL_STATUS_CHOICES = [
        ('CERTIFIED', 'Halal Certified'),
        ('NOT_CERTIFIED', 'Not Certified'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    
    # Identification
    barcode = models.CharField(max_length=50, unique=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])  # Current price
    
    # Inventory
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    min_stock_level = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    max_stock_level = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    
    # Physical Properties
    weight = models.CharField(max_length=50, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    origin = models.CharField(max_length=100, blank=True, null=True)
    
    # Dates
    expiry_date = models.DateField()
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Location
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Aisle/shelf location")
    
    # Halal Information
    halal_certified = models.BooleanField(default=False)
    halal_status = models.CharField(max_length=20, choices=HALAL_STATUS_CHOICES, default='UNKNOWN')
    halal_certification_body = models.CharField(max_length=255, blank=True, null=True)
    
    # Images
    image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    # Relationships
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='products')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # POS Integration
    synced_with_pos = models.BooleanField(default=False)
    pos_id = models.CharField(max_length=100, blank=True, null=True)
    last_pos_sync = models.DateTimeField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-added_date']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['quantity']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.barcode}"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level
    
    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()
    
    @property
    def days_until_expiry(self):
        delta = self.expiry_date - timezone.now().date()
        return delta.days
    
    @property
    def is_expiring_soon(self):
        return 0 < self.days_until_expiry <= 7
    
    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    @property
    def total_value(self):
        return self.quantity * self.price


class ProductImage(models.Model):
    """Additional product images"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/additional/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"


class StockMovement(models.Model):
    """Track stock movements"""
    
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('RETURNED', 'Returned'),
        ('TRANSFER', 'Transfer'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True)  # Invoice, PO number, etc.
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"


class ProductAlert(models.Model):
    """Product alerts for low stock, expiry, etc."""
    
    ALERT_TYPES = [
        ('LOW_STOCK', 'Low Stock'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('PRICE_CHANGE', 'Price Change'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.alert_type}"


class Barcode(models.Model):
    """Barcode management"""
    
    BARCODE_TYPES = [
        ('UPC', 'UPC'),
        ('EAN', 'EAN'),
        ('CODE128', 'Code 128'),
        ('CODE39', 'Code 39'),
        ('QR', 'QR Code'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    barcode_type = models.CharField(max_length=10, choices=BARCODE_TYPES, default='EAN')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='barcodes')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} ({self.barcode_type})"


class ProductReview(models.Model):
    """Product reviews and ratings"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating}/5 by {self.user.email}"