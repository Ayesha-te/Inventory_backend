from django.urls import path
from . import views

urlpatterns = [
    # POS Integration management
    path('integrations/', views.POSIntegrationListView.as_view(), name='pos_integration_list'),
    path('integrations/<int:pk>/', views.POSIntegrationDetailView.as_view(), name='pos_integration_detail'),
    path('integrations/create/', views.POSIntegrationCreateView.as_view(), name='pos_integration_create'),
    
    # POS Systems
    path('systems/', views.POSSystemListView.as_view(), name='pos_system_list'),
    
    # Sync operations
    path('integrations/<int:integration_id>/sync/', views.trigger_sync, name='trigger_pos_sync'),
    path('integrations/<int:integration_id>/test/', views.test_connection, name='test_pos_connection'),
    
    # Sync logs
    path('integrations/<int:integration_id>/logs/', views.POSSyncLogListView.as_view(), name='pos_sync_log_list'),
]