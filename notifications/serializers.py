"""
Serializers for notifications and reminders
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Notification, NotificationTemplate, EmailNotification,
    NotificationPreference, NotificationDigest, PushNotificationDevice,
    Reminder, ReminderLog
)

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'supermarket', 'notification_type', 'title', 'message',
            'priority', 'related_object_type', 'related_object_id', 'action_url',
            'action_data', 'is_read', 'is_sent', 'read_at', 'send_email',
            'send_push', 'send_sms', 'created_at', 'scheduled_for', 'sent_at'
        ]
        read_only_fields = ['id', 'user', 'is_sent', 'sent_at', 'created_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model"""
    
    class Meta:
        model = NotificationTemplate
        fields = '__all__'


class EmailNotificationSerializer(serializers.ModelSerializer):
    """Serializer for EmailNotification model"""
    
    class Meta:
        model = EmailNotification
        fields = '__all__'
        read_only_fields = ['notification', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""
    
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class NotificationDigestSerializer(serializers.ModelSerializer):
    """Serializer for NotificationDigest model"""
    
    class Meta:
        model = NotificationDigest
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class PushNotificationDeviceSerializer(serializers.ModelSerializer):
    """Serializer for PushNotificationDevice model"""
    
    class Meta:
        model = PushNotificationDevice
        fields = '__all__'
        read_only_fields = ['user', 'last_used', 'created_at']


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for Reminder model"""
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'user', 'supermarket', 'reminder_type', 'title', 'description',
            'related_object_type', 'related_object_id', 'remind_at', 'target_date',
            'days_before', 'frequency', 'is_recurring', 'next_reminder', 'status',
            'is_sent', 'sent_at', 'task_id', 'send_email', 'email_subject',
            'email_body', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'is_sent', 'sent_at', 'task_id', 'next_reminder',
            'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate reminder data"""
        
        # If target_date is provided, ensure it's in the future
        if data.get('target_date'):
            if data['target_date'] <= timezone.now():
                raise serializers.ValidationError(
                    "Target date must be in the future"
                )
        
        # If remind_at is provided, ensure it's in the future
        if data.get('remind_at'):
            if data['remind_at'] <= timezone.now():
                raise serializers.ValidationError(
                    "Reminder time must be in the future"
                )
        
        # Validate days_before
        days_before = data.get('days_before', 30)
        if days_before < 0:
            raise serializers.ValidationError(
                "Days before must be a positive number"
            )
        
        # If both target_date and remind_at are provided, ensure consistency
        if data.get('target_date') and data.get('remind_at'):
            expected_remind_at = data['target_date'] - timedelta(days=days_before)
            if abs((data['remind_at'] - expected_remind_at).total_seconds()) > 3600:  # 1 hour tolerance
                raise serializers.ValidationError(
                    "Remind time is not consistent with target date and days_before"
                )
        
        return data


class ReminderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reminders with additional validation"""
    
    class Meta:
        model = Reminder
        fields = [
            'supermarket', 'reminder_type', 'title', 'description',
            'related_object_type', 'related_object_id', 'remind_at', 'target_date',
            'days_before', 'frequency', 'is_recurring', 'send_email',
            'email_subject', 'email_body', 'metadata'
        ]
    
    def validate(self, data):
        """Validate reminder creation data"""
        
        # Either remind_at or target_date must be provided
        if not data.get('remind_at') and not data.get('target_date'):
            raise serializers.ValidationError(
                "Either 'remind_at' or 'target_date' must be provided"
            )
        
        # If target_date is provided, ensure it's in the future
        if data.get('target_date'):
            if data['target_date'] <= timezone.now():
                raise serializers.ValidationError(
                    "Target date must be in the future"
                )
        
        # If remind_at is provided, ensure it's in the future
        if data.get('remind_at'):
            if data['remind_at'] <= timezone.now():
                raise serializers.ValidationError(
                    "Reminder time must be in the future"
                )
        
        # Validate days_before
        days_before = data.get('days_before', 30)
        if days_before < 0:
            raise serializers.ValidationError(
                "Days before must be a positive number"
            )
        
        # Validate recurring settings
        if data.get('is_recurring', False):
            if not data.get('target_date'):
                raise serializers.ValidationError(
                    "Target date is required for recurring reminders"
                )
            
            frequency = data.get('frequency', 'ONCE')
            if frequency == 'ONCE':
                raise serializers.ValidationError(
                    "Frequency cannot be 'ONCE' for recurring reminders"
                )
        
        return data


class ReminderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reminders"""
    
    class Meta:
        model = Reminder
        fields = [
            'title', 'description', 'remind_at', 'target_date', 'days_before',
            'frequency', 'is_recurring', 'status', 'send_email', 'email_subject',
            'email_body', 'metadata'
        ]
    
    def validate_status(self, value):
        """Validate status changes"""
        if self.instance and self.instance.status in ['COMPLETED', 'FAILED']:
            if value not in ['CANCELLED']:
                raise serializers.ValidationError(
                    "Cannot change status from completed/failed to active"
                )
        return value
    
    def validate(self, data):
        """Validate reminder update data"""
        
        # If target_date is being updated, ensure it's in the future
        if 'target_date' in data and data['target_date']:
            if data['target_date'] <= timezone.now():
                raise serializers.ValidationError(
                    "Target date must be in the future"
                )
        
        # If remind_at is being updated, ensure it's in the future
        if 'remind_at' in data and data['remind_at']:
            if data['remind_at'] <= timezone.now():
                raise serializers.ValidationError(
                    "Reminder time must be in the future"
                )
        
        # Validate days_before
        if 'days_before' in data:
            if data['days_before'] < 0:
                raise serializers.ValidationError(
                    "Days before must be a positive number"
                )
        
        return data


class ReminderLogSerializer(serializers.ModelSerializer):
    """Serializer for ReminderLog model"""
    
    reminder_title = serializers.CharField(source='reminder.title', read_only=True)
    reminder_type = serializers.CharField(source='reminder.reminder_type', read_only=True)
    
    class Meta:
        model = ReminderLog
        fields = [
            'id', 'reminder', 'reminder_title', 'reminder_type', 'executed_at',
            'status', 'email_sent', 'email_recipient', 'error_message',
            'task_id', 'execution_time'
        ]
        read_only_fields = '__all__'


class ExpiryReminderCreateSerializer(serializers.Serializer):
    """Serializer for creating expiry reminders"""
    
    product_name = serializers.CharField(max_length=255)
    expiry_date = serializers.DateTimeField()
    days_before = serializers.IntegerField(default=30, min_value=1, max_value=365)
    supermarket_id = serializers.UUIDField(required=False, allow_null=True)
    product_id = serializers.CharField(max_length=100, required=False, allow_null=True)
    custom_message = serializers.CharField(max_length=500, required=False, allow_null=True)
    
    def validate_expiry_date(self, value):
        """Validate expiry date"""
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Expiry date must be in the future"
            )
        return value
    
    def validate(self, data):
        """Validate the reminder will be scheduled in the future"""
        expiry_date = data['expiry_date']
        days_before = data.get('days_before', 30)
        
        remind_at = expiry_date - timedelta(days=days_before)
        if remind_at <= timezone.now():
            raise serializers.ValidationError(
                f"Reminder would be scheduled in the past. "
                f"Reduce days_before or choose a later expiry date."
            )
        
        return data


class BulkExpiryReminderCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple expiry reminders"""
    
    products = serializers.ListField(
        child=ExpiryReminderCreateSerializer(),
        min_length=1,
        max_length=100
    )
    
    def validate_products(self, value):
        """Validate products list"""
        if not value:
            raise serializers.ValidationError("At least one product is required")
        
        # Check for duplicate product names
        product_names = [product['product_name'] for product in value]
        if len(product_names) != len(set(product_names)):
            raise serializers.ValidationError("Duplicate product names are not allowed")
        
        return value


class ReminderStatsSerializer(serializers.Serializer):
    """Serializer for reminder statistics"""
    
    total_reminders = serializers.IntegerField(read_only=True)
    active_reminders = serializers.IntegerField(read_only=True)
    completed_reminders = serializers.IntegerField(read_only=True)
    cancelled_reminders = serializers.IntegerField(read_only=True)
    failed_reminders = serializers.IntegerField(read_only=True)
    upcoming_reminders = serializers.IntegerField(read_only=True)
    overdue_reminders = serializers.IntegerField(read_only=True)
    
    # By type
    expiry_reminders = serializers.IntegerField(read_only=True)
    low_stock_reminders = serializers.IntegerField(read_only=True)
    custom_reminders = serializers.IntegerField(read_only=True)
    
    # Recent activity
    reminders_sent_today = serializers.IntegerField(read_only=True)
    reminders_sent_this_week = serializers.IntegerField(read_only=True)
    reminders_sent_this_month = serializers.IntegerField(read_only=True)