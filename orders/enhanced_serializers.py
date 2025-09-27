"""
Enhanced Serializers for Multi-Channel Order Management System
Similar to MultiOrders.com functionality
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .enhanced_models import (
    Channel, SKUMapping, StockLevel, StockReservation, 
    ProductBundle, BundleComponent, AutomationRule, 
    EnhancedOrder, EnhancedOrderItem,
    ChannelSyncLog, CourierService, CourierServiceOption
)
from .models import Order, OrderItem, Warehouse
from supermarkets.models import Supermarket
from inventory.models import Product

User = get_user_model()


class ChannelSerializer(serializers.ModelSerializer):
    """Serializer for sales channels"""
    
    class Meta:
        model = Channel
        fields = [
            'id', 'supermarket', 'name', 'type', 'is_active',
            'credentials', 'webhook_url', 'sync_status', 'last_sync',
            'auto_sync_orders', 'auto_sync_stock', 'auto_sync_products',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_sync']
        extra_kwargs = {
            'credentials': {'write_only': True}
        }


class SKUMappingSerializer(serializers.ModelSerializer):
    """Serializer for SKU mappings between channels and internal products"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    
    class Meta:
        model = SKUMapping
        fields = [
            'id', 'channel', 'channel_name', 'product', 'product_name',
            'internal_sku', 'channel_sku', 'channel_product_id',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for warehouses"""
    
    class Meta:
        model = Warehouse
        fields = [
            'id', 'supermarket', 'name', 'code', 'address',
            'is_active', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockLevelSerializer(serializers.ModelSerializer):
    """Serializer for stock levels"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    available_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = StockLevel
        fields = [
            'id', 'product', 'product_name', 'warehouse', 'warehouse_name',
            'quantity', 'reserved_quantity', 'available_stock',
            'min_stock_level', 'max_stock_level', 'reorder_point',
            'updated_at'
        ]
        read_only_fields = ['id', 'updated_at', 'available_stock']
    
    def get_available_stock(self, obj):
        return obj.quantity - obj.reserved_quantity


class StockReservationSerializer(serializers.ModelSerializer):
    """Serializer for stock reservations"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = StockReservation
        fields = [
            'id', 'product', 'product_name', 'warehouse', 'warehouse_name',
            'quantity', 'reference_type', 'reference_id', 'expires_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BundleComponentSerializer(serializers.ModelSerializer):
    """Serializer for bundle components"""
    
    component_name = serializers.CharField(source='component.name', read_only=True)
    
    class Meta:
        model = BundleComponent
        fields = [
            'id', 'component', 'component_name', 'quantity'
        ]
        read_only_fields = ['id']


class ProductBundleSerializer(serializers.ModelSerializer):
    """Serializer for product bundles"""
    
    components = BundleComponentSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductBundle
        fields = [
            'id', 'product', 'product_name', 'name', 'description',
            'is_active', 'components', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AutomationRuleSerializer(serializers.ModelSerializer):
    """Serializer for automation rules"""
    
    class Meta:
        model = AutomationRule
        fields = [
            'id', 'supermarket', 'name', 'description', 'trigger_event',
            'conditions', 'actions', 'is_active', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EnhancedOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for enhanced order items"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = EnhancedOrderItem
        fields = [
            'id', 'product', 'product_name', 'sku', 'quantity',
            'unit_price', 'total_price', 'status'
        ]
        read_only_fields = ['id', 'total_price']


class EnhancedOrderSerializer(serializers.ModelSerializer):
    """Serializer for enhanced orders"""
    
    items = EnhancedOrderItemSerializer(many=True, read_only=True)
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = EnhancedOrder
        fields = [
            'id', 'order_number', 'channel', 'channel_name', 'channel_order_id',
            'customer_name', 'customer_email', 'customer_phone',
            'shipping_address', 'billing_address', 'status', 'priority',
            'total_amount', 'currency', 'payment_status', 'payment_method',
            'shipping_method', 'tracking_number', 'warehouse', 'warehouse_name',
            'notes', 'tags', 'automation_applied', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CourierServiceOptionSerializer(serializers.ModelSerializer):
    """Serializer for courier service options"""
    
    class Meta:
        model = CourierServiceOption
        fields = [
            'id', 'name', 'code', 'estimated_days', 'max_weight', 'is_active'
        ]
        read_only_fields = ['id']


class CourierServiceSerializer(serializers.ModelSerializer):
    """Serializer for courier services"""
    
    service_options = CourierServiceOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = CourierService
        fields = [
            'id', 'supermarket', 'name', 'code', 'is_active',
            'auto_select_service', 'default_service', 'max_weight',
            'max_length', 'max_width', 'max_height', 'service_options',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'credentials': {'write_only': True}
        }


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for stock movements"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'warehouse', 'warehouse_name',
            'type', 'quantity', 'reason', 'reference', 'balance_before',
            'balance_after', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'balance_before', 'balance_after', 'created_at']


class ChannelSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for channel sync logs"""
    
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    
    class Meta:
        model = ChannelSyncLog
        fields = [
            'id', 'channel', 'channel_name', 'type', 'status', 'message',
            'details', 'records_processed', 'records_successful',
            'records_failed', 'duration', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Dashboard and Analytics Serializers
class ChannelPerformanceSerializer(serializers.Serializer):
    """Serializer for channel performance analytics"""
    
    channel_id = serializers.UUIDField()
    channel_name = serializers.CharField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_products = serializers.ListField()


class StockAlertSerializer(serializers.Serializer):
    """Serializer for stock alerts"""
    
    product_id = serializers.UUIDField()
    product_name = serializers.CharField()
    warehouse_id = serializers.UUIDField()
    warehouse_name = serializers.CharField()
    current_stock = serializers.IntegerField()
    min_stock_level = serializers.IntegerField()
    alert_type = serializers.CharField()  # 'low_stock', 'out_of_stock', 'overstock'


class OrderSummarySerializer(serializers.Serializer):
    """Serializer for order summary statistics"""
    
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    processing_orders = serializers.IntegerField()
    shipped_orders = serializers.IntegerField()
    delivered_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)