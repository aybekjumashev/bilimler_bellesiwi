# testapp/tasks.py

from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Subject, Test, TestQuestion, Question
from .utils.analytics import AnalyticsEngine
from .utils.notifications import NotificationService
import datetime
import logging
import random
import requests
import json

logger = logging.getLogger(__name__)

def send_telegram(tests):
    """Send notification to Telegram channel about new test creation"""
    if not tests:
        return
    
    try:
        test_names = set()
        test_grades = set()
        for test in tests:
            test_names.add(test.subject.name)
            test_grades.add(test.subject.grade)
        
        keyboards = []
        if len(tests) == 1:
            message = f"📌 <b>{tests[0].subject.name}</b> páninen <b>{tests[0].subject.grade}-klasslar</b> ushın test." 
            keyboard = [
                {
                    'text': f'🚀 Qatnasıw',
                    'url': f'{settings.WEB_APP_URL}/test?startapp={tests[0].id}'
                }
            ]
            keyboards.append(keyboard)
        elif len(test_names) == 1:
            sorted_tests = sorted(tests, key=lambda x: x.subject.grade) 
            message = f"<b>📌 {list(test_names)[0]} páninen test.</b>\n" 
            message += f"🎒 {','.join([str(test.subject.grade) for test in sorted_tests])}-klasslar ushın\n\n"
            message += f"@bilimler_bellesiwi | #{list(test_names)[0].lower().replace(' ', '_')}_test"
            # sorted_tests = sorted(tests, key=lambda x: x.subject.grade) 
            # row_keyboards = []
            # for test in sorted_tests[:-2]:
            #     col_keyboards = {
            #             'text': f'{test.subject.grade}',
            #             'url': f'{settings.WEB_APP_URL}/test?startapp={test.id}'
            #         }
            #     row_keyboards.append(col_keyboards)
            # keyboards.append(row_keyboards)
            # row_keyboards = []
            # for test in sorted_tests[-2:]:
            #     col_keyboards = {
            #             'text': f'{test.subject.grade}',
            #             'url': f'{settings.WEB_APP_URL}/test?startapp={test.id}'
            #         }
            #     row_keyboards.append(col_keyboards)
            # keyboards.append(row_keyboards)
            keyboard = [
                    {
                        'text': 'Qatnasıw | Analizlew | Nátiyjeler',
                        'url': f"{settings.WEB_APP_URL}/landing?startapp={'A'.join([str(test.id) for test in tests])}"
                    }
                ]
            keyboards.append(keyboard)

        elif len(test_grades) == 1:
            message = f"📌 <b>{list(test_grades)[0]}-klasslar</b> ushın testler." 
            for test in tests:
                keyboard = [
                    {
                        'text': f'{test.subject.name} ({test.subject.grade}-klass)',
                        'url': f'{settings.WEB_APP_URL}/test?startapp={test.id}'
                    }
                ]
                keyboards.append(keyboard)
        else:
            message = f"📌 {tests[0].subject.start_time.strftime('%H:%M')} waqıtına rejelestirilgen testler." 
            for test in tests:
                keyboard = [
                    {
                        'text': f'{test.subject.name} ({test.subject.grade}-klass)',
                        'url': f'{settings.WEB_APP_URL}/test?startapp={test.id}'
                    }
                ]
                keyboards.append(keyboard)
        
        telegram_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        keyboard = {
            'inline_keyboard': keyboards
        }
        payload = {
            'chat_id': chat_id,
            'text': message,
            'reply_markup': json.dumps(keyboard),
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logger.info(f"Telegram notification sent")
        else:
            logger.error(f"Failed to send Telegram notification for test ID: {test.id}, {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")


def create_scheduled_tests_func(force=False, target_date=None, stdout=None):
    """Subject schedule asosida testlarni yaratish (faqat start_time mos bo'lsa)"""
    if target_date:
        try:
            target_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            if stdout:
                stdout.write('Invalid date format. Use YYYY-MM-DD')
            else:
                print('Invalid date format. Use YYYY-MM-DD')
            return
    else:
        target_date = timezone.now().date()
        if stdout:
            stdout.write(f'Using current date: {target_date}')
        else:
            print(f'Using current date: {target_date}')

    now = timezone.now()
    current_time = now.time()
    current_weekday = target_date.isoweekday()

    # Faqat hozirgi vaqt (soat va daqiqa) start_time ga mos keladigan subjectlar
    scheduled_subjects = Subject.objects.filter(
        subject_days__day_of_week=current_weekday,
        start_time__hour=current_time.hour,
        start_time__minute=current_time.minute
    ).distinct()

    print(current_time)

    if not scheduled_subjects.exists():
        msg = f'No subjects scheduled for {target_date} (weekday {current_weekday}, time {current_time.strftime("%H:%M")})'
        if stdout:
            stdout.write(msg)
        else:
            print(msg)
        return

    created_tests = 0
    skipped_tests = 0
    errors = 0

    tests = []
    for subject in scheduled_subjects:
        print(f'Processing subject: {subject.name} (ID: {subject.id}) Time: {subject.start_time.strftime("%H:%M")}')
        try:
            available_questions = Question.objects.filter(subject=subject)
            if available_questions.count() < subject.questions_count:
                msg = (
                    f'Not enough questions for {subject.name}. '
                    f'Required: {subject.questions_count}, Available: {available_questions.count()}'
                )
                if stdout:
                    stdout.write(msg)
                else:
                    print(msg)
                errors += 1
                continue
            test = Test.objects.create(
                subject=subject,
                is_active=True
            )
            selected_questions = random.sample(
                list(available_questions), 
                subject.questions_count
            )
            for index, question in enumerate(selected_questions, 1):
                TestQuestion.objects.create(
                    test=test,
                    question=question,
                    order_number=index
                )
            
            tests.append(test)

            msg = f'✓ Created test for {subject.name} (ID: {test.id}) with {len(selected_questions)} questions'
            if stdout:
                stdout.write(msg)
            else:
                print(msg)
            created_tests += 1
        except Exception as e:
            msg = f'Error creating test for {subject.name}: {str(e)}'
            if stdout:
                stdout.write(msg)
            else:
                print(msg)
            errors += 1

    send_telegram(tests)

    summary = (
        f'\n=== Summary for {target_date} ===\n'
        f'Created: {created_tests} tests\n'
        f'Skipped: {skipped_tests} tests\n'
        f'Errors: {errors} tests\n'
        f'Total subjects processed: {scheduled_subjects.count()}'
    )
    if stdout:
        stdout.write(summary)
    else:
        print(summary)




@shared_task
def create_scheduled_tests_task():
    """Celery task for creating scheduled tests"""
    try:
        # call_command('create_scheduled_tests')
        create_scheduled_tests_func()
        return "Success: Scheduled tests created"
    except Exception as e:
        logger.error(f"Error creating scheduled tests via Celery: {e}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_data_task(days=30):
    """Celery task for cleaning up old data"""
    try:
        call_command('cleanup_old_tests', f'--days={days}')
        logger.info(f"Old data cleanup completed for {days} days via Celery")
        return f"Success: Cleaned up data older than {days} days"
    except Exception as e:
        logger.error(f"Error cleaning up old data via Celery: {e}")
        return f"Error: {str(e)}"


@shared_task
def generate_weekly_report_task():
    """Celery task for generating weekly reports"""
    try:
        analytics = AnalyticsEngine()
        stats = analytics.get_overall_statistics()
        
        # Generate report data
        report_data = {
            'start_date': (timezone.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
            'end_date': timezone.now().strftime('%Y-%m-%d'),
            'total_tests': stats['total_tests'],
            'total_participants': stats['total_participants'],
            'average_score': stats['average_score'],
            'pass_rate': stats['pass_rate'],
            'top_subjects': analytics.get_subject_performance()[:5],
        }
        
        # Send email report
        notification_service = NotificationService()
        admin_emails = ['admin@example.com']  # Configure admin emails
        notification_service.send_weekly_report(report_data, admin_emails)
        
        logger.info("Weekly report generated and sent via Celery")
        return "Success: Weekly report generated and sent"
        
    except Exception as e:
        logger.error(f"Error generating weekly report via Celery: {e}")
        return f"Error: {str(e)}"


@shared_task
def check_low_questions_task():
    """Check for subjects with low question count"""
    try:
        warning_sent = 0
        
        for subject in Subject.objects.all():
            if not subject.has_enough_questions():
                shortage = subject.questions_count - subject.questions.count()
                if shortage > 0:
                    # Send warning
                    notification_service = NotificationService()
                    admin_emails = ['admin@example.com']  # Configure admin emails
                    notification_service.send_low_questions_warning(subject, admin_emails)
                    warning_sent += 1
        
        logger.info(f"Low questions check completed, {warning_sent} warnings sent")
        return f"Success: {warning_sent} low question warnings sent"
        
    except Exception as e:
        logger.error(f"Error checking low questions via Celery: {e}")
        return f"Error: {str(e)}"


@shared_task
def backup_database_task():
    """Backup database (for SQLite)"""
    try:
        import shutil
        import os
        
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Database backup created: {backup_path}")
        return f"Success: Database backup created at {backup_path}"
        
    except Exception as e:
        logger.error(f"Error creating database backup via Celery: {e}")
        return f"Error: {str(e)}"
