#!/usr/bin/env python
"""
Test script for the Django Reminder System
Run this script to test the reminder functionality
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from notifications.services import ReminderService, create_bulk_expiry_reminders
from notifications.models import Reminder, ReminderLog

User = get_user_model()

def create_test_user():
    """Create a test user if it doesn't exist"""
    try:
        user = User.objects.get(email='test@example.com')
        print(f"✅ Using existing test user: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Created test user: {user.email}")
    
    return user

def test_basic_reminder_creation():
    """Test basic reminder creation"""
    print("\n🧪 Testing Basic Reminder Creation...")
    
    user = create_test_user()
    
    # Create a simple reminder
    reminder = ReminderService.create_reminder(
        user=user,
        reminder_type='CUSTOM',
        title='Test Reminder - Basic',
        description='This is a test reminder created by the test script',
        remind_at=timezone.now() + timedelta(minutes=5),  # 5 minutes from now
        send_email=True,
        email_subject='Test Reminder Email'
    )
    
    print(f"✅ Created reminder: {reminder.title}")
    print(f"   ID: {reminder.id}")
    print(f"   Status: {reminder.status}")
    print(f"   Remind at: {reminder.remind_at}")
    print(f"   Task ID: {reminder.task_id}")
    
    return reminder

def test_expiry_reminder():
    """Test expiry reminder creation"""
    print("\n🧪 Testing Expiry Reminder Creation...")
    
    user = create_test_user()
    
    # Create an expiry reminder
    expiry_date = timezone.now() + timedelta(days=45)  # 45 days from now
    reminder = ReminderService.create_expiry_reminder(
        user=user,
        product_name='Test Milk Product',
        expiry_date=expiry_date,
        days_before=30,  # Remind 30 days before expiry
        product_id='TEST-MILK-001'
    )
    
    print(f"✅ Created expiry reminder: {reminder.title}")
    print(f"   Product: Test Milk Product")
    print(f"   Expiry Date: {expiry_date}")
    print(f"   Remind at: {reminder.remind_at}")
    print(f"   Days before: {reminder.days_before}")
    
    return reminder

def test_bulk_expiry_reminders():
    """Test bulk expiry reminder creation"""
    print("\n🧪 Testing Bulk Expiry Reminders...")
    
    user = create_test_user()
    
    # Create multiple expiry reminders
    products_data = [
        {
            'name': 'Test Bread',
            'expiry_date': timezone.now() + timedelta(days=20),
            'product_id': 'TEST-BREAD-001'
        },
        {
            'name': 'Test Cheese',
            'expiry_date': timezone.now() + timedelta(days=35),
            'product_id': 'TEST-CHEESE-001'
        },
        {
            'name': 'Test Yogurt',
            'expiry_date': timezone.now() + timedelta(days=15),
            'product_id': 'TEST-YOGURT-001'
        }
    ]
    
    reminders = create_bulk_expiry_reminders(
        user=user,
        products_data=products_data,
        days_before=7  # Remind 7 days before expiry
    )
    
    print(f"✅ Created {len(reminders)} bulk expiry reminders:")
    for reminder in reminders:
        print(f"   - {reminder.title} (Remind at: {reminder.remind_at})")
    
    return reminders

def test_recurring_reminder():
    """Test recurring reminder creation"""
    print("\n🧪 Testing Recurring Reminder...")
    
    user = create_test_user()
    
    # Create a recurring reminder
    reminder = ReminderService.create_reminder(
        user=user,
        reminder_type='MAINTENANCE',
        title='Weekly Inventory Check',
        description='Perform weekly inventory audit and stock check',
        target_date=timezone.now() + timedelta(days=7),  # Next week
        days_before=1,  # Remind 1 day before
        frequency='WEEKLY',
        is_recurring=True,
        send_email=True
    )
    
    print(f"✅ Created recurring reminder: {reminder.title}")
    print(f"   Frequency: {reminder.frequency}")
    print(f"   Is recurring: {reminder.is_recurring}")
    print(f"   Next reminder: {reminder.remind_at}")
    
    return reminder

