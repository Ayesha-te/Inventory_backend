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
    
    # Barcode and Ticket Generation
    path('products/<uuid:product_id>/barcode/', views.BarcodeGenerationView.as_view(), name='product_barcode'),
    path('products/<uuid:product_id>/ticket/', views.ProductTicketView.as_view(), name='product_ticket'),
    path('products/<uuid:product_id>/generate-barcode/', views.generate_barcode_for_product, name='generate_barcode'),
    path('products/bulk-tickets/', views.BulkTicketsView.as_view(), name='bulk_tickets'),
    path('products/bulk-barcodes/', views.BulkBarcodesView.as_view(), name='bulk_barcodes'),

    # Clearance
    path('clearance/', views.ClearanceListCreateView.as_view(), name='clearance_list_create'),
    path('clearance/<uuid:pk>/', views.ClearanceDetailView.as_view(), name='clearance_detail'),
    path('clearance/active/', views.ClearanceActiveListView.as_view(), name='clearance_active'),
    path('clearance/<uuid:clearance_id>/barcode/', views.ClearanceBarcodeView.as_view(), name='clearance_barcode'),
    path('clearance/<uuid:clearance_id>/ticket/', views.ClearanceTicketView.as_view(), name='clearance_ticket'),
]