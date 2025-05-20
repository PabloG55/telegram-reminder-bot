import re
import logging
from twilio.rest import Client
from flask import current_app as app
import helpers.state as state
from helpers.db import Task
from helpers.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER

logger = logging.getLogger(__name__)

def send_reminder(task, followup=False):
    logger.info(f"📤 Sending {'follow-up' if followup else 'initial'} reminder for task: {task.description}")

    try:
        with app.app_context():
            # Save task in global state if it's a follow-up (for response tracking)
            if followup:
                state.last_follow_up_task = task
                logger.info(f"🔁 Set last_follow_up_task to: {task.description}")

        # Prepare message text
        if followup:
            message_body = f"✅ Did you finish: '{task.description}'? Reply YES or NO"
        else:
            message_body = f"🔔 Reminder: {task.description}"

        # Send message via Twilio WhatsApp
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=USER_PHONE_NUMBER,
            body=message_body
        )

        logger.info(f"✅ Message sent (SID: {message.sid})")

    except Exception as e:
        logger.error(f"❌ Failed to send reminder for task {task.id}: {str(e)}")
        raise


def send_reminder_with_app(task, app):
    with app.app_context():
        send_reminder(task)