def test_reminder_updates():
    """Test reminder updates"""
    print("\n🧪 Testing Reminder Updates...")
    
    user = create_test_user()
    
    # Create a reminder
    reminder = ReminderService.create_reminder(
        user=user,
        reminder_type='CUSTOM',
        title='Original Title',
        description='Original description',
        remind_at=timezone.now() + timedelta(hours=2)
    )
    
    print(f"✅ Created reminder: {reminder.title}")
    
    # Update the reminder
    updated_reminder = ReminderService.update_reminder(
        str(reminder.id),
        title='Updated Title',
        description='Updated description',
        remind_at=timezone.now() + timedelta(hours=4)
    )
    
    if updated_reminder:
        print(f"✅ Updated reminder: {updated_reminder.title}")
        print(f"   New remind time: {updated_reminder.remind_at}")
    else:
        print("❌ Failed to update reminder")
    
    return updated_reminder

def test_reminder_cancellation():
    """Test reminder cancellation"""
    print("\n🧪 Testing Reminder Cancellation...")
    
    user = create_test_user()
    
    # Create a reminder
    reminder = ReminderService.create_reminder(
        user=user,
        reminder_type='CUSTOM',
        title='Reminder to Cancel',
        remind_at=timezone.now() + timedelta(hours=1)
    )
    
    print(f"✅ Created reminder: {reminder.title} (Status: {reminder.status})")
    
    # Cancel the reminder
    success = ReminderService.cancel_reminder(str(reminder.id))
    
    if success:
        # Refresh from database
        reminder.refresh_from_db()
        print(f"✅ Cancelled reminder: {reminder.title} (Status: {reminder.status})")
    else:
        print("❌ Failed to cancel reminder")
    
    return reminder

def display_reminder_statistics():
    """Display reminder statistics"""
    print("\n📊 Reminder Statistics:")
    
    total_reminders = Reminder.objects.count()
    active_reminders = Reminder.objects.filter(status='ACTIVE').count()
    completed_reminders = Reminder.objects.filter(status='COMPLETED').count()
    cancelled_reminders = Reminder.objects.filter(status='CANCELLED').count()
    failed_reminders = Reminder.objects.filter(status='FAILED').count()
    
    print(f"   Total Reminders: {total_reminders}")
    print(f"   Active: {active_reminders}")
    print(f"   Completed: {completed_reminders}")
    print(f"   Cancelled: {cancelled_reminders}")
    print(f"   Failed: {failed_reminders}")
    
    # Show recent reminders
    recent_reminders = Reminder.objects.order_by('-created_at')[:5]
    print(f"\n📝 Recent Reminders:")
    for reminder in recent_reminders:
        print(f"   - {reminder.title} ({reminder.status}) - {reminder.created_at}")

def display_execution_logs():
    """Display reminder execution logs"""
    print("\n📋 Recent Execution Logs:")
    
    logs = ReminderLog.objects.order_by('-executed_at')[:5]
    
    if logs:
        for log in logs:
            print(f"   - {log.reminder.title}")
            print(f"     Status: {log.status}")
            print(f"     Executed: {log.executed_at}")
            if log.error_message:
                print(f"     Error: {log.error_message}")
            print()
    else:
        print("   No execution logs found")

def main():
    """Main test function"""
    print("🚀 Django Reminder System Test Script")
    print("=" * 50)
    
    try:
        # Run tests
        test_basic_reminder_creation()
        test_expiry_reminder()
        test_bulk_expiry_reminders()
        test_recurring_reminder()
        test_reminder_updates()
        test_reminder_cancellation()
        
        # Display statistics
        display_reminder_statistics()
        display_execution_logs()
        
        print("\n✅ All tests completed successfully!")
        print("\n💡 Next Steps:")
        print("   1. Start Django-Q cluster: python manage.py qcluster")
        print("   2. Check Django admin for created reminders")
        print("   3. Monitor reminder execution in logs")
        print("   4. Test API endpoints using the documentation")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()