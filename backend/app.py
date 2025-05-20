from datetime import datetime

import logger
from flask_cors import CORS

from helpers.reminder import send_reminder
from helpers.config import *
from flask import Flask, request, jsonify, Blueprint
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests
import uuid
from werkzeug.utils import secure_filename
import logging
from requests.auth import HTTPBasicAuth

from helpers.job_utils import remove_jobs_for_task, schedule_jobs_for_task
from helpers.reminder_parser import process_text_command
from helpers.transcriber import transcribe_audio
from helpers.db import db, Task
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
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"check_same_thread": False}}

db.init_app(app)

with app.app_context():
    db.create_all()


# Configure constants
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB
ALLOWED_AUDIO_TYPES = {'audio/wav', 'audio/mp3', 'audio/ogg'}
DOWNLOAD_TIMEOUT = 30  # seconds

@app.route("/bot", methods=["POST"])
def bot():
    logger.info("Incoming Twilio payload:")
    for k, v in request.values.items():
        logger.info(f"  {k}: {v}")
    resp = MessagingResponse()
    msg = resp.message()

    try:
        num_media = int(request.values.get("NumMedia", 0))

        if num_media > 0:
            media_url = request.values.get("MediaUrl0")
            media_type = request.values.get("MediaContentType0")

            if not media_type.startswith("audio/"):
                msg.body("Sorry, I only handle audio messages right now.")
                return str(resp)

            if media_type not in ALLOWED_AUDIO_TYPES:
                msg.body("Sorry, I can only process WAV, MP3, or OGG audio messages.")
                return str(resp)

            filename = f"temp_{uuid.uuid4()}.{secure_filename(media_type.split('/')[-1])}"

            try:
                r = requests.get(
                    media_url,
                    timeout=DOWNLOAD_TIMEOUT,
                    auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                )
                r.raise_for_status()

                if len(r.content) > MAX_CONTENT_LENGTH:
                    msg.body("Sorry, the audio file is too large. Please send a shorter message.")
                    return str(resp)

                with open(filename, "wb") as f:
                    f.write(r.content)

                transcription = transcribe_audio(filename)
                result = process_text_command(transcription)
                if result:
                    msg.body(result)
                else:
                    msg.body(f"You said: \"{transcription}\"")


            except requests.RequestException as e:
                logger.error(f"Error downloading audio: {str(e)}")
                msg.body("❌ Sorry, I couldn't download your voice message.")
            except Exception as e:
                logger.error(f"Error processing audio: {str(e)}")
                msg.body("❌ Sorry, I couldn't process your voice message.")
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
        else:
            body = request.values.get("Body", "").strip()
            result = process_text_command(body)
            logger.info(f"Message body going to Twilio: {result}")
            if result:
                msg.body(result)
            else:
                msg.body(f"You said: \"{body}\"")


    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        msg.body("❌ An unexpected error occurred.")

    return str(resp)


@reminders_bp.route("/run-reminders")
def run_reminders():
    now = datetime.now(ECUADOR_TZ)

    due_tasks = Task.query.filter(
        Task.scheduled_time <= now,
        Task.status.in_(["pending"])
    ).all()

    for task in due_tasks:
        try:
            send_reminder(task)
            db.session.commit()
        except Exception as e:
            logger.error(f"❌ Error sending reminder for task {task.id}: {e}")

    return f"✅ Checked reminders at {now.strftime('%H:%M:%S')}. Sent: {len(due_tasks)}"

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
