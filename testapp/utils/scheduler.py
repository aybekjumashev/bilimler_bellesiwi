
# testapp/utils/scheduler.py

import schedule
import time
import threading
import logging
from django.core.management import call_command
from django.conf import settings
import os



logger = logging.getLogger(__name__)

class TestScheduler:
    """
    Avtomatik test yaratish uchun scheduler
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def create_daily_tests(self):
        """Har kuni testlar yaratish"""
        try:
            logger.info("Creating scheduled tests...")
            call_command('create_scheduled_tests')
            logger.info("Successfully created scheduled tests")
        except Exception as e:
            logger.error(f"Error creating scheduled tests: {e}")
    
    def cleanup_old_data(self):
        """Eski ma'lumotlarni tozalash"""
        try:
            logger.info("Cleaning up old data...")
            call_command('cleanup_old_tests', '--days=30')
            logger.info("Successfully cleaned up old data")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def generate_weekly_report(self):
        """Haftalik hisobot yaratish"""
        try:
            logger.info("Generating weekly report...")
            report_path = os.path.join(settings.MEDIA_ROOT, 'reports', 'weekly_report.txt')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            call_command('generate_test_report', '--days=7', '--output', report_path)
            logger.info(f"Weekly report generated: {report_path}")
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
    
    def setup_schedule(self):
        """Schedule setup"""
        # Har kuni ertalab 6:00 da testlar yaratish
        schedule.every().day.at("06:00").do(self.create_daily_tests)
        
        # Har kuni tunda 2:00 da eski ma'lumotlarni tozalash
        schedule.every().day.at("02:00").do(self.cleanup_old_data)
        
        # Har dushanba 8:00 da haftalik hisobot
        schedule.every().monday.at("08:00").do(self.generate_weekly_report)
        
        # Har daqiqada tekshirish (development uchun)
        schedule.every().minute.do(self.check_and_create_tests)
    
    def check_and_create_tests(self):
        """Har daqiqada tekshirish va kerak bo'lsa test yaratish"""
        from django.utils import timezone
        from testapp.models import Subject, SubjectDay, Test
        
        now = timezone.now()
        current_time = now.time()
        current_weekday = now.isoweekday()
        current_date = now.date()
        
        # Hozir boshlanishi kerak bo'lgan fanlarni topish
        scheduled_subjects = Subject.objects.filter(
            subject_days__day_of_week=current_weekday,
            start_time__hour=current_time.hour,
            start_time__minute=current_time.minute
        ).distinct()
        
        for subject in scheduled_subjects:
            # Bugun bu fan uchun test yaratilganmi?
            existing_test = Test.objects.filter(
                subject=subject,
                created_at__date=current_date
            ).first()
            
            if not existing_test:
                try:
                    call_command('create_scheduled_tests', '--force')
                    logger.info(f"Auto-created test for {subject.name}")
                except Exception as e:
                    logger.error(f"Failed to auto-create test for {subject.name}: {e}")
    
    def run_scheduler(self):
        """Scheduler ishga tushirish"""
        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """Scheduler thread ishga tushirish"""
        if not self.running:
            self.setup_schedule()
            self.thread = threading.Thread(target=self.run_scheduler)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Test scheduler started")
    
    def stop(self):
        """Scheduler to'xtatish"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Test scheduler stopped")

# Global scheduler instance
test_scheduler = TestScheduler()



if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    test_scheduler.start()
    while True:
        time.sleep(60)