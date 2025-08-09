from celery import Celery
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

# Use localhost as default Redis broker/backend to avoid Docker network issues
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/0")

celery = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)

@celery.task
def send_email_async(to_email: str, subject: str, body: str):
    from app.email_utils import send_email_smtp
    send_email_smtp(to_email, subject, body)

@celery.task
def send_daily_overdue_summary():
    from app.database import SessionLocal
    from app import crud, models
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        today = datetime.date.today()
        for user in users:
            overdue_tasks = db.query(models.Task).join(models.Project).filter(
                models.Project.owner_id == user.id,
                models.Task.due_date < today,
                models.Task.status != "done"
            ).all()
            if overdue_tasks:
                body = "Your overdue tasks:\n" + "\n".join([t.title for t in overdue_tasks])
                send_email_smtp(user.email, "Daily Overdue Tasks Summary", body)
    finally:
        db.close()
