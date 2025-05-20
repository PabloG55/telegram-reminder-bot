import re
import logging
from twilio.rest import Client
from flask import current_app as app
import helpers.state as state
from helpers.db import Task
from helpers.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER

logger = logging.getLogger(__name__)

def send_reminder(task):
    logger.info(f"Attempting to send WhatsApp reminder for task: {task}")
    try:
        with app.app_context():
            # Check if it's a follow-up message
            match = re.search(r"Did you finish: '(.+?)'\?", str(task))
            if match:
                description = match.group(1).strip()
                task_obj = Task.query.filter(Task.description.ilike(f"%{description}%")).first()
                if task_obj:
                    state.last_follow_up_task = task_obj
                    logger.info(f"🔁 Setting last_follow_up_task to: {task_obj.description}")

        # Create Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        logger.info(f"Sending WhatsApp message from {TWILIO_PHONE_NUMBER} to {USER_PHONE_NUMBER}")
        message = client.messages.create(
            from_='whatsapp:+14155238886',
            to='whatsapp:+19803587992',
            body=f"🔔 Reminder: {task}"
        )

        logger.info(f"✅ Reminder sent successfully: {task} (Message SID: {message.sid})")

    except Exception as e:
        logger.error(f"❌ Failed to send reminder: {task}. Error: {str(e)}")
        raise


def send_reminder_with_app(task, app):
    with app.app_context():
        send_reminder(task)
