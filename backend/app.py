import hashlib
import hmac
import time
from datetime import datetime, timedelta

import logger
from flask_cors import CORS

from helpers.reminder_sender import send_reminder
from helpers.config import *
from flask import Flask, request, jsonify, Blueprint
import os
import requests
import uuid
import logging

from helpers.job_utils import remove_jobs_for_task, schedule_jobs_for_task
from helpers.reminder_parser import process_text_command
from helpers.transcriber import transcribe_audio
from helpers.db import db, Task, User
import pytz
ECUADOR_TZ = pytz.timezone("America/Guayaquil")
# Configure logging only once
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
reminders_bp = Blueprint('reminders', __name__)
CORS(app, supports_credentials=True)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "connect_args": {"sslmode": "require"},
}

db.init_app(app)

with app.app_context():
    db.create_all()

# Configure constants
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB
ALLOWED_AUDIO_TYPES = {'audio/wav', 'audio/mp3', 'audio/ogg'}
DOWNLOAD_TIMEOUT = 30  # seconds
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@app.route("/api/login", methods=["POST"])
def telegram_login():
    logger.info("🔐 Telegram login attempt received.")
    data = request.json
    logger.info(f"📥 Payload: {data}")

    hash_to_check = data.pop("hash", None)
    auth_date = int(data.get("auth_date", 0))

    if not hash_to_check:
        logger.warning("❌ Missing hash in login request.")
        return jsonify({"error": "Missing hash"}), 400

    # Reject old logins (older than 24h)
    if abs(time.time() - auth_date) > 86400:
        logger.warning("❌ Login expired. auth_date: %s", auth_date)
        return jsonify({"error": "Login expired"}), 400

    # Check hash
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    logger.debug(f"🔒 Computed hash: {computed_hash}")
    logger.debug(f"🔑 Provided hash: {hash_to_check}")

    if not hmac.compare_digest(computed_hash, hash_to_check):
        logger.warning("❌ Hash mismatch - invalid login attempt.")
        return jsonify({"error": "Invalid login"}), 403

    telegram_id = data["id"]
    logger.info(f"✅ Telegram login verified for user_id: {telegram_id}")

    # Check or create user
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        logger.info("👤 New user detected. Creating user...")
        user = User(
            telegram_id=telegram_id,
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            photo_url=data.get("photo_url")
        )
        db.session.add(user)
    else:
        logger.info("🔄 Existing user. Updating info if needed.")
        user.username = data.get("username")
        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.photo_url = data.get("photo_url")

    db.session.commit()
    logger.info(f"✅ User login processed successfully: {telegram_id}")

    return jsonify({ "ok": True, "telegram_id": telegram_id })


@app.route("/bot", methods=["POST"])
def bot():
    data = request.get_json()
    logger.info("📥 Incoming Telegram payload:")
    logger.info(data)

    try:
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")

        if not chat_id:
            return jsonify({"ok": True})  # Ignore if no chat

        # Handle voice messages
        if "voice" in message:
            file_id = message["voice"]["file_id"]

            # Step 1: Get a file path from Telegram
            file_info = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

            # Download the voice file
            r = requests.get(file_url, timeout=DOWNLOAD_TIMEOUT)
            r.raise_for_status()

            # Check file size
            if len(r.content) > MAX_CONTENT_LENGTH:
                reply = "❌ Sorry, the audio file is too large. Please send a shorter message."
            else:
                # Save the file
                filename = f"temp_{uuid.uuid4()}.ogg"
                with open(filename, "wb") as f:
                    f.write(r.content)

                try:
                    # Transcribe and process
                    transcription = transcribe_audio(filename)
                    result = process_text_command(transcription)
                    reply = result or f"❌ I couldn't understand: \"{transcription}\""
                except Exception as e:
                    logger.error(f"❌ Error processing audio: {str(e)}")
                    reply = "❌ Sorry, I couldn't process your voice message."
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)

        else:
            # Handle text messages
            text = message.get("text", "").strip()
            result = process_text_command(text)
            reply = result or f"❌ I couldn't understand: \"{text}\""

        # Send reply to user
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply
        })

    except Exception as e:
        logger.error(f"❌ Unexpected error in /bot: {str(e)}")
        # Try to send fallback error
        if "chat_id" in locals():
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": "❌ An unexpected error occurred."
            })

    return jsonify({"ok": True})

@reminders_bp.route("/run-reminders")
def run_reminders():
    now = datetime.now(ECUADOR_TZ)
    sent_count = 0

    # Initial reminders
    tasks = Task.query.filter(
        Task.scheduled_time <= now,
        Task.status == "pending",
        Task.reminder_sent == False
    ).all()

    for task in tasks:
        try:
            send_reminder(task)
            task.reminder_sent = True
            task.reminder_sent_at = now
            db.session.commit()
            sent_count += 1
        except Exception as e:
            logger.error(f"❌ Error sending reminder for task {task.id}: {e}")

    # Follow-ups (1h after original reminder)
    followup_tasks = Task.query.filter(
        Task.status == "pending",
        Task.reminder_sent == True,
        Task.reminder_sent_at <= now - timedelta(hours=1)
    ).all()

    for task in followup_tasks:
        try:
            send_reminder(task, followup=True)
            task.followup_sent = True
            task.reminder_sent_at = now
            db.session.commit()
            sent_count += 1
        except Exception as e:
            logger.error(f"❌ Error sending follow-up for task {task.id}: {e}")

    return f"✅ Checked reminders at {now.strftime('%H:%M:%S')}. Sent: {sent_count}"


app.register_blueprint(reminders_bp)


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    tasks = Task.query.order_by(Task.scheduled_time.asc()).all()
    return jsonify([{
        "id": task.id,
        "description": task.description,
        "scheduled_time": task.scheduled_time.isoformat(),
        "status": task.status
    } for task in tasks])

@app.route("/api/tasks/create", methods=["POST"])
def api_create_task():
    data = request.get_json()
    description = data.get("description")
    scheduled_time = datetime.fromisoformat(data.get("scheduled_time"))

    new_task = Task(description=description, scheduled_time=scheduled_time)
    db.session.add(new_task)
    db.session.commit()

    schedule_jobs_for_task(new_task)
    return jsonify({"message": "Task created", "id": new_task.id}), 201

@app.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
def api_complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    remove_jobs_for_task(task.id)
    task.status = "done"
    db.session.commit()
    return jsonify({"message": f"Task {task.id} marked as done."})

@app.route("/api/tasks/<int:task_id>/reschedule", methods=["POST"])
def api_reschedule_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.status == "done":
        task.status = "pending"
        remove_jobs_for_task(task.id)
        db.session.commit()
        schedule_jobs_for_task(task)

    return jsonify({
        "message": f"Task {task.id} rescheduled",
        "task_id": task.id,
        "scheduled_time": task.scheduled_time.isoformat()
    })

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    remove_jobs_for_task(task.id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": f"Task {task.id} deleted."})

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    task.description = data.get("description", task.description)
    task.scheduled_time = datetime.fromisoformat(data.get("scheduled_time"))
    if task.status == "done":
        task.status = "pending"

    remove_jobs_for_task(task.id)
    db.session.commit()
    schedule_jobs_for_task(task)
    return jsonify({"message": f"Task {task.id} updated."})

@app.route("/jobs")
def jobs():
    from helpers.scheduler import scheduler
    jobs = scheduler.get_jobs()
    job_list = [{
        "id": job.id,
        "name": job.name,
        "next_run_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
    } for job in jobs]

    return jsonify(job_list)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=False)
