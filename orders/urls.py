from django.urls import path, include
from . import views

urlpatterns = [
    # Basic Orders (legacy)
    path('', views.OrderListCreateView.as_view(), name='order_list_create'),
    path('<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('<uuid:pk>/assign-warehouse/', views.assign_warehouse, name='order_assign_warehouse'),
    path('<uuid:pk>/generate-label/', views.generate_label, name='order_generate_label'),
    path('<uuid:pk>/tracking-update/', views.tracking_update, name='order_tracking_update'),
    path('import/', views.import_orders, name='orders_import'),

    # Warehouses (legacy)
    path('warehouses/', views.WarehouseListCreateView.as_view(), name='warehouse_list_create'),
    path('warehouses/<uuid:pk>/', views.WarehouseDetailView.as_view(), name='warehouse_detail'),

    # RMA
    path('rma/', views.RMAListCreateView.as_view(), name='rma_list_create'),
    path('rma/<uuid:pk>/', views.RMADetailView.as_view(), name='rma_detail'),
    
    # Multi-Channel Order Management (Enhanced)
    path('multi-channel/', include('orders.enhanced_urls')),
]