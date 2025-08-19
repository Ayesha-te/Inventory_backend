from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('unread-count/', views.get_unread_count, name='unread_notification_count'),
    
    # Notification preferences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification_preferences'),
    
    # Push notification devices
    path('devices/', views.PushDeviceListCreateView.as_view(), name='push_device_list_create'),
    path('devices/<int:pk>/', views.PushDeviceDetailView.as_view(), name='push_device_detail'),
    
    # Notification templates (admin)
    path('templates/', views.NotificationTemplateListView.as_view(), name='notification_template_list'),
    path('templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='notification_template_detail'),
    
    # Test notifications
    path('test/', views.send_test_notification, name='send_test_notification'),
]