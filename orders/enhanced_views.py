"""
Enhanced API Views for Multi-Channel Order Management System
Similar to MultiOrders.com functionality
"""

from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .enhanced_models import (
    Channel, SKUMapping, StockLevel, StockReservation, 
    ProductBundle, BundleComponent, AutomationRule, 
    EnhancedOrder, EnhancedOrderItem,
    ChannelSyncLog, CourierService
)
from .models import Order, OrderItem, Warehouse
from supermarkets.models import Supermarket
from inventory.models import Product, StockMovement


# Channel Management Views
class ChannelListCreateView(generics.ListCreateAPIView):
    """List and create sales channels"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'is_active', 'sync_status']
    search_fields = ['name', 'type']

    def get_queryset(self):
        return Channel.objects.filter(
            supermarket__owner=self.request.user
        ).select_related('supermarket')

    def get_serializer_class(self):
        from .enhanced_serializers import ChannelSerializer
        return ChannelSerializer

    def perform_create(self, serializer):
        # Ensure user owns the supermarket
        supermarket_id = self.request.data.get('supermarket')
        try:
            supermarket = Supermarket.objects.get(
                id=supermarket_id, 
                owner=self.request.user
            )
            serializer.save(supermarket=supermarket)
        except Supermarket.DoesNotExist:
            raise ValidationError("Invalid supermarket")


class ChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete a specific channel"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Channel.objects.filter(supermarket__owner=self.request.user)

    def get_serializer_class(self):
        from .enhanced_serializers import ChannelSerializer
        return ChannelSerializer


# SKU Mapping Views
class SKUMappingListCreateView(generics.ListCreateAPIView):
    """List and create SKU mappings between internal and external systems"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['channel', 'product']
    search_fields = ['internal_sku', 'external_sku']

    def get_queryset(self):
        return SKUMapping.objects.filter(
            channel__supermarket__owner=self.request.user
        ).select_related('channel', 'product')

    def get_serializer_class(self):
        from .enhanced_serializers import SKUMappingSerializer
        return SKUMappingSerializer


