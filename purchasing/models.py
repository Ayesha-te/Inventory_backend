from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class SupplierProduct(models.Model):
    """Mapping between a Supplier and a Product with supplier-specific pricing and availability"""
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.CASCADE, related_name='supplier_products')
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='supplier_products')
    supplier_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('supplier', 'product')
        ordering = ['supplier__name']

    def __str__(self):
        return f"{self.supplier.name} -> {self.product.name}"


class PurchaseOrder(models.Model):
    """Simple purchase order to buy products from suppliers"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.PROTECT, related_name='purchase_orders')
    supermarket = models.ForeignKey('supermarkets.Supermarket', on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        return sum([(item.quantity * item.unit_price) for item in self.items.all()])

    def __str__(self):
        return f"PO#{self.id} - {self.supplier.name} - {self.status}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"