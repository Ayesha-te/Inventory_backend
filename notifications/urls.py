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
    
    # Reminders
    path('reminders/', views.ReminderListView.as_view(), name='reminder_list'),
    path('reminders/create/', views.ReminderCreateView.as_view(), name='reminder_create'),
    path('reminders/<uuid:pk>/', views.ReminderDetailView.as_view(), name='reminder_detail'),
    path('reminders/logs/', views.ReminderLogListView.as_view(), name='reminder_logs'),
    path('reminders/stats/', views.reminder_stats, name='reminder_stats'),
    path('reminders/upcoming/', views.upcoming_reminders, name='upcoming_reminders'),
    
    # Expiry reminders
    path('reminders/expiry/create/', views.create_expiry_reminder, name='create_expiry_reminder'),
    path('reminders/expiry/bulk-create/', views.create_bulk_expiry_reminders, name='create_bulk_expiry_reminders'),
]