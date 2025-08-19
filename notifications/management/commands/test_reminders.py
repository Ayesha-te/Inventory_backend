"""
Management command to test the reminder system
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from notifications.services import ReminderService, create_bulk_expiry_reminders
from notifications.models import Reminder, ReminderLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the reminder system functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create a test user'
        )
        
        parser.add_argument(
            '--test-basic',
            action='store_true',
            help='Test basic reminder creation'
        )
        
        parser.add_argument(
            '--test-expiry',
            action='store_true',
            help='Test expiry reminder creation'
        )
        
        parser.add_argument(
            '--test-bulk',
            action='store_true',
            help='Test bulk reminder creation'
        )
        
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show reminder statistics'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all tests'
        )
    
    def handle(self, *args, **options):
        if options['all']:
            options.update({
                'create_user': True,
                'test_basic': True,
                'test_expiry': True,
                'test_bulk': True,
                'stats': True
            })
        
        if options['create_user']:
            self.create_test_user()
        
        if options['test_basic']:
            self.test_basic_reminder()
        
        if options['test_expiry']:
            self.test_expiry_reminder()
        
        if options['test_bulk']:
            self.test_bulk_reminders()
        
        if options['stats']:
            self.show_statistics()
    
    def create_test_user(self):
        """Create a test user"""
        try:
            user = User.objects.get(email='test@example.com')
            self.stdout.write(
                self.style.SUCCESS(f'✅ Using existing test user: {user.email}')
            )
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created test user: {user.email}')
            )
        
        return user
    
    def test_basic_reminder(self):
        """Test basic reminder creation"""
        self.stdout.write('\n🧪 Testing Basic Reminder Creation...')
        
        user = self.create_test_user()
        
        try:
            reminder = ReminderService.create_reminder(
                user=user,
                reminder_type='CUSTOM',
                title='Test Reminder - Basic',
                description='This is a test reminder created by management command',
                remind_at=timezone.now() + timedelta(minutes=5),
                send_email=True,
                email_subject='Test Reminder Email'
            )
            
            self.stdout.write(f'✅ Created reminder: {reminder.title}')
            self.stdout.write(f'   ID: {reminder.id}')
            self.stdout.write(f'   Status: {reminder.status}')
            self.stdout.write(f'   Remind at: {reminder.remind_at}')
            self.stdout.write(f'   Task ID: {reminder.task_id}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create basic reminder: {str(e)}')
            )
    
    def test_expiry_reminder(self):
        """Test expiry reminder creation"""
        self.stdout.write('\n🧪 Testing Expiry Reminder Creation...')
        
        user = self.create_test_user()
        
        try:
            expiry_date = timezone.now() + timedelta(days=45)
            reminder = ReminderService.create_expiry_reminder(
                user=user,
                product_name='Test Milk Product',
                expiry_date=expiry_date,
                days_before=30,
                product_id='TEST-MILK-001'
            )
            
            self.stdout.write(f'✅ Created expiry reminder: {reminder.title}')
            self.stdout.write(f'   Product: Test Milk Product')
            self.stdout.write(f'   Expiry Date: {expiry_date}')
            self.stdout.write(f'   Remind at: {reminder.remind_at}')
            self.stdout.write(f'   Days before: {reminder.days_before}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create expiry reminder: {str(e)}')
            )
    
    def test_bulk_reminders(self):
        """Test bulk reminder creation"""
        self.stdout.write('\n🧪 Testing Bulk Expiry Reminders...')
        
        user = self.create_test_user()
        
        try:
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
                days_before=7
            )
            
            self.stdout.write(f'✅ Created {len(reminders)} bulk expiry reminders:')
            for reminder in reminders:
                self.stdout.write(f'   - {reminder.title} (Remind at: {reminder.remind_at})')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create bulk reminders: {str(e)}')
            )
    
    def show_statistics(self):
        """Show reminder statistics"""
        self.stdout.write('\n📊 Reminder Statistics:')
        
        total_reminders = Reminder.objects.count()
        active_reminders = Reminder.objects.filter(status='ACTIVE').count()
        completed_reminders = Reminder.objects.filter(status='COMPLETED').count()
        cancelled_reminders = Reminder.objects.filter(status='CANCELLED').count()
        failed_reminders = Reminder.objects.filter(status='FAILED').count()
        
        self.stdout.write(f'   Total Reminders: {total_reminders}')
        self.stdout.write(f'   Active: {active_reminders}')
        self.stdout.write(f'   Completed: {completed_reminders}')
        self.stdout.write(f'   Cancelled: {cancelled_reminders}')
        self.stdout.write(f'   Failed: {failed_reminders}')
        
        # Show recent reminders
        recent_reminders = Reminder.objects.order_by('-created_at')[:5]
        self.stdout.write(f'\n📝 Recent Reminders:')
        for reminder in recent_reminders:
            self.stdout.write(f'   - {reminder.title} ({reminder.status}) - {reminder.created_at}')
        
        # Show execution logs
        logs = ReminderLog.objects.order_by('-executed_at')[:5]
        self.stdout.write(f'\n📋 Recent Execution Logs:')
        if logs:
            for log in logs:
                self.stdout.write(f'   - {log.reminder.title}')
                self.stdout.write(f'     Status: {log.status}')
                self.stdout.write(f'     Executed: {log.executed_at}')
                if log.error_message:
                    self.stdout.write(f'     Error: {log.error_message}')
        else:
            self.stdout.write('   No execution logs found')
        
        self.stdout.write('\n💡 Next Steps:')
        self.stdout.write('   1. Start Django-Q cluster: python manage.py qcluster')
        self.stdout.write('   2. Check Django admin for created reminders')
        self.stdout.write('   3. Monitor reminder execution in logs')
        self.stdout.write('   4. Test API endpoints using the documentation')