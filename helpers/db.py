from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create the shared SQLAlchemy object (not bound to app yet)
db = SQLAlchemy()

# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.id} - {self.description}>"
