
# testapp/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Subject, Question, Test, Result
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Subject)
def subject_created_or_updated(sender, instance, created, **kwargs):
    """Signal when subject is created or updated"""
    if created:
        logger.info(f"New subject created: {instance.name} (Grade {instance.grade})")
        # Clear cache
        cache.delete('subjects_list')
    else:
        logger.info(f"Subject updated: {instance.name}")
        cache.delete(f'subject_{instance.id}_stats')


@receiver(post_save, sender=Question)
def question_created(sender, instance, created, **kwargs):
    """Signal when question is created"""
    if created:
        logger.info(f"New question created for {instance.subject.name}")
        # Clear related cache
        cache.delete(f'subject_{instance.subject.id}_stats')


@receiver(post_save, sender=Test)
def test_created(sender, instance, created, **kwargs):
    """Signal when test is created"""
    if created:
        print('AAAAAAAAAAA')
        logger.info(f"New test created: ID {instance.id} for {instance.subject.name}")
        
        # Send notification (if configured)
        from .utils.notifications import NotificationService
        try:
            notification_service = NotificationService()
            # You can add admin emails here
            admin_emails = []  # Configure this
            if admin_emails:
                notification_service.send_test_created_notification(instance, admin_emails)
        except Exception as e:
            logger.error(f"Failed to send test creation notification: {e}")


@receiver(post_save, sender=Result)
def result_submitted(sender, instance, created, **kwargs):
    """Signal when test result is submitted"""
    if created:
        logger.info(f"New result submitted: {instance.student_name} - {instance.score_percentage}%")
        
        # Clear live results cache
        cache.delete(f'live_results_{instance.test.id}')
