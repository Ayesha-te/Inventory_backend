from django.contrib import admin
from .models import SupplierProduct, PurchaseOrder, PurchaseOrderItem

@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'product', 'supplier_price', 'available_quantity', 'is_active')
    list_filter = ('is_active', 'supplier')
    search_fields = ('supplier__name', 'product__name')

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'supermarket', 'status', 'created_at')
    list_filter = ('status', 'supplier', 'supermarket')
    inlines = [PurchaseOrderItemInline]