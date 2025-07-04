# bilim_sinovi/celery.py

import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Periodic tasks schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'create-scheduled-tests': {
        'task': 'testapp.tasks.create_scheduled_tests_task',
        'schedule': crontab(),   # minute='0,10,20,30,40,50'
    },
    # 'cleanup-old-data': {
    #     'task': 'testapp.tasks.cleanup_old_data_task',
    #     'schedule': crontab(minute=0, hour=2),  # Every day at 2:00 AM
    # },
    # 'generate-weekly-report': {
    #     'task': 'testapp.tasks.generate_weekly_report_task',
    #     'schedule': crontab(minute=0, hour=8, day_of_week=1),  # Every Monday at 8:00 AM
    # },
    # 'check-low-questions': {
    #     'task': 'testapp.tasks.check_low_questions_task',
    #     'schedule': crontab(minute=0, hour=9),  # Every day at 9:00 AM
    # },
    # 'backup-database': {
    #     'task': 'testapp.tasks.backup_database_task',
    #     'schedule': crontab(minute=0, hour=1),  # Every day at 1:00 AM
    # },
}

app.conf.timezone = 'Asia/Tashkent'