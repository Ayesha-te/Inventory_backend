"""
Enhanced Order Management Models for Multi-Channel System
Similar to MultiOrders.com functionality
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class Channel(models.Model):
    """Sales channels (Shopify, Amazon, eBay, etc.)"""
    
    CHANNEL_TYPES = [
        ('SHOPIFY', 'Shopify'),
        ('AMAZON', 'Amazon'),
        ('EBAY', 'eBay'),
        ('ETSY', 'Etsy'),
        ('WOOCOMMERCE', 'WooCommerce'),
        ('MAGENTO', 'Magento'),
        ('DARAZ', 'Daraz'),
        ('POS', 'POS'),
        ('MANUAL', 'Manual'),
        ('WEBSITE', 'Website'),
    ]
    
    SYNC_STATUS_CHOICES = [
        ('CONNECTED', 'Connected'),
        ('DISCONNECTED', 'Disconnected'),
        ('ERROR', 'Error'),
        ('SYNCING', 'Syncing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Credentials stored as JSON
    credentials = models.JSONField(default=dict, blank=True)
    
    # Channel settings
    auto_import_orders = models.BooleanField(default=True)
    auto_sync_stock = models.BooleanField(default=True)
    order_import_frequency = models.PositiveIntegerField(default=15)  # minutes
    stock_sync_frequency = models.PositiveIntegerField(default=30)  # minutes
    default_warehouse = models.ForeignKey('orders.Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    price_markup = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Sync status
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='DISCONNECTED')
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('supermarket', 'name', 'type')
        indexes = [
            models.Index(fields=['supermarket', 'type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sync_status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.type})"


class SKUMapping(models.Model):
    """Maps internal SKUs to channel-specific SKUs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='sku_mappings')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='sku_mappings')
    internal_sku = models.CharField(max_length=100)
    channel_sku = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_override = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('channel', 'channel_sku')
        indexes = [
            models.Index(fields=['product', 'channel']),
            models.Index(fields=['internal_sku']),
            models.Index(fields=['channel_sku']),
        ]
    
    def __str__(self):
        return f"{self.internal_sku} -> {self.channel_sku} ({self.channel.name})"


class StockLevel(models.Model):
    """Stock levels per product per warehouse"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='stock_levels')
    warehouse = models.ForeignKey('orders.Warehouse', on_delete=models.CASCADE, related_name='stock_levels')
    
    available = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reserved = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    on_order = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    allocated = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    damaged = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    reorder_point = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    max_stock = models.IntegerField(default=1000, validators=[MinValueValidator(1)])
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'warehouse')
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['warehouse']),
            models.Index(fields=['available']),
            models.Index(fields=['reorder_point']),
        ]
    
    @property
    def total(self):
        return self.available + self.reserved + self.allocated + self.damaged
    
    @property
    def sellable(self):
        return self.available - self.reserved
    
    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}: {self.available} available"


class StockReservation(models.Model):
    """Stock reservations for orders"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('FULFILLED', 'Fulfilled'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='stock_reservations')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='stock_reservations')
    warehouse = models.ForeignKey('orders.Warehouse', on_delete=models.CASCADE, related_name='stock_reservations')
    
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    expires_at = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Reserved {self.quantity} x {self.product.name} for Order {self.order.id}"


