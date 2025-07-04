

# testapp/utils/notifications.py

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Email notification service"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bilimsinovi.com')
    
    def send_test_created_notification(self, test, recipients):
        """Test yaratilganda notification"""
        try:
            subject = f'New Test Created: {test.subject.name}'
            
            context = {
                'test': test,
                'test_url': f"{settings.SITE_URL}/start/?test_id={test.id}",
                'results_url': f"{settings.SITE_URL}/results/?test_id={test.id}",
            }
            
            html_message = render_to_string('emails/test_created.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Test creation notification sent for test {test.id}")
            
        except Exception as e:
            logger.error(f"Failed to send test creation notification: {e}")
    
    def send_low_questions_warning(self, subject, recipients):
        """Kam savol qolganda ogohlantirish"""
        try:
            subject_text = f'Low Questions Warning: {subject.name}'
            
            context = {
                'subject': subject,
                'current_questions': subject.questions.count(),
                'required_questions': subject.questions_count,
                'admin_url': f"{settings.SITE_URL}/admin/questions/?subject={subject.id}",
            }
            
            html_message = render_to_string('emails/low_questions_warning.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject_text,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Low questions warning sent for subject {subject.name}")
            
        except Exception as e:
            logger.error(f"Failed to send low questions warning: {e}")
    
    def send_weekly_report(self, report_data, recipients):
        """Haftalik hisobot email"""
        try:
            subject = f'Weekly Test Report - {report_data["start_date"]} to {report_data["end_date"]}'
            
            context = {
                'report': report_data,
                'admin_url': f"{settings.SITE_URL}/admin/dashboard/",
            }
            
            html_message = render_to_string('emails/weekly_report.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=self.from_email,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info("Weekly report email sent")
            
        except Exception as e:
            logger.error(f"Failed to send weekly report: {e}")