"""
APScheduler configuration.
Daily job: runs every day at 7:00 AM UTC.
Weekly job: runs every Sunday at 8:00 AM UTC.

Run with: python scheduler/jobs.py
Keep this process alive (use Railway's always-on service or a worker dyno).
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler.daily_job import run as daily_run
from scheduler.weekly_job import run as weekly_run

scheduler = BlockingScheduler(timezone="UTC")

scheduler.add_job(
    daily_run,
    CronTrigger(hour=7, minute=0),
    id="daily",
    name="UNFOMO daily",
    max_instances=1,
    coalesce=True,
)

scheduler.add_job(
    weekly_run,
    CronTrigger(day_of_week="sun", hour=8, minute=0),
    id="weekly",
    name="UNFOMO weekly",
    max_instances=1,
    coalesce=True,
)

if __name__ == "__main__":
    print("UNFOMO scheduler started.")
    print("  Daily  → every day at 07:00 UTC")
    print("  Weekly → every Sunday at 08:00 UTC")
    print("  Press Ctrl+C to stop.\n")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