class ProductBundle(models.Model):
    """Product bundles/kits"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='bundles')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('supermarket', 'sku')
        indexes = [
            models.Index(fields=['supermarket']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Bundle: {self.name} ({self.sku})"


class BundleComponent(models.Model):
    """Components of a product bundle"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bundle = models.ForeignKey(ProductBundle, on_delete=models.CASCADE, related_name='components')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='bundle_components')
    quantity = models.PositiveIntegerField(default=1)
    is_optional = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('bundle', 'product')
        indexes = [
            models.Index(fields=['bundle']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.bundle.name}"




class AutomationRule(models.Model):
    """Automation rules for order processing"""
    
    TRIGGER_EVENTS = [
        ('ORDER_PLACED', 'Order Placed'),
        ('STOCK_LOW', 'Stock Low'),
        ('ORDER_SHIPPED', 'Order Shipped'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='automation_rules')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Trigger configuration stored as JSON
    trigger_event = models.CharField(max_length=20, choices=TRIGGER_EVENTS)
    trigger_conditions = models.JSONField(default=list)  # List of conditions
    
    # Actions stored as JSON
    actions = models.JSONField(default=list)  # List of actions
    
    priority = models.IntegerField(default=0)  # Higher number = higher priority
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['supermarket']),
            models.Index(fields=['trigger_event']),
            models.Index(fields=['is_active']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"Rule: {self.name} ({self.trigger_event})"


class EnhancedOrder(models.Model):
    """Enhanced order model with multi-channel support"""
    
    ORDER_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial'),
    ]
    
    FULFILLMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True)
    external_order_id = models.CharField(max_length=100, blank=True, null=True)
    
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='enhanced_orders')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='orders')
    
    # Customer information stored as JSON
    customer_info = models.JSONField(default=dict)
    
    # Shipping information stored as JSON
    shipping_info = models.JSONField(default=dict)
    
    # Status fields
    status = models.CharField(max_length=12, choices=ORDER_STATUS, default='PENDING')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    fulfillment_status = models.CharField(max_length=12, choices=FULFILLMENT_STATUS, default='PENDING')
    
    # Financial fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    # Fulfillment
    assigned_warehouse = models.ForeignKey('orders.Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    courier_service = models.CharField(max_length=50, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipping_label_url = models.URLField(blank=True, null=True)
    
    # Metadata
    tags = models.JSONField(default=list)  # List of tags
    notes = models.TextField(blank=True, null=True)
    raw_payload = models.JSONField(blank=True, null=True)  # Original order data from channel
    automation_rules_applied = models.JSONField(default=list)  # List of rule IDs applied
    
    # Timestamps
    placed_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-placed_at']
        indexes = [
            models.Index(fields=['supermarket']),
            models.Index(fields=['channel']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['fulfillment_status']),
            models.Index(fields=['placed_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['external_order_id']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} [{self.channel.name}] - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import time
            self.order_number = f"ORD-{int(time.time())}"
        
        if not self.placed_at:
            self.placed_at = timezone.now()
        
        super().save(*args, **kwargs)


class EnhancedOrderItem(models.Model):
    """Enhanced order items with stock management"""
    
    ITEM_STATUS = [
        ('PENDING', 'Pending'),
        ('RESERVED', 'Reserved'),
        ('ALLOCATED', 'Allocated'),
        ('PICKED', 'Picked'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(EnhancedOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, related_name='enhanced_order_items')
    
    sku = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Stock management
    reservation = models.ForeignKey(StockReservation, on_delete=models.SET_NULL, null=True, blank=True)
    allocated_warehouse = models.ForeignKey('orders.Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Bundle information
    bundle = models.ForeignKey(ProductBundle, on_delete=models.SET_NULL, null=True, blank=True)
    bundle_components = models.JSONField(default=list, blank=True)  # For bundle items
    
    # Status
    status = models.CharField(max_length=12, choices=ITEM_STATUS, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order {self.order.order_number})"
    
    def save(self, *args, **kwargs):
        if self.unit_price and self.quantity:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class CourierService(models.Model):
    """Courier/shipping services"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='courier_services')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    
    # Credentials stored as JSON
    credentials = models.JSONField(default=dict, blank=True)
    
    # Settings
    auto_select_service = models.BooleanField(default=False)
    default_service = models.CharField(max_length=50, blank=True, null=True)
    max_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    max_height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('supermarket', 'code')
        indexes = [
            models.Index(fields=['supermarket']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class CourierServiceOption(models.Model):
    """Specific service options for couriers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    courier_service = models.ForeignKey(CourierService, on_delete=models.CASCADE, related_name='service_options')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    estimated_days = models.PositiveIntegerField()
    max_weight = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('courier_service', 'code')
        indexes = [
            models.Index(fields=['courier_service']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.courier_service.name} - {self.name}"




class ChannelSyncLog(models.Model):
    """Log channel synchronization activities"""
    
    SYNC_TYPES = [
        ('ORDER_IMPORT', 'Order Import'),
        ('STOCK_SYNC', 'Stock Sync'),
        ('PRODUCT_SYNC', 'Product Sync'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='sync_logs')
    type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.TextField()
    details = models.JSONField(blank=True, null=True)
    
    records_processed = models.PositiveIntegerField(default=0)
    records_successful = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    duration = models.PositiveIntegerField(default=0)  # milliseconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['channel']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.channel.name} - {self.type} - {self.status}"