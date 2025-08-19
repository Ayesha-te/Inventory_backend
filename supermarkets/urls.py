from django.urls import path
from . import views

urlpatterns = [
    # Supermarkets
    path('', views.SupermarketListCreateView.as_view(), name='supermarket_list_create'),
    path('<uuid:pk>/', views.SupermarketDetailView.as_view(), name='supermarket_detail'),
    path('stats/', views.supermarket_stats, name='supermarket_stats'),
    
    # Staff management
    path('<uuid:supermarket_id>/staff/', views.SupermarketStaffListView.as_view(), name='supermarket_staff_list'),
    
    # Settings
    path('<uuid:supermarket_id>/settings/', views.SupermarketSettingsView.as_view(), name='supermarket_settings'),
]