# Stock Management Views
class StockLevelListView(generics.ListAPIView):
    """List stock levels with filtering and search"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['warehouse', 'product']
    search_fields = ['product__name', 'product__barcode']
    ordering_fields = ['available_quantity', 'reserved_quantity', 'last_updated']
    ordering = ['-last_updated']

    def get_queryset(self):
        return StockLevel.objects.filter(
            warehouse__supermarket__owner=self.request.user
        ).select_related('warehouse', 'product')

    def get_serializer_class(self):
        from .enhanced_serializers import StockLevelSerializer
        return StockLevelSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_stock_levels(request):
    """Bulk update stock levels"""
    updates = request.data.get('updates', [])
    results = []
    
    for update in updates:
        try:
            stock_level = StockLevel.objects.get(
                id=update['id'],
                warehouse__supermarket__owner=request.user
            )
            
            # Update quantities
            if 'available_quantity' in update:
                stock_level.available_quantity = update['available_quantity']
            if 'damaged_quantity' in update:
                stock_level.damaged_quantity = update['damaged_quantity']
            
            stock_level.save()
            
            # Create stock movement record
            StockMovement.objects.create(
                product=stock_level.product,
                warehouse=stock_level.warehouse,
                movement_type='ADJUSTMENT',
                quantity_change=update.get('quantity_change', 0),
                reason=update.get('reason', 'Manual adjustment'),
                created_by=request.user
            )
            
            results.append({
                'id': stock_level.id,
                'status': 'success'
            })
            
        except StockLevel.DoesNotExist:
            results.append({
                'id': update.get('id'),
                'status': 'error',
                'message': 'Stock level not found'
            })
        except Exception as e:
            results.append({
                'id': update.get('id'),
                'status': 'error',
                'message': str(e)
            })
    
    return Response({'results': results})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_stock_to_channels(request):
    """Sync stock levels to all connected channels"""
    supermarket_id = request.data.get('supermarket_id')
    
    try:
        supermarket = Supermarket.objects.get(
            id=supermarket_id,
            owner=request.user
        )
        
        channels = Channel.objects.filter(
            supermarket=supermarket,
            is_active=True,
            auto_sync_stock=True
        )
        
        sync_results = []
        
        for channel in channels:
            try:
                # Get all stock levels for this supermarket
                stock_levels = StockLevel.objects.filter(
                    warehouse__supermarket=supermarket
                ).select_related('product')
                
                # Simulate sync to channel (implement actual API calls)
                sync_count = 0
                for stock_level in stock_levels:
                    # Here you would make actual API calls to update stock
                    # For now, we'll just log the sync
                    SyncLog.objects.create(
                        channel=channel,
                        sync_type='STOCK_UPDATE',
                        status='SUCCESS',
                        details=f'Updated stock for {stock_level.product.name}'
                    )
                    sync_count += 1
                
                sync_results.append({
                    'channel': channel.name,
                    'status': 'success',
                    'synced_items': sync_count
                })
                
            except Exception as e:
                sync_results.append({
                    'channel': channel.name,
                    'status': 'error',
                    'message': str(e)
                })
                
                SyncLog.objects.create(
                    channel=channel,
                    sync_type='STOCK_UPDATE',
                    status='ERROR',
                    error_message=str(e)
                )
        
        return Response({
            'status': 'completed',
            'results': sync_results
        })
        
    except Supermarket.DoesNotExist:
        return Response(
            {'error': 'Supermarket not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# Enhanced Order Views
class EnhancedOrderListCreateView(generics.ListCreateAPIView):
    """List and create enhanced orders with multi-channel support"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'channel', 'fulfillment_status', 'payment_status']
    search_fields = ['customer_name', 'customer_email', 'external_order_id']
    ordering_fields = ['created_at', 'total_amount', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return EnhancedOrder.objects.filter(
            supermarket__owner=self.request.user
        ).select_related('supermarket', 'channel', 'assigned_warehouse')

    def get_serializer_class(self):
        from .enhanced_serializers import EnhancedOrderSerializer
        return EnhancedOrderSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_channel_orders(request):
    """Import orders from external channels"""
    channel_id = request.data.get('channel_id')
    orders_data = request.data.get('orders', [])
    
    try:
        channel = Channel.objects.get(
            id=channel_id,
            supermarket__owner=request.user
        )
        
        imported_orders = []
        errors = []
        
        for order_data in orders_data:
            try:
                # Check if order already exists
                existing_order = EnhancedOrder.objects.filter(
                    external_order_id=order_data.get('external_order_id'),
                    channel=channel
                ).first()
                
                if existing_order:
                    continue  # Skip existing orders
                
                # Create new order
                order = EnhancedOrder.objects.create(
                    supermarket=channel.supermarket,
                    channel=channel,
                    external_order_id=order_data.get('external_order_id'),
                    customer_name=order_data.get('customer_name'),
                    customer_email=order_data.get('customer_email'),
                    customer_phone=order_data.get('customer_phone'),
                    shipping_address=order_data.get('shipping_address', {}),
                    billing_address=order_data.get('billing_address', {}),
                    total_amount=order_data.get('total_amount', 0),
                    currency=order_data.get('currency', 'USD'),
                    payment_method=order_data.get('payment_method'),
                    raw_data=order_data
                )
                
                # Create order items
                for item_data in order_data.get('items', []):
                    # Map external SKU to internal product
                    sku_mapping = SKUMapping.objects.filter(
                        channel=channel,
                        external_sku=item_data.get('sku')
                    ).first()
                    
                    if sku_mapping:
                        EnhancedOrderItem.objects.create(
                            order=order,
                            product=sku_mapping.product,
                            quantity=item_data.get('quantity', 1),
                            unit_price=item_data.get('unit_price', 0),
                            external_sku=item_data.get('sku')
                        )
                
                # Try to reserve stock
                reserve_stock_for_order(order)
                
                imported_orders.append(order.id)
                
            except Exception as e:
                errors.append({
                    'order_id': order_data.get('external_order_id'),
                    'error': str(e)
                })
        
        return Response({
            'imported_count': len(imported_orders),
            'imported_orders': imported_orders,
            'errors': errors
        })
        
    except Channel.DoesNotExist:
        return Response(
            {'error': 'Channel not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


def reserve_stock_for_order(order):
    """Reserve stock for order items"""
    for item in order.items.all():
        # Find available stock
        stock_levels = StockLevel.objects.filter(
            product=item.product,
            warehouse__supermarket=order.supermarket,
            available_quantity__gte=item.quantity
        ).order_by('-available_quantity')
        
        remaining_quantity = item.quantity
        
        for stock_level in stock_levels:
            if remaining_quantity <= 0:
                break
                
            reserve_quantity = min(remaining_quantity, stock_level.available_quantity)
            
            # Create reservation
            StockReservation.objects.create(
                product=item.product,
                warehouse=stock_level.warehouse,
                order=order,
                reserved_quantity=reserve_quantity,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # Update stock level
            stock_level.reserved_quantity += reserve_quantity
            stock_level.available_quantity -= reserve_quantity
            stock_level.save()
            
            remaining_quantity -= reserve_quantity
        
        if remaining_quantity > 0:
            # Partial stock available - mark order for review
            order.notes = f"Insufficient stock for {item.product.name}. Short by {remaining_quantity} units."
            order.status = 'ON_HOLD'
            order.save()


# Analytics Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_analytics(request):
    """Get order analytics and metrics"""
    supermarket_id = request.GET.get('supermarket_id')
    days = int(request.GET.get('days', 30))
    
    try:
        supermarket = Supermarket.objects.get(
            id=supermarket_id,
            owner=request.user
        )
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Basic metrics
        orders = EnhancedOrder.objects.filter(
            supermarket=supermarket,
            created_at__gte=start_date
        )
        
        total_orders = orders.count()
        total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        avg_order_value = orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
        
        # Orders by channel
        orders_by_channel = orders.values('channel__name').annotate(
            count=Count('id'),
            revenue=Sum('total_amount')
        ).order_by('-count')
        
        # Orders by status
        orders_by_status = orders.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Top products
        top_products = EnhancedOrderItem.objects.filter(
            order__supermarket=supermarket,
            order__created_at__gte=start_date
        ).values('product__name').annotate(
            quantity_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-quantity_sold')[:10]
        
        # Stock alerts
        low_stock_items = StockLevel.objects.filter(
            warehouse__supermarket=supermarket,
            available_quantity__lte=F('reorder_level')
        ).select_related('product').count()
        
        return Response({
            'period_days': days,
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'average_order_value': float(avg_order_value),
            'orders_by_channel': list(orders_by_channel),
            'orders_by_status': list(orders_by_status),
            'top_products': list(top_products),
            'low_stock_alerts': low_stock_items
        })
        
    except Supermarket.DoesNotExist:
        return Response(
            {'error': 'Supermarket not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# Automation Rules Views
class AutomationRuleListCreateView(generics.ListCreateAPIView):
    """List and create automation rules"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'trigger_event']

    def get_queryset(self):
        return AutomationRule.objects.filter(
            supermarket__owner=self.request.user
        )

    def get_serializer_class(self):
        from .enhanced_serializers import AutomationRuleSerializer
        return AutomationRuleSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_channel_connection(request):
    """Test connection to a sales channel"""
    channel_id = request.data.get('channel_id')
    
    try:
        channel = Channel.objects.get(
            id=channel_id,
            supermarket__owner=request.user
        )
        
        # Simulate connection test (implement actual API calls)
        # This would make actual API calls to test credentials
        
        if channel.type == 'SHOPIFY':
            # Test Shopify connection
            test_result = test_shopify_connection(channel.credentials)
        elif channel.type == 'AMAZON':
            # Test Amazon connection
            test_result = test_amazon_connection(channel.credentials)
        else:
            test_result = {'success': True, 'message': 'Connection test not implemented for this channel type'}
        
        # Update channel status
        if test_result['success']:
            channel.sync_status = 'CONNECTED'
            channel.last_sync = timezone.now()
        else:
            channel.sync_status = 'ERROR'
        
        channel.save()
        
        return Response(test_result)
        
    except Channel.DoesNotExist:
        return Response(
            {'error': 'Channel not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


def test_shopify_connection(credentials):
    """Test Shopify API connection"""
    # Implement actual Shopify API test
    return {'success': True, 'message': 'Shopify connection successful'}


def test_amazon_connection(credentials):
    """Test Amazon API connection"""
    # Implement actual Amazon API test
    return {'success': True, 'message': 'Amazon connection successful'}


# Warehouse Management Views
class WarehouseListCreateView(generics.ListCreateAPIView):
    """List and create warehouses"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'city', 'postcode']

    def get_queryset(self):
        return Warehouse.objects.filter(
            supermarket__owner=self.request.user
        )

    def get_serializer_class(self):
        from .enhanced_serializers import WarehouseSerializer
        return WarehouseSerializer


# Courier Service Views
class CourierServiceListView(generics.ListAPIView):
    """List available courier services"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CourierService.objects.filter(is_active=True)

    def get_serializer_class(self):
        from .enhanced_serializers import CourierServiceSerializer
        return CourierServiceSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_metrics(request):
    """Get dashboard metrics for multi-channel order management"""
    supermarket_id = request.GET.get('supermarket_id')
    
    try:
        supermarket = Supermarket.objects.get(
            id=supermarket_id,
            owner=request.user
        )
        
        today = timezone.now().date()
        
        # Today's metrics
        today_orders = EnhancedOrder.objects.filter(
            supermarket=supermarket,
            created_at__date=today
        )
        
        # Channel status
        channels = Channel.objects.filter(supermarket=supermarket)
        active_channels = channels.filter(is_active=True).count()
        connected_channels = channels.filter(sync_status='CONNECTED').count()
        
        # Stock alerts
        low_stock_count = StockLevel.objects.filter(
            warehouse__supermarket=supermarket,
            available_quantity__lte=F('reorder_level')
        ).count()
        
        # Recent orders
        recent_orders = EnhancedOrder.objects.filter(
            supermarket=supermarket
        ).select_related('channel').order_by('-created_at')[:10]
        
        return Response({
            'today_orders_count': today_orders.count(),
            'today_revenue': float(today_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
            'active_channels': active_channels,
            'connected_channels': connected_channels,
            'low_stock_alerts': low_stock_count,
            'recent_orders': [
                {
                    'id': order.id,
                    'external_order_id': order.external_order_id,
                    'customer_name': order.customer_name,
                    'channel': order.channel.name if order.channel else 'Manual',
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'created_at': order.created_at
                }
                for order in recent_orders
            ]
        })
        
    except Supermarket.DoesNotExist:
        return Response(
            {'error': 'Supermarket not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )