
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # # Start scheduler in development mode
    # if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
    #     from django.conf import settings
    #     # if settings.DEBUG:
    #     #     import threading
    #     #     import time
            
    #     #     def start_scheduler():
    #     #         time.sleep(2)  # Wait for Django to start
    #     #         try:
    #     #             from testapp.utils.scheduler import test_scheduler
    #     #             test_scheduler.start()
    #     #             print("✓ Test scheduler started in development mode")
    #     #         except Exception as e:
    #     #             print(f"✗ Failed to start scheduler: {e}")
            
    #     #     scheduler_thread = threading.Thread(target=start_scheduler)
    #     #     scheduler_thread.daemon = True
    #     #     scheduler_thread.start()
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()