import re
import dateparser
from flask import request

from helpers.db import db, Task
from helpers.job_utils import schedule_jobs_for_task, remove_jobs_for_task, schedule_still_working_tasks
from helpers.reminder import send_reminder
from helpers.scheduler import scheduler
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def normalize_time_string(time_str):
    """Converts '1118 pm' to '11:18 pm' for better parsing."""
    match = re.match(r"^(\d{1,2})(\d{2})\s*(am|pm|a\.m\.|p\.m\.)$", time_str.replace(".", ""), re.IGNORECASE)
    if match:
        return f"{match.group(1)}:{match.group(2)} {match.group(3)}"
    return time_str

def try_schedule_reminder(text):
    logger.info(f"Processing text: {text}")
    if text.lower().startswith("remind me"):
        logger.info("Found 'remind me' command")

        parts = text.lower().split(" to ", 1)
        if len(parts) < 2:
            return None

        rest = parts[1]
        if " at " in rest:
            task_desc, time_str = rest.rsplit(" at ", 1)
        else:
            task_desc = rest
            time_str = "in 1 minute"

        remind_time = dateparser.parse(time_str, settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()})
        if remind_time < datetime.now():
            logger.warning("Parsed time is in the past, not scheduling.")
            return "❌ That time already passed. Try 'in 1 minute' instead."

        if remind_time:
            logger.info(f"Current time: {datetime.now()}")
            logger.info(f"Reminder time: {remind_time}")

            new_task = Task(description=task_desc, scheduled_time=remind_time)
            db.session.add(new_task)
            db.session.commit()

            schedule_jobs_for_task(new_task)

            logger.info(f"Reminder jobs scheduled for task '{task_desc}' (ID: {new_task.id})")
            return f"✅ Reminder set for '{task_desc}' at {remind_time.strftime('%I:%M %p')}"

    return None



def process_text_command(text):
    text = text.strip()
    logger.info(f"Processing text: {text}")

    if text.lower() == "yes":
        return "✅ Great! Task marked as done."


    elif text.lower() == "no":
        # Try to extract task description from the previous message
        incoming_msg = request.values.get("Body", "")

        # Try to find the quoted task name in the last message
        last_reminder = request.values.get("Context", "") or ""  # fallback if you use a custom context var
        full_text = incoming_msg.strip().lower()


        # Extract the quoted task name using regex
        match = re.search(r"[‘'](.+?)[’']|\bfinish: ['\"](.+?)['\"]", incoming_msg, re.IGNORECASE)
        task_desc = match.group(1) or match.group(2) if match else None

        if not task_desc:
            return "❌ I couldn't figure out which task you're referring to."

        # Look for the task in DB
        task = Task.query.filter(Task.description.ilike(f"%{task_desc}%")).first()
        if not task:
            return f"❌ No task found matching '{task_desc}'."

        schedule_still_working_tasks(task)
        return f"🔁 Got it — I’ll check in again in 1 hour about '{task.description}'."

    if text.lower() in ["what are my tasks", "list all tasks", "show my reminders", "list all reminders"]:
        tasks = Task.query.order_by(Task.scheduled_time.asc()).all()
        if not tasks:
            return "📭 You have no tasks right now."

        response = "📝 Your tasks:\n"
        for task in tasks:
            time = task.scheduled_time.strftime("%b %d at %I:%M %p")
            response += f"• {task.description} — {task.status} at {time}\n"
        return response.strip()

    if text.lower().startswith("delete "):
        try:
            description = text[7:].strip().lower()
            task = Task.query.filter(Task.description.ilike(f"%{description}%")).first()

            if task:
                remove_jobs_for_task(task.id)

                db.session.delete(task)
                db.session.commit()

                return f"🗑️ Task '{task.description}' deleted."
            else:
                return f"❌ No task found matching '{description}'."
        except Exception as e:
            logger.error(f"Error deleting task by name: {e}")
            return "❌ Could not delete task."

    elif text.lower().startswith("edit "):
        try:
            match = re.search(r"edit (.+?) (?:at|to) (.+)", text.lower())
            if not match:
                return "❌ Use format: 'Edit <task name> at <new time>'"

            task_desc = match.group(1).strip()
            time_str = normalize_time_string(match.group(2).strip())
            task = Task.query.filter(Task.description.ilike(f"%{task_desc}%")).first()

            if not task:
                return f"❌ No task found matching '{task_desc}'."

            new_time = dateparser.parse(time_str)
            if not new_time:
                return f"❌ Could not parse the time '{time_str}'. Try something like 'Edit laundry at 9:00pm'."

            remove_jobs_for_task(task.id)

            if task.status == "done":
                task.status = "pending"

            task.scheduled_time = new_time

            db.session.commit()

            schedule_jobs_for_task(task)

            logger.info(f"Task '{task.description}' rescheduled to {new_time}")
            return f"⏰ Task '{task.description}' rescheduled to {new_time.strftime('%I:%M %p')}"

        except Exception as e:
            logger.error(f"Error rescheduling task: {e}")
            return "❌ Failed to reschedule task."

    elif text.lower().startswith("complete "):
        try:
            description = text[9:].strip().lower()
            task = Task.query.filter(Task.description.ilike(f"%{description}%")).first()

            if task:
                remove_jobs_for_task(task.id)
                task.status = "done"
                db.session.commit()
                return f"✅ Task '{task.description}' marked as done."
            else:
                return f"❌ No task found matching '{description}'."
        except Exception as e:
            logger.error(f"Error marking task as done: {e}")
            return "❌ Failed to mark task as done."

    elif text.lower().startswith("remind me"):
        return try_schedule_reminder(text)

    return "❓ I didn't understand that. Try 'remind me...', 'edit task...', or 'delete task...'"
