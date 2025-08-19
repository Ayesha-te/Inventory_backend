from django.contrib import admin
from .models import (
    Category, Supplier, Product, ProductImage, StockMovement,
    ProductAlert, Barcode, ProductReview
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'barcode', 'category', 'supplier', 'quantity',
        'price', 'expiry_date', 'is_active'
    ]
    list_filter = [
        'category', 'supplier', 'is_active', 'halal_certified',
        'synced_with_pos', 'added_date'
    ]
    search_fields = ['name', 'barcode', 'brand', 'description']
    ordering = ['-added_date']
    readonly_fields = ['added_date', 'updated_date']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'movement_type', 'quantity', 'new_quantity',
        'created_by', 'created_at'
    ]
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ProductAlert)
class ProductAlertAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'alert_type', 'priority', 'is_read',
        'is_resolved', 'created_at'
    ]
    list_filter = ['alert_type', 'priority', 'is_read', 'is_resolved']
    search_fields = ['product__name', 'message']
    ordering = ['-created_at']