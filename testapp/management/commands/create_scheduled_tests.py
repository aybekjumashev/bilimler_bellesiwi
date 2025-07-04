# testapp/management/commands/create_scheduled_tests.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from testapp.models import Subject, SubjectDay, Test, TestQuestion, Question
import datetime
import random


class Command(BaseCommand):
    help = 'Create scheduled tests based on subject schedules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create tests even if they already exist for today',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Create tests for specific date (YYYY-MM-DD)',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        target_date = options.get('date')
        
        if target_date:
            try:
                target_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            target_date = timezone.now().date()
            print(f'Using current date: {target_date}')
        
        # Get current day of week (1=Monday, 7=Sunday)
        current_weekday = target_date.isoweekday()
        
        # Find subjects scheduled for today
        scheduled_subjects = Subject.objects.filter(
            subject_days__day_of_week=current_weekday
        ).distinct()
        
        if not scheduled_subjects.exists():
            self.stdout.write(
                self.style.WARNING(f'No subjects scheduled for {target_date} (weekday {current_weekday})')
            )
            return
        
        created_tests = 0
        skipped_tests = 0
        errors = 0
        
        for subject in scheduled_subjects:
            try:
                # Check if test already exists for this subject today
                existing_test = Test.objects.filter(
                    subject=subject,
                    created_at__date=target_date
                ).first()
                
                if existing_test and not force:
                    self.stdout.write(
                        self.style.WARNING(f'Test already exists for {subject.name} on {target_date}. ID: {existing_test.id}')
                    )
                    skipped_tests += 1
                    continue
                
                # Check if subject has enough questions
                available_questions = Question.objects.filter(subject=subject)
                if available_questions.count() < subject.questions_count:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Not enough questions for {subject.name}. '
                            f'Required: {subject.questions_count}, Available: {available_questions.count()}'
                        )
                    )
                    errors += 1
                    continue
                
                # Create test
                test = Test.objects.create(
                    subject=subject,
                    is_active=True
                )
                
                # Select random questions
                selected_questions = random.sample(
                    list(available_questions), 
                    subject.questions_count
                )
                
                # Create test-question relationships
                for index, question in enumerate(selected_questions, 1):
                    TestQuestion.objects.create(
                        test=test,
                        question=question,
                        order_number=index
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created test for {subject.name} (ID: {test.id}) with {len(selected_questions)} questions'
                    )
                )
                created_tests += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating test for {subject.name}: {str(e)}')
                )
                errors += 1
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Summary for {target_date} ===\n'
                f'Created: {created_tests} tests\n'
                f'Skipped: {skipped_tests} tests\n'
                f'Errors: {errors} tests\n'
                f'Total subjects processed: {scheduled_subjects.count()}'
            )
        )
