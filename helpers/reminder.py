from twilio.rest import Client
from helpers.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER
import logging

logger = logging.getLogger(__name__)


def send_reminder(task):
    logger.info(f"Attempting to send reminder for task: {task}")
    try:
        logger.info("Creating Twilio client...")
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        logger.info(f"Sending message from {TWILIO_PHONE_NUMBER} to {USER_PHONE_NUMBER}")
        message = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=USER_PHONE_NUMBER,
            body=f"🔔 Reminder: {task}"
        )
        logger.info(f"Reminder sent successfully: {task} (Message SID: {message.sid})")
    except Exception as e:
        logger.error(f"Failed to send reminder: {task}. Error: {str(e)}")
        raise  # Re-raise the exception so APScheduler can log it
