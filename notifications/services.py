"""
Reminder services for scheduling and managing reminders using Django-Q
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django_q.tasks import schedule, async_task
from django_q.models import Schedule

from .models import Reminder, ReminderLog, Notification

User = get_user_model()
logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing reminders"""
    
    @staticmethod
    def create_reminder(
        user: User,
        reminder_type: str,
        title: str,
        target_date: datetime = None,
        days_before: int = 30,
        description: str = None,
        supermarket=None,
        related_object_type: str = None,
        related_object_id: str = None,
        frequency: str = 'ONCE',
        is_recurring: bool = False,
        email_subject: str = None,
        email_body: str = None,
        metadata: Dict[str, Any] = None,
        remind_at: datetime = None,
        send_email: bool = True
    ) -> Reminder:
        """
        Create a new reminder and schedule it
        """
        try:
            # Calculate remind_at if target_date is provided and remind_at is not explicitly set
            if not remind_at and target_date:
                remind_at = target_date - timedelta(days=days_before)
            
            # Create reminder instance
            reminder = Reminder.objects.create(
                user=user,
                supermarket=supermarket,
                reminder_type=reminder_type,
                title=title,
                description=description,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                remind_at=remind_at,
                target_date=target_date,
                days_before=days_before,
                frequency=frequency,
                is_recurring=is_recurring,
                email_subject=email_subject,
                email_body=email_body,
                metadata=metadata or {}
            )
            
            # Schedule the reminder task
            if remind_at:
                task_id = ReminderService.schedule_reminder_task(reminder)
                reminder.task_id = task_id
                reminder.save()
            
            logger.info(f"Created reminder {reminder.id} for user {user.id}")
            return reminder
            
        except Exception as e:
            logger.error(f"Error creating reminder: {str(e)}")
            raise
    
    @staticmethod
    def schedule_reminder_task(reminder: Reminder) -> str:
        """
        Schedule a Django-Q task for the reminder
        """
        try:
            # Schedule the task
            scheduled_task = schedule(
                'notifications.services.execute_reminder',
                reminder.id,
                schedule_type=Schedule.ONCE,
                next_run=reminder.remind_at,
                name=f"reminder_{reminder.id}"
            )
            
            logger.info(f"Scheduled reminder task {scheduled_task.name} for {reminder.remind_at}")
            return str(scheduled_task.id)
            
        except Exception as e:
            logger.error(f"Error scheduling reminder task: {str(e)}")
            raise
    
    @staticmethod
    def execute_reminder(reminder_id: str):
        """
        Execute a reminder - send email and create notification
        This function is called by Django-Q
        """
        start_time = timezone.now()
        
        try:
            reminder = Reminder.objects.get(id=reminder_id)
            
            # Check if reminder is still active
            if reminder.status != 'ACTIVE':
                ReminderService._log_reminder_execution(
                    reminder, 'SKIPPED', 
                    error_message=f"Reminder status is {reminder.status}"
                )
                return
            
            # Send email if enabled
            email_sent = False
            email_recipient = None
            
            if reminder.send_email and reminder.user.email:
                email_sent = ReminderService._send_reminder_email(reminder)
                email_recipient = reminder.user.email
            
            # Create in-app notification
            ReminderService._create_notification(reminder)
            
            # Update reminder status
            reminder.is_sent = True
            reminder.sent_at = timezone.now()
            
            # Handle recurring reminders
            if reminder.is_recurring:
                next_reminder_date = ReminderService._calculate_next_reminder(reminder)
                if next_reminder_date:
                    reminder.next_reminder = next_reminder_date
                    # Schedule next occurrence
                    new_task_id = schedule(
                        'notifications.services.execute_reminder',
                        reminder.id,
                        schedule_type=Schedule.ONCE,
                        next_run=next_reminder_date,
                        name=f"reminder_{reminder.id}_next"
                    )
                    reminder.task_id = new_task_id
                else:
                    reminder.status = 'COMPLETED'
            else:
                reminder.status = 'COMPLETED'
            
            reminder.save()
            
            # Log successful execution
            execution_time = (timezone.now() - start_time).total_seconds()
            ReminderService._log_reminder_execution(
                reminder, 'SUCCESS',
                email_sent=email_sent,
                email_recipient=email_recipient,
                execution_time=execution_time
            )
            
            logger.info(f"Successfully executed reminder {reminder_id}")
            
        except Reminder.DoesNotExist:
            logger.error(f"Reminder {reminder_id} not found")
        except Exception as e:
            logger.error(f"Error executing reminder {reminder_id}: {str(e)}")
            
            # Log failed execution
            try:
                reminder = Reminder.objects.get(id=reminder_id)
                reminder.status = 'FAILED'
                reminder.save()
                
                execution_time = (timezone.now() - start_time).total_seconds()
                ReminderService._log_reminder_execution(
                    reminder, 'FAILED',
                    error_message=str(e),
                    execution_time=execution_time
                )
            except:
                pass
    
    @staticmethod
    def _send_reminder_email(reminder: Reminder) -> bool:
        """
        Send reminder email
        """
        try:
            # Use custom subject/body if provided, otherwise use defaults
            subject = reminder.email_subject or f"Reminder: {reminder.title}"
            
            if reminder.email_body:
                message = reminder.email_body
            else:
                # Generate default email body
                context = {
                    'reminder': reminder,
                    'user': reminder.user,
                    'target_date': reminder.target_date,
                    'days_before': reminder.days_before,
                }
                
                # Try to render template, fallback to simple text
                try:
                    message = render_to_string('notifications/reminder_email.html', context)
                except:
                    message = f"""
                    Dear {reminder.user.get_full_name() or reminder.user.email},
                    
                    This is a reminder about: {reminder.title}
                    
                    {reminder.description or ''}
                    
                    {'Target Date: ' + reminder.target_date.strftime('%Y-%m-%d %H:%M') if reminder.target_date else ''}
                    
                    Best regards,
                    Your Inventory Management System
                    """
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reminder.user.email],
                fail_silently=False,
                html_message=message if '<html>' in message.lower() else None
            )
            
            logger.info(f"Sent reminder email to {reminder.user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending reminder email: {str(e)}")
            return False
    
    @staticmethod
    def _create_notification(reminder: Reminder):
        """
        Create in-app notification for the reminder
        """
        try:
            # Map reminder types to notification types
            notification_type_map = {
                'EXPIRY': 'EXPIRY',
                'LOW_STOCK': 'LOW_STOCK',
                'REORDER': 'LOW_STOCK',
                'CUSTOM': 'SYSTEM',
                'MAINTENANCE': 'SYSTEM',
                'REPORT': 'REPORT_READY',
            }
            
            notification_type = notification_type_map.get(reminder.reminder_type, 'SYSTEM')
            
            # Determine priority based on reminder type
            priority_map = {
                'EXPIRY': 'HIGH',
                'LOW_STOCK': 'MEDIUM',
                'REORDER': 'MEDIUM',
                'CUSTOM': 'MEDIUM',
                'MAINTENANCE': 'LOW',
                'REPORT': 'LOW',
            }
            
            priority = priority_map.get(reminder.reminder_type, 'MEDIUM')
            
            # Create notification
            notification = Notification.objects.create(
                user=reminder.user,
                supermarket=reminder.supermarket,
                notification_type=notification_type,
                title=reminder.title,
                message=reminder.description or f"Reminder: {reminder.title}",
                priority=priority,
                related_object_type=reminder.related_object_type,
                related_object_id=reminder.related_object_id,
                send_email=False,  # Email already handled separately
                send_push=True,
                action_data={
                    'reminder_id': str(reminder.id),
                    'reminder_type': reminder.reminder_type,
                    'target_date': reminder.target_date.isoformat() if reminder.target_date else None,
                }
            )
            
            logger.info(f"Created notification {notification.id} for reminder {reminder.id}")
            
        except Exception as e:
            logger.error(f"Error creating notification for reminder: {str(e)}")
    
    @staticmethod
    def _calculate_next_reminder(reminder: Reminder) -> Optional[datetime]:
        """
        Calculate next reminder date for recurring reminders
        """
        if not reminder.is_recurring or not reminder.target_date:
            return None
        
        try:
            current_target = reminder.target_date
            
            if reminder.frequency == 'DAILY':
                next_target = current_target + timedelta(days=1)
            elif reminder.frequency == 'WEEKLY':
                next_target = current_target + timedelta(weeks=1)
            elif reminder.frequency == 'MONTHLY':
                # Add one month (approximate)
                next_target = current_target + timedelta(days=30)
            elif reminder.frequency == 'YEARLY':
                next_target = current_target + timedelta(days=365)
            else:
                return None
            
            # Calculate reminder date (days_before the target)
            next_reminder_date = next_target - timedelta(days=reminder.days_before)
            
            # Only schedule if it's in the future
            if next_reminder_date > timezone.now():
                return next_reminder_date
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating next reminder date: {str(e)}")
            return None
    
    @staticmethod
    def _log_reminder_execution(
        reminder: Reminder,
        status: str,
        email_sent: bool = False,
        email_recipient: str = None,
        error_message: str = None,
        execution_time: float = None
    ):
        """
        Log reminder execution
        """
        try:
            ReminderLog.objects.create(
                reminder=reminder,
                status=status,
                email_sent=email_sent,
                email_recipient=email_recipient,
                error_message=error_message,
                execution_time=execution_time
            )
        except Exception as e:
            logger.error(f"Error logging reminder execution: {str(e)}")
    
    @staticmethod
    def cancel_reminder(reminder_id: str) -> bool:
        """
        Cancel a scheduled reminder
        """
        try:
            reminder = Reminder.objects.get(id=reminder_id)
            
            # Cancel the scheduled task if it exists
            if reminder.task_id:
                try:
                    # Remove from Django-Q schedule
                    Schedule.objects.filter(name=f"reminder_{reminder.id}").delete()
                except:
                    pass
            
            # Update reminder status
            reminder.status = 'CANCELLED'
            reminder.save()
            
            logger.info(f"Cancelled reminder {reminder_id}")
            return True
            
        except Reminder.DoesNotExist:
            logger.error(f"Reminder {reminder_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error cancelling reminder {reminder_id}: {str(e)}")
            return False
    
    @staticmethod
    def update_reminder(
        reminder_id: str,
        **kwargs
    ) -> Optional[Reminder]:
        """
        Update an existing reminder
        """
        try:
            reminder = Reminder.objects.get(id=reminder_id)
            
            # Store old remind_at for comparison
            old_remind_at = reminder.remind_at
            
            # Update fields
            for field, value in kwargs.items():
                if hasattr(reminder, field):
                    setattr(reminder, field, value)
            
            # Recalculate remind_at if target_date or days_before changed
            if 'target_date' in kwargs or 'days_before' in kwargs:
                if reminder.target_date and reminder.days_before:
                    reminder.remind_at = reminder.target_date - timedelta(days=reminder.days_before)
            
            reminder.save()
            
            # Reschedule if remind_at changed and reminder is still active
            if (reminder.remind_at != old_remind_at and 
                reminder.status == 'ACTIVE' and 
                reminder.remind_at > timezone.now()):
                
                # Cancel old task
                if reminder.task_id:
                    try:
                        Schedule.objects.filter(name=f"reminder_{reminder.id}").delete()
                    except:
                        pass
                
                # Schedule new task
                new_task_id = ReminderService.schedule_reminder_task(reminder)
                reminder.task_id = new_task_id
                reminder.save()
            
            logger.info(f"Updated reminder {reminder_id}")
            return reminder
            
        except Reminder.DoesNotExist:
            logger.error(f"Reminder {reminder_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating reminder {reminder_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_user_reminders(
        user: User,
        status: str = None,
        reminder_type: str = None,
        limit: int = None
    ) -> List[Reminder]:
        """
        Get reminders for a user with optional filtering
        """
        try:
            queryset = Reminder.objects.filter(user=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if reminder_type:
                queryset = queryset.filter(reminder_type=reminder_type)
            
            if limit:
                queryset = queryset[:limit]
            
            return list(queryset)
            
        except Exception as e:
            logger.error(f"Error getting user reminders: {str(e)}")
            return []
    
    @staticmethod
    def create_expiry_reminder(
        user: User,
        product_name: str,
        expiry_date: datetime,
        days_before: int = 30,
        supermarket=None,
        product_id: str = None
    ) -> Reminder:
        """
        Convenience method to create product expiry reminders
        """
        return ReminderService.create_reminder(
            user=user,
            reminder_type='EXPIRY',
            title=f"Product Expiry Alert: {product_name}",
            description=f"The product '{product_name}' will expire on {expiry_date.strftime('%Y-%m-%d')}",
            target_date=expiry_date,
            days_before=days_before,
            supermarket=supermarket,
            related_object_type='product',
            related_object_id=product_id,
            email_subject=f"Product Expiry Alert: {product_name}",
            metadata={
                'product_name': product_name,
                'expiry_date': expiry_date.isoformat(),
            }
        )


# Utility functions for common reminder scenarios

def create_bulk_expiry_reminders(user: User, products_data: List[Dict], days_before: int = 30):
    """
    Create expiry reminders for multiple products
    
    products_data format:
    [
        {
            'name': 'Product Name',
            'expiry_date': datetime_object,
            'product_id': 'optional_id',
            'supermarket': supermarket_object  # optional
        },
        ...
    ]
    """
    reminders = []
    
    for product_data in products_data:
        try:
            reminder = ReminderService.create_expiry_reminder(
                user=user,
                product_name=product_data['name'],
                expiry_date=product_data['expiry_date'],
                days_before=days_before,
                supermarket=product_data.get('supermarket'),
                product_id=product_data.get('product_id')
            )
            reminders.append(reminder)
        except Exception as e:
            logger.error(f"Error creating expiry reminder for {product_data.get('name')}: {str(e)}")
    
    return reminders


def cleanup_old_reminders(days_old: int = 90):
    """
    Clean up old completed/cancelled reminders
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        old_reminders = Reminder.objects.filter(
            status__in=['COMPLETED', 'CANCELLED', 'FAILED'],
            updated_at__lt=cutoff_date
        )
        
        count = old_reminders.count()
        old_reminders.delete()
        
        logger.info(f"Cleaned up {count} old reminders")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning up old reminders: {str(e)}")
        return 0