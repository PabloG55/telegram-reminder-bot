from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create the shared SQLAlchemy object (not bound to app yet)
db = SQLAlchemy()
import pytz
ECUADOR_TZ = pytz.timezone("America/Guayaquil")
# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now(ECUADOR_TZ))
    reminder_sent = db.Column(db.Boolean, default=False)
    followup_sent = db.Column(db.Boolean, default=False)
    current_reminder_type = db.Column(db.String(50), default='initial')

    def __repr__(self):
        return f"<Task {self.id} - {self.description}>"
