from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid



class Warehouse(models.Model):
    """Warehouse/fulfillment centers linked to a Supermarket (store). Used for order fulfillment."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, default='MAIN')
    
    # Address fields
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='UK')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Contact information
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=1)
    
    # Capacity and limits
    max_capacity = models.PositiveIntegerField(null=True, blank=True)
    current_utilization = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('supermarket', 'code')
        indexes = [
            models.Index(fields=['supermarket']),
            models.Index(fields=['city']),
            models.Index(fields=['postcode']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.city}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default warehouse per supermarket
        if self.is_default:
            Warehouse.objects.filter(
                supermarket=self.supermarket,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class Order(models.Model):
    """Customer order for a supermarket with expanded e-commerce fields."""

    ORDER_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned'),
        ('CANCELLED', 'Cancelled'),
    ]

    CHANNEL_CHOICES = [
        ('SHOPIFY', 'Shopify'),
        ('AMAZON', 'Amazon'),
        ('DARAZ', 'Daraz'),
        ('POS', 'POS'),
        ('MANUAL', 'Manual'),
        ('WEBSITE', 'Website'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('PREPAID', 'Prepaid'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('FAILED', 'Failed'),
    ]

    SHIPPING_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('LABEL_CREATED', 'Label Created'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
    ]

    COURIER_CHOICES = [
        ('DPD', 'DPD UK'),
        ('YODEL', 'Yodel'),
        ('CITYSPRINT', 'CitySprint'),
        ('COLLECTPLUS', 'CollectPlus'),
        ('TUFFNELLS', 'Tuffnells'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.CASCADE, related_name='orders')

    # Multi-channel
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='MANUAL')
    external_order_id = models.CharField(max_length=100, blank=True, null=True)

    # Customer + shipping
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    ship_name = models.CharField(max_length=255, blank=True, null=True)
    ship_phone = models.CharField(max_length=20, blank=True, null=True)
    ship_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    ship_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    ship_city = models.CharField(max_length=100, blank=True, null=True)
    ship_postcode = models.CharField(max_length=20, blank=True, null=True)
    ship_country = models.CharField(max_length=100, blank=True, null=True)

    # Fulfillment / warehouse
    assigned_warehouse = models.ForeignKey('orders.Warehouse', on_delete=models.SET_NULL, blank=True, null=True, related_name='orders')

    # Statuses
    status = models.CharField(max_length=12, choices=ORDER_STATUS, default='PENDING')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='COD')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    # Totals
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    # Raw source payload (for auditing)
    raw_payload = models.JSONField(blank=True, null=True)

    # Shipping / courier
    courier = models.CharField(max_length=20, choices=COURIER_CHOICES, blank=True, null=True)
    courier_awb = models.CharField(max_length=100, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    shipping_label_url = models.URLField(blank=True, null=True)
    shipping_status = models.CharField(max_length=20, choices=SHIPPING_STATUS_CHOICES, default='PENDING')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supermarket']),
            models.Index(fields=['status']),
            models.Index(fields=['channel']),
            models.Index(fields=['courier']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Order {self.id} [{self.channel}] - {self.status}"


class OrderItem(models.Model):
    """Items within an order"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, related_name='order_items')

    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        # Auto-calc line total
        if self.quantity is not None and self.unit_price is not None:
            self.total_price = (self.unit_price or 0) * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=12, choices=Order.ORDER_STATUS)
    to_status = models.CharField(max_length=12, choices=Order.ORDER_STATUS)
    note = models.CharField(max_length=255, blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']


class RMA(models.Model):
    """Return Merchandise Authorization"""
    RMA_STATUS = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('RECEIVED', 'Received'),
        ('REFUNDED', 'Refunded'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='rmas')
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=RMA_STATUS, default='REQUESTED')
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    restock = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class RMAItem(models.Model):
    rma = models.ForeignKey(RMA, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='rma_items')
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=50, blank=True, null=True)  # e.g., Damaged, Open-box

    class Meta:
        unique_together = ('rma', 'order_item')