import requests
import logging
from flask import current_app as app
import helpers.state as state
from helpers.db import Task
from helpers.config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID

logger = logging.getLogger(__name__)

def send_reminder(task, followup=False):
    logger.info(f"📤 Sending {'follow-up' if followup else 'initial'} reminder for task: {task.description}")

    try:
        with app.app_context():
            if followup:
                state.last_follow_up_task_id = task.id
                logger.info(f"🔁 Set last_follow_up_task_id to: {task.description}")

        # Prepare message
        if followup:
            message_body = f"✅ Did you finish: '{task.description}'? Reply YES or NO"
        else:
            message_body = f"🔔 Reminder: '{task.description}'"

        # Send message via Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_USER_ID,
            "text": message_body
        }
        response = requests.post(url, json=payload)

        if response.ok:
            logger.info("✅ Message sent successfully via Telegram")
        else:
            logger.error(f"❌ Failed to send Telegram message: {response.text}")

    except Exception as e:
        logger.error(f"❌ Error sending Telegram reminder for task {task.id}: {str(e)}")
        raise
