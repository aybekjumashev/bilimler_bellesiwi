
# testapp/apps.py

from django.apps import AppConfig


class TestappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testapp'
    
    def ready(self):
        # Import signal handlers
        import testapp.signals
        
        # # Start scheduler in development mode
        # from django.conf import settings
        # if settings.DEBUG:
        #     from .utils.scheduler import test_scheduler
        #     # test_scheduler.start()  # Uncomment if you want to use scheduler instead of Celery
