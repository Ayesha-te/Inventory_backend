"""
Views for notifications and reminders
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import logging

from .models import (
    Notification, NotificationTemplate, EmailNotification,
    NotificationPreference, NotificationDigest, PushNotificationDevice,
    Reminder, ReminderLog
)
from .serializers import (
    NotificationSerializer, NotificationTemplateSerializer, EmailNotificationSerializer,
    NotificationPreferenceSerializer, NotificationDigestSerializer, PushNotificationDeviceSerializer,
    ReminderSerializer, ReminderCreateSerializer, ReminderUpdateSerializer, ReminderLogSerializer,
    ExpiryReminderCreateSerializer, BulkExpiryReminderCreateSerializer, ReminderStatsSerializer
)
from .services import ReminderService, create_bulk_expiry_reminders

User = get_user_model()
logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Notification Views
class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by notification type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a notification"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the user"""
    try:
        updated = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(
            is_read=True, 
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated} notifications marked as read'
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_count(request):
    """Get count of unread notifications"""
    try:
        count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        return Response({'unread_count': count})
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


# Notification Preference Views
class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get or update notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference


# Push Device Views
class PushDeviceListCreateView(generics.ListCreateAPIView):
    """List or create push notification devices"""
    serializer_class = PushNotificationDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PushNotificationDevice.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PushDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a push device"""
    serializer_class = PushNotificationDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PushNotificationDevice.objects.filter(user=self.request.user)


# Notification Template Views (Admin only)
class NotificationTemplateListView(generics.ListCreateAPIView):
    """List or create notification templates"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationTemplate.objects.all()


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a notification template"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationTemplate.objects.all()


# Test notification
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_test_notification(request):
    """Send a test notification"""
    try:
        notification = Notification.objects.create(
            user=request.user,
            notification_type='SYSTEM',
            title='Test Notification',
            message='This is a test notification to verify the system is working.',
            priority='LOW',
            send_email=False,
            send_push=True
        )
        
        return Response({
            'message': 'Test notification created',
            'notification_id': notification.id
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


# Reminder Views
class ReminderListView(generics.ListAPIView):
    """List user reminders"""
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by reminder type
        reminder_type = self.request.query_params.get('type')
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(remind_at__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(remind_at__lte=end_date)
            except ValueError:
                pass
        
        # Filter upcoming reminders
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(
                remind_at__gte=timezone.now(),
                status='ACTIVE'
            )
        
        return queryset.order_by('remind_at')


class ReminderCreateView(generics.CreateAPIView):
    """Create a new reminder"""
    serializer_class = ReminderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Create reminder using the service
        reminder_data = serializer.validated_data
        
        try:
            reminder = ReminderService.create_reminder(
                user=self.request.user,
                **reminder_data
            )
            
            # Return the created reminder data
            self.reminder = reminder
            
        except Exception as e:
            logger.error(f"Error creating reminder: {str(e)}")
            raise
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Serialize the created reminder
        reminder_serializer = ReminderSerializer(self.reminder)
        headers = self.get_success_headers(reminder_serializer.data)
        
        return Response(
            reminder_serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )


class ReminderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a reminder"""
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReminderUpdateSerializer
        return ReminderSerializer
    
    def perform_update(self, serializer):
        # Update reminder using the service
        reminder = self.get_object()
        update_data = serializer.validated_data
        
        try:
            updated_reminder = ReminderService.update_reminder(
                str(reminder.id),
                **update_data
            )
            
            if not updated_reminder:
                raise Exception("Failed to update reminder")
                
        except Exception as e:
            logger.error(f"Error updating reminder: {str(e)}")
            raise
    
    def perform_destroy(self, instance):
        # Cancel reminder using the service
        try:
            success = ReminderService.cancel_reminder(str(instance.id))
            if not success:
                raise Exception("Failed to cancel reminder")
        except Exception as e:
            logger.error(f"Error cancelling reminder: {str(e)}")
            raise


class ReminderLogListView(generics.ListAPIView):
    """List reminder execution logs"""
    serializer_class = ReminderLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # Get logs for user's reminders only
        user_reminders = Reminder.objects.filter(user=self.request.user)
        queryset = ReminderLog.objects.filter(reminder__in=user_reminders)
        
        # Filter by reminder
        reminder_id = self.request.query_params.get('reminder_id')
        if reminder_id:
            queryset = queryset.filter(reminder_id=reminder_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-executed_at')


# Expiry Reminder Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_expiry_reminder(request):
    """Create an expiry reminder for a product"""
    serializer = ExpiryReminderCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            data = serializer.validated_data
            
            # Get supermarket if provided
            supermarket = None
            if data.get('supermarket_id'):
                from supermarkets.models import Supermarket
                try:
                    supermarket = Supermarket.objects.get(
                        id=data['supermarket_id'],
                        user=request.user
                    )
                except Supermarket.DoesNotExist:
                    return Response(
                        {'error': 'Supermarket not found'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create reminder
            reminder = ReminderService.create_expiry_reminder(
                user=request.user,
                product_name=data['product_name'],
                expiry_date=data['expiry_date'],
                days_before=data.get('days_before', 30),
                supermarket=supermarket,
                product_id=data.get('product_id')
            )
            
            # Add custom message if provided
            if data.get('custom_message'):
                reminder.description = data['custom_message']
                reminder.save()
            
            reminder_serializer = ReminderSerializer(reminder)
            return Response(reminder_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating expiry reminder: {str(e)}")
            return Response(
                {'error': 'Failed to create reminder'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_bulk_expiry_reminders(request):
    """Create multiple expiry reminders"""
    serializer = BulkExpiryReminderCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            products_data = []
            
            for product_data in serializer.validated_data['products']:
                # Get supermarket if provided
                supermarket = None
                if product_data.get('supermarket_id'):
                    from supermarkets.models import Supermarket
                    try:
                        supermarket = Supermarket.objects.get(
                            id=product_data['supermarket_id'],
                            user=request.user
                        )
                    except Supermarket.DoesNotExist:
                        continue
                
                products_data.append({
                    'name': product_data['product_name'],
                    'expiry_date': product_data['expiry_date'],
                    'product_id': product_data.get('product_id'),
                    'supermarket': supermarket,
                    'days_before': product_data.get('days_before', 30),
                    'custom_message': product_data.get('custom_message')
                })
            
            # Create reminders
            reminders = create_bulk_expiry_reminders(
                user=request.user,
                products_data=products_data
            )
            
            # Update custom messages if provided
            for i, reminder in enumerate(reminders):
                custom_message = serializer.validated_data['products'][i].get('custom_message')
                if custom_message:
                    reminder.description = custom_message
                    reminder.save()
            
            reminder_serializer = ReminderSerializer(reminders, many=True)
            return Response({
                'message': f'Created {len(reminders)} reminders',
                'reminders': reminder_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating bulk expiry reminders: {str(e)}")
            return Response(
                {'error': 'Failed to create reminders'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reminder_stats(request):
    """Get reminder statistics for the user"""
    try:
        user_reminders = Reminder.objects.filter(user=request.user)
        now = timezone.now()
        
        # Basic counts
        total_reminders = user_reminders.count()
        active_reminders = user_reminders.filter(status='ACTIVE').count()
        completed_reminders = user_reminders.filter(status='COMPLETED').count()
        cancelled_reminders = user_reminders.filter(status='CANCELLED').count()
        failed_reminders = user_reminders.filter(status='FAILED').count()
        
        # Upcoming and overdue
        upcoming_reminders = user_reminders.filter(
            status='ACTIVE',
            remind_at__gte=now
        ).count()
        
        overdue_reminders = user_reminders.filter(
            status='ACTIVE',
            remind_at__lt=now
        ).count()
        
        # By type
        expiry_reminders = user_reminders.filter(reminder_type='EXPIRY').count()
        low_stock_reminders = user_reminders.filter(reminder_type='LOW_STOCK').count()
        custom_reminders = user_reminders.filter(reminder_type='CUSTOM').count()
        
        # Recent activity
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        reminders_sent_today = user_reminders.filter(
            sent_at__date=today
        ).count()
        
        reminders_sent_this_week = user_reminders.filter(
            sent_at__gte=week_ago
        ).count()
        
        reminders_sent_this_month = user_reminders.filter(
            sent_at__gte=month_ago
        ).count()
        
        stats_data = {
            'total_reminders': total_reminders,
            'active_reminders': active_reminders,
            'completed_reminders': completed_reminders,
            'cancelled_reminders': cancelled_reminders,
            'failed_reminders': failed_reminders,
            'upcoming_reminders': upcoming_reminders,
            'overdue_reminders': overdue_reminders,
            'expiry_reminders': expiry_reminders,
            'low_stock_reminders': low_stock_reminders,
            'custom_reminders': custom_reminders,
            'reminders_sent_today': reminders_sent_today,
            'reminders_sent_this_week': reminders_sent_this_week,
            'reminders_sent_this_month': reminders_sent_this_month,
        }
        
        serializer = ReminderStatsSerializer(stats_data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting reminder stats: {str(e)}")
        return Response(
            {'error': 'Failed to get reminder statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upcoming_reminders(request):
    """Get upcoming reminders for the user"""
    try:
        days = int(request.query_params.get('days', 7))  # Default to next 7 days
        
        end_date = timezone.now() + timedelta(days=days)
        
        reminders = Reminder.objects.filter(
            user=request.user,
            status='ACTIVE',
            remind_at__gte=timezone.now(),
            remind_at__lte=end_date
        ).order_by('remind_at')
        
        serializer = ReminderSerializer(reminders, many=True)
        return Response({
            'count': reminders.count(),
            'days': days,
            'reminders': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Error getting upcoming reminders: {str(e)}")
        return Response(
            {'error': 'Failed to get upcoming reminders'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )