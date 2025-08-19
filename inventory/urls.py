from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Suppliers
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier_list_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    
    # Products
    path('products/', views.ProductListCreateView.as_view(), name='product_list_create'),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<uuid:product_id>/stock/', views.ProductStockUpdateView.as_view(), name='product_stock_update'),
    path('products/bulk-update/', views.BulkProductUpdateView.as_view(), name='bulk_product_update'),
    path('products/stats/', views.ProductStatsView.as_view(), name='product_stats'),
    path('products/barcode/<str:barcode>/', views.search_products_by_barcode, name='search_by_barcode'),
    
    # Stock Movements
    path('stock-movements/', views.StockMovementListView.as_view(), name='stock_movement_list'),
    
    # Alerts
    path('alerts/', views.ProductAlertListView.as_view(), name='product_alert_list'),
    path('alerts/<int:alert_id>/read/', views.mark_alert_as_read, name='mark_alert_read'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Reviews
    path('reviews/', views.ProductReviewListCreateView.as_view(), name='product_review_list_create'),
]