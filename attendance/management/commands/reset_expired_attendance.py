from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from attendance.models import Attendance


class Command(BaseCommand):
    help = 'Reset attendance records that are older than 15 hours to unattended status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=15,
            help='Number of hours after which attendance should be reset (default: 15)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be reset without actually doing it'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        # Calculate the cutoff time
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find attendance records older than the cutoff time
        expired_attendance = Attendance.objects.filter(
            timestamp__lt=cutoff_time,
            status__in=['present', 'late']  # Only reset present/late, not absent
        )
        
        count = expired_attendance.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would reset {count} attendance records older than {hours} hours'
                )
            )
            
            if count > 0:
                self.stdout.write('Records that would be affected:')
                for record in expired_attendance[:10]:  # Show first 10
                    self.stdout.write(
                        f'  - {record.student.student_id} ({record.student.full_name}) '
                        f'in {record.class_attended.code} on {record.date} at {record.timestamp}'
                    )
                if count > 10:
                    self.stdout.write(f'  ... and {count - 10} more records')
        else:
            if count > 0:
                # Reset the attendance records
                expired_attendance.delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully reset {count} expired attendance records'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No expired attendance records found')
                )
