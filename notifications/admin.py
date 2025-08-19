"""
Django admin configuration for notifications and reminders
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    Notification, NotificationTemplate, EmailNotification,
    NotificationPreference, NotificationDigest, PushNotificationDevice,
    Reminder, ReminderLog
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'notification_type', 'priority', 'is_read', 
        'is_sent', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_sent', 
        'send_email', 'send_push', 'created_at'
    ]
    search_fields = ['title', 'message', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'sent_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'supermarket', 'notification_type', 'priority')
        }),
        ('Content', {
            'fields': ('title', 'message')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Action', {
            'fields': ('action_url', 'action_data'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'read_at', 'sent_at')
        }),
        ('Delivery Channels', {
            'fields': ('send_email', 'send_push', 'send_sms')
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'supermarket')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'default_priority']
    search_fields = ['name', 'title_template', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('Templates', {
            'fields': ('title_template', 'message_template')
        }),
        ('Email Templates', {
            'fields': ('email_subject_template', 'email_body_template'),
            'classes': ('collapse',)
        }),
        ('Default Settings', {
            'fields': ('default_priority', 'default_send_email', 'default_send_push', 'default_send_sms')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ['notification', 'to_email', 'status', 'sent_at', 'retry_count']
    list_filter = ['status', 'sent_at', 'delivered_at']
    search_fields = ['to_email', 'subject', 'notification__title']
    readonly_fields = ['notification', 'created_at', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notification', 'notification__user')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notifications_enabled', 'email_notifications', 'push_notifications', 'digest_frequency']
    list_filter = ['notifications_enabled', 'email_notifications', 'push_notifications', 'digest_frequency']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Global Settings', {
            'fields': ('notifications_enabled', 'email_notifications', 'push_notifications', 'sms_notifications')
        }),
        ('Notification Types', {
            'fields': (
                'low_stock_alerts', 'expiry_alerts', 'out_of_stock_alerts',
                'pos_sync_alerts', 'report_alerts', 'file_processing_alerts', 'system_alerts'
            )
        }),
        ('Timing', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'timezone', 'digest_frequency'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PushNotificationDevice)
class PushNotificationDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'device_name', 'is_active', 'last_used']
    list_filter = ['device_type', 'is_active', 'last_used']
    search_fields = ['user__email', 'device_name', 'device_token']
    readonly_fields = ['created_at', 'last_used']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'reminder_type', 'status', 'remind_at', 
        'is_sent', 'is_recurring', 'created_at'
    ]
    list_filter = [
        'reminder_type', 'status', 'is_recurring', 'frequency', 
        'is_sent', 'send_email', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'user__email', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'id', 'is_sent', 'sent_at', 'task_id', 'next_reminder', 
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'remind_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'supermarket', 'reminder_type', 'status')
        }),
        ('Content', {
            'fields': ('title', 'description')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('remind_at', 'target_date', 'days_before')
        }),
        ('Recurrence', {
            'fields': ('frequency', 'is_recurring', 'next_reminder'),
            'classes': ('collapse',)
        }),
        ('Status & Tracking', {
            'fields': ('is_sent', 'sent_at', 'task_id')
        }),
        ('Email Settings', {
            'fields': ('send_email', 'email_subject', 'email_body'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['cancel_reminders', 'activate_reminders']
    
    def cancel_reminders(self, request, queryset):
        """Cancel selected reminders"""
        from .services import ReminderService
        
        cancelled_count = 0
        for reminder in queryset.filter(status='ACTIVE'):
            if ReminderService.cancel_reminder(str(reminder.id)):
                cancelled_count += 1
        
        self.message_user(
            request, 
            f'Successfully cancelled {cancelled_count} reminders.'
        )
    cancel_reminders.short_description = "Cancel selected reminders"
    
    def activate_reminders(self, request, queryset):
        """Activate selected reminders"""
        now = timezone.now()
        activated_count = 0
        
        for reminder in queryset.filter(status='CANCELLED'):
            if reminder.remind_at > now:
                reminder.status = 'ACTIVE'
                reminder.save()
                activated_count += 1
        
        self.message_user(
            request, 
            f'Successfully activated {activated_count} reminders.'
        )
    activate_reminders.short_description = "Activate selected reminders"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'supermarket')


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = [
        'reminder_title', 'reminder_user', 'status', 'email_sent', 
        'executed_at', 'execution_time'
    ]
    list_filter = ['status', 'email_sent', 'executed_at']
    search_fields = [
        'reminder__title', 'reminder__user__email', 'email_recipient', 'error_message'
    ]
    readonly_fields = [
        'reminder', 'executed_at', 'status', 'email_sent', 'email_recipient',
        'error_message', 'task_id', 'execution_time'
    ]
    date_hierarchy = 'executed_at'
    
    def reminder_title(self, obj):
        return obj.reminder.title
    reminder_title.short_description = 'Reminder'
    reminder_title.admin_order_field = 'reminder__title'
    
    def reminder_user(self, obj):
        return obj.reminder.user.email
    reminder_user.short_description = 'User'
    reminder_user.admin_order_field = 'reminder__user__email'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('reminder', 'reminder__user')


# Custom admin site configuration
admin.site.site_header = "Inventory Management System"
admin.site.site_title = "IMS Admin"
admin.site.index_title = "Welcome to IMS Administration"