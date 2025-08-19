from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
import uuid

User = get_user_model()


class Supermarket(models.Model):
    """Supermarket/Store model"""
    
    POS_SYSTEM_CHOICES = [
        ('SQUARE', 'Square'),
        ('SHOPIFY', 'Shopify'),
        ('CUSTOM', 'Custom'),
        ('NONE', 'None'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    address = models.TextField()
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")]
    )
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    
    # Business Information
    business_license = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Registration
    registration_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    
    # Media
    logo = models.ImageField(upload_to='supermarket_logos/', blank=True, null=True)
    
    # Relationships
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_supermarkets')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='sub_stores')
    is_sub_store = models.BooleanField(default=False)
    
    # POS System Configuration
    pos_system_type = models.CharField(max_length=20, choices=POS_SYSTEM_CHOICES, default='NONE')
    pos_system_enabled = models.BooleanField(default=False)
    pos_api_key = models.CharField(max_length=255, blank=True, null=True)
    pos_api_secret = models.CharField(max_length=255, blank=True, null=True)
    pos_store_id = models.CharField(max_length=100, blank=True, null=True)
    pos_sync_enabled = models.BooleanField(default=False)
    last_pos_sync = models.DateTimeField(blank=True, null=True)
    
    # Settings
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_sub_store']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def total_products(self):
        return self.products.filter(is_active=True).count()
    
    @property
    def total_inventory_value(self):
        from inventory.models import Product
        products = self.products.filter(is_active=True)
        return sum(p.total_value for p in products)
    
    @property
    def low_stock_products_count(self):
        return self.products.filter(
            is_active=True,
            quantity__lte=models.F('min_stock_level')
        ).count()


class SupermarketStaff(models.Model):
    """Staff members of supermarkets"""
    
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('ASSISTANT_MANAGER', 'Assistant Manager'),
        ('CASHIER', 'Cashier'),
        ('STOCK_CLERK', 'Stock Clerk'),
        ('SECURITY', 'Security'),
        ('CLEANER', 'Cleaner'),
        ('OTHER', 'Other'),
    ]
    
    supermarket = models.ForeignKey(Supermarket, on_delete=models.CASCADE, related_name='staff')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='staff_positions')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Permissions
    can_manage_inventory = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_pos = models.BooleanField(default=False)
    can_manage_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['supermarket', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} at {self.supermarket.name}"


class SupermarketSettings(models.Model):
    """Supermarket-specific settings"""
    
    supermarket = models.OneToOneField(Supermarket, on_delete=models.CASCADE, related_name='settings')
    
    # Notification Settings
    low_stock_alert_enabled = models.BooleanField(default=True)
    expiry_alert_enabled = models.BooleanField(default=True)
    expiry_alert_days = models.IntegerField(default=7)
    daily_report_enabled = models.BooleanField(default=False)
    weekly_report_enabled = models.BooleanField(default=True)
    monthly_report_enabled = models.BooleanField(default=True)
    
    # Inventory Settings
    auto_reorder_enabled = models.BooleanField(default=False)
    default_min_stock_level = models.IntegerField(default=5)
    barcode_generation_enabled = models.BooleanField(default=True)
    
    # POS Settings
    auto_sync_interval = models.IntegerField(default=60, help_text="Minutes between auto syncs")
    sync_price_changes = models.BooleanField(default=True)
    sync_stock_changes = models.BooleanField(default=True)
    sync_new_products = models.BooleanField(default=True)
    
    # Display Settings
    products_per_page = models.IntegerField(default=20)
    default_currency_symbol = models.CharField(max_length=5, default='$')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.supermarket.name}"


class SupermarketInvitation(models.Model):
    """Invitations to join supermarket staff"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('EXPIRED', 'Expired'),
    ]
    
    supermarket = models.ForeignKey(Supermarket, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=SupermarketStaff.ROLE_CHOICES)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    # Permissions for the invited user
    can_manage_inventory = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_pos = models.BooleanField(default=False)
    can_manage_staff = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.supermarket.name}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class SupermarketAnalytics(models.Model):
    """Daily analytics for supermarkets"""
    
    supermarket = models.ForeignKey(Supermarket, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # Product metrics
    total_products = models.IntegerField(default=0)
    total_inventory_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    low_stock_products = models.IntegerField(default=0)
    expired_products = models.IntegerField(default=0)
    expiring_soon_products = models.IntegerField(default=0)
    
    # Stock movements
    products_added = models.IntegerField(default=0)
    products_removed = models.IntegerField(default=0)
    stock_adjustments = models.IntegerField(default=0)
    
    # POS sync metrics
    pos_sync_count = models.IntegerField(default=0)
    pos_sync_errors = models.IntegerField(default=0)
    last_pos_sync = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['supermarket', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.supermarket.name} on {self.date}"