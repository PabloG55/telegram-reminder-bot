from datetime import datetime, timedelta

import logger
from helpers.config import *
from flask import Flask, request, render_template, url_for, redirect, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests
import uuid
from werkzeug.utils import secure_filename
import logging
from requests.auth import HTTPBasicAuth

from helpers.job_utils import remove_jobs_for_task, schedule_jobs_for_task
from helpers.reminder import send_reminder
from helpers.reminder_parser import try_schedule_reminder, process_text_command
from helpers.scheduler import scheduler
from helpers.transcriber import transcribe_audio
from helpers.db import db, Task

# Configure logging only once
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


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
                # Download audio with timeout
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

@app.route("/dashboard")
def dashboard():
    from datetime import datetime
    tasks = Task.query.order_by(Task.scheduled_time).all()
    return render_template("dashboard.html", tasks=tasks)


@app.route("/tasks/create", methods=["POST"])
def create_task():
    description = request.form["description"]
    scheduled_time = datetime.strptime(request.form["scheduled_time"], "%Y-%m-%dT%H:%M")

    new_task = Task(description=description, scheduled_time=scheduled_time)
    db.session.add(new_task)
    db.session.commit()

    # Schedule jobs after task has an ID
    schedule_jobs_for_task(new_task)

    return redirect(url_for("dashboard"))


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Remove associated jobs when task is marked done
    remove_jobs_for_task(task.id)

    task.status = "done"
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Remove jobs before deleting task
    remove_jobs_for_task(task.id)

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.description = request.form["description"]
        task.scheduled_time = datetime.strptime(request.form["scheduled_time"], "%Y-%m-%dT%H:%M")

        if task.status == "done":
            task.status = "pending"

        remove_jobs_for_task(task.id)
        db.session.commit()
        schedule_jobs_for_task(task)

        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


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
