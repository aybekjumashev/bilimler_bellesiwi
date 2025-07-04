from django_cron import CronJobBase, Schedule
from datetime import datetime

class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 1  # Har 1 daqiqada ishlaydi

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'testapp.my_cron_job'  # Unikal kod

    def do(self):
        print(f"Cron ishladi: {datetime.now()}")
        # bu yerga kerakli ishni yozing
