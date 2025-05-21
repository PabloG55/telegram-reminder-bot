from datetime import timedelta, datetime
from helpers.scheduler import scheduler
from helpers.reminder_sender import send_reminder_with_app
import logging
from flask import current_app
import pytz
ECUADOR_TZ = pytz.timezone("America/Guayaquil")

logger = logging.getLogger(__name__)

def schedule_jobs_for_task(task):
    """Schedules reminder and follow-up jobs for a given task."""
    utc_reminder_time = task.scheduled_time.astimezone(pytz.utc)
    followup_time = utc_reminder_time + timedelta(minutes=1)

    reminder_id = f"reminder_{task.id}_{int(utc_reminder_time.timestamp())}"
    followup_id = f"followup_{task.id}_{int(followup_time.timestamp())}"

    app = current_app._get_current_object()

    scheduler.add_job(
        send_reminder_with_app,
        trigger='date',
        run_date=utc_reminder_time,
        args=[task.description, app],
        id=reminder_id,
        name=f"Reminder for: {task.description}",
        replace_existing=True
    )

    scheduler.add_job(
        send_reminder_with_app,
        trigger='date',
        run_date=followup_time,
        args=[f"✅ Did you finish: '{task.description}'? Reply YES or NO", app],
        id=followup_id,
        name=f"Follow-up for: {task.description}",
        replace_existing=True
    )

    logger.info(f"Scheduled jobs for task {task.id}: {reminder_id}, {followup_id}")

def remove_jobs_for_task(task_id):
    """Removes any reminder/follow-up jobs for the given task ID."""
    for job in scheduler.get_jobs():
        if f"reminder_{task_id}" in job.id or f"followup_{task_id}" in job.id:
            scheduler.remove_job(job.id)
            logger.info(f"Removed job: {job.id}")

def schedule_still_working_tasks(task):
    next_reminder_time = datetime.now(pytz.utc) + timedelta(minutes=1)
    reminder_id = f"followup_{task.id}_{int(next_reminder_time.timestamp())}"

    app = current_app._get_current_object()

    scheduler.add_job(
        send_reminder_with_app,
        trigger='date',
        run_date=next_reminder_time,
        args=[f"🔁 Still working on: '{task.description}'? Reply YES or NO", app],
        id=reminder_id,
        name=f"Follow-up loop for: {task.description}",
        replace_existing=False
    )