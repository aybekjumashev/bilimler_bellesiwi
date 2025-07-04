
# testapp/management/commands/generate_test_report.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
from testapp.models import Subject, Test, Result
import datetime
import csv
import os


class Command(BaseCommand):
    help = 'Generate comprehensive test reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['csv', 'txt'],
            default='txt',
            help='Output format (csv or txt)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to include in report (default: 7)',
        )
    
    def handle(self, *args, **options):
        format_type = options['format']
        output_path = options['output']
        days = options['days']
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Gather statistics
        stats = self.gather_statistics(start_date, end_date)
        
        # Generate report
        if format_type == 'csv':
            self.generate_csv_report(stats, output_path, start_date, end_date)
        else:
            self.generate_txt_report(stats, output_path, start_date, end_date)
    
    def gather_statistics(self, start_date, end_date):
        stats = {}
        
        # Overall statistics
        stats['total_tests'] = Test.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).count()
        
        stats['total_participants'] = Result.objects.filter(
            completed_at__date__range=[start_date, end_date]
        ).count()
        
        stats['average_score'] = Result.objects.filter(
            completed_at__date__range=[start_date, end_date]
        ).aggregate(avg_score=Avg('score_percentage'))['avg_score'] or 0
        
        # Subject-wise statistics
        stats['subjects'] = []
        for subject in Subject.objects.all():
            subject_tests = Test.objects.filter(
                subject=subject,
                created_at__date__range=[start_date, end_date]
            )
            
            subject_results = Result.objects.filter(
                test__subject=subject,
                completed_at__date__range=[start_date, end_date]
            )
            
            if subject_tests.exists() or subject_results.exists():
                subject_stats = {
                    'name': subject.name,
                    'grade': subject.grade,
                    'tests_created': subject_tests.count(),
                    'participants': subject_results.count(),
                    'avg_score': subject_results.aggregate(avg=Avg('score_percentage'))['avg'] or 0,
                    'highest_score': subject_results.aggregate(max=Max('score_percentage'))['max'] or 0,
                    'lowest_score': subject_results.aggregate(min=Min('score_percentage'))['min'] or 0,
                }
                stats['subjects'].append(subject_stats)
        
        # Daily statistics
        stats['daily'] = []
        current_date = start_date
        while current_date <= end_date:
            daily_tests = Test.objects.filter(created_at__date=current_date).count()
            daily_participants = Result.objects.filter(completed_at__date=current_date).count()
            daily_avg_score = Result.objects.filter(
                completed_at__date=current_date
            ).aggregate(avg=Avg('score_percentage'))['avg'] or 0
            
            stats['daily'].append({
                'date': current_date,
                'tests': daily_tests,
                'participants': daily_participants,
                'avg_score': daily_avg_score,
            })
            current_date += datetime.timedelta(days=1)
        
        return stats
    
    def generate_txt_report(self, stats, output_path, start_date, end_date):
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("BILIM SINOVI - TEST PLATFORM REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Period: {start_date} to {end_date}")
        report_lines.append(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Overall statistics
        report_lines.append("OVERALL STATISTICS")
        report_lines.append("-" * 30)
        report_lines.append(f"Total Tests Created: {stats['total_tests']}")
        report_lines.append(f"Total Participants: {stats['total_participants']}")
        report_lines.append(f"Average Score: {stats['average_score']:.2f}%")
        report_lines.append("")
        
        # Subject-wise statistics
        if stats['subjects']:
            report_lines.append("SUBJECT-WISE STATISTICS")
            report_lines.append("-" * 30)
            for subject in stats['subjects']:
                report_lines.append(f"Subject: {subject['name']} (Grade {subject['grade']})")
                report_lines.append(f"  Tests Created: {subject['tests_created']}")
                report_lines.append(f"  Participants: {subject['participants']}")
                report_lines.append(f"  Average Score: {subject['avg_score']:.2f}%")
                report_lines.append(f"  Highest Score: {subject['highest_score']:.2f}%")
                report_lines.append(f"  Lowest Score: {subject['lowest_score']:.2f}%")
                report_lines.append("")
        
        # Daily statistics
        report_lines.append("DAILY STATISTICS")
        report_lines.append("-" * 30)
        for daily in stats['daily']:
            if daily['tests'] > 0 or daily['participants'] > 0:
                report_lines.append(
                    f"{daily['date']}: {daily['tests']} tests, "
                    f"{daily['participants']} participants, "
                    f"avg: {daily['avg_score']:.2f}%"
                )
        
        report_content = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.stdout.write(
                self.style.SUCCESS(f'Report saved to {output_path}')
            )
        else:
            self.stdout.write(report_content)
    
    def generate_csv_report(self, stats, output_path, start_date, end_date):
        if not output_path:
            output_path = f'test_report_{start_date}_to_{end_date}.csv'
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Bilim Sinovi Test Report'])
            writer.writerow([f'Period: {start_date} to {end_date}'])
            writer.writerow([''])
            
            # Overall stats
            writer.writerow(['Overall Statistics'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Tests', stats['total_tests']])
            writer.writerow(['Total Participants', stats['total_participants']])
            writer.writerow(['Average Score', f"{stats['average_score']:.2f}%"])
            writer.writerow([''])
            
            # Subject stats
            if stats['subjects']:
                writer.writerow(['Subject Statistics'])
                writer.writerow(['Subject', 'Grade', 'Tests', 'Participants', 'Avg Score', 'Highest', 'Lowest'])
                for subject in stats['subjects']:
                    writer.writerow([
                        subject['name'],
                        subject['grade'],
                        subject['tests_created'],
                        subject['participants'],
                        f"{subject['avg_score']:.2f}%",
                        f"{subject['highest_score']:.2f}%",
                        f"{subject['lowest_score']:.2f}%"
                    ])
        
        self.stdout.write(
            self.style.SUCCESS(f'CSV report saved to {output_path}')
        )