"""
Management command to clean up old reminders
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.services import cleanup_old_reminders


class Command(BaseCommand):
    help = 'Clean up old completed/cancelled reminders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days old reminders to keep (default: 90)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days_old = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaning up reminders older than {days_old} days...'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No reminders will be deleted')
            )
            
            # Show what would be deleted
            from notifications.models import Reminder
            cutoff_date = timezone.now() - timedelta(days=days_old)
            
            old_reminders = Reminder.objects.filter(
                status__in=['COMPLETED', 'CANCELLED', 'FAILED'],
                updated_at__lt=cutoff_date
            )
            
            count = old_reminders.count()
            
            if count > 0:
                self.stdout.write(f'Would delete {count} reminders:')
                for reminder in old_reminders[:10]:  # Show first 10
                    self.stdout.write(f'  - {reminder.title} ({reminder.status}) - {reminder.updated_at}')
                
                if count > 10:
                    self.stdout.write(f'  ... and {count - 10} more')
            else:
                self.stdout.write('No reminders to delete')
        else:
            # Actually clean up
            count = cleanup_old_reminders(days_old)
            
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully cleaned up {count} old reminders')
                )
            else:
                self.stdout.write('No old reminders found to clean up')