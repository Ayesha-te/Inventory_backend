"""
Enhanced URL patterns for Multi-Channel Order Management System
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import enhanced_views
from .webhooks import (
    ShopifyWebhookView, AmazonWebhookView, EbayWebhookView,
    WooCommerceWebhookView, EtsyWebhookView
)

# Create router for viewsets if needed
router = DefaultRouter()

urlpatterns = [
    # Channel Management
    path('channels/', enhanced_views.ChannelListCreateView.as_view(), name='channel-list-create'),
    path('channels/<uuid:pk>/', enhanced_views.ChannelDetailView.as_view(), name='channel-detail'),
    path('channels/test-connection/', enhanced_views.test_channel_connection, name='test-channel-connection'),
    
    # SKU Mapping
    path('sku-mappings/', enhanced_views.SKUMappingListCreateView.as_view(), name='sku-mapping-list-create'),
    
    # Stock Management
    path('stock-levels/', enhanced_views.StockLevelListView.as_view(), name='stock-level-list'),
    path('stock-levels/update/', enhanced_views.update_stock_levels, name='update-stock-levels'),
    path('stock-levels/sync-to-channels/', enhanced_views.sync_stock_to_channels, name='sync-stock-to-channels'),
    
    # Enhanced Orders
    path('enhanced-orders/', enhanced_views.EnhancedOrderListCreateView.as_view(), name='enhanced-order-list-create'),
    path('enhanced-orders/import/', enhanced_views.import_channel_orders, name='import-channel-orders'),
    
    # Automation Rules
    path('automation-rules/', enhanced_views.AutomationRuleListCreateView.as_view(), name='automation-rule-list-create'),
    
    # Warehouses
    path('warehouses/', enhanced_views.WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    
    # Courier Services
    path('courier-services/', enhanced_views.CourierServiceListView.as_view(), name='courier-service-list'),
    
    # Analytics and Metrics
    path('analytics/', enhanced_views.order_analytics, name='order-analytics'),
    path('dashboard-metrics/', enhanced_views.dashboard_metrics, name='dashboard-metrics'),
    
    # Webhook Endpoints for Channel Integration
    path('webhooks/shopify/', ShopifyWebhookView.as_view(), name='shopify-webhook'),
    path('webhooks/amazon/', AmazonWebhookView.as_view(), name='amazon-webhook'),
    path('webhooks/ebay/', EbayWebhookView.as_view(), name='ebay-webhook'),
    path('webhooks/woocommerce/', WooCommerceWebhookView.as_view(), name='woocommerce-webhook'),
    path('webhooks/etsy/', EtsyWebhookView.as_view(), name='etsy-webhook'),
    
    # Include router URLs
    path('', include(router.urls)),
]