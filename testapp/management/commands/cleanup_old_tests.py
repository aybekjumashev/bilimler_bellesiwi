
# testapp/management/commands/cleanup_old_tests.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from testapp.models import Test, Result
import datetime


class Command(BaseCommand):
    help = 'Cleanup old tests and results'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        # Find old tests
        old_tests = Test.objects.filter(created_at__lt=cutoff_date)
        old_results = Result.objects.filter(completed_at__lt=cutoff_date)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No data will be deleted')
            )
        
        self.stdout.write(
            f'Found {old_tests.count()} tests older than {days} days\n'
            f'Found {old_results.count()} results older than {days} days'
        )
        
        if not dry_run:
            # Delete old results first (due to foreign key constraints)
            deleted_results = old_results.delete()
            deleted_tests = old_tests.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Deleted {deleted_results[0]} results and {deleted_tests[0]} tests'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('Use without --dry-run to actually delete the data')
            )

