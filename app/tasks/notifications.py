import smtplib
from email.mime.text import MIMEText

from app.tasks.celery_app import celery_app
from app.core.config import settings


@celery_app.task(bind=True)
def send_notification(self, task_id: int) -> None:
    """Отправка email-уведомления при смене статуса задачи."""
    from app.db import SessionLocal
    from app.models import Task

    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if not task:
            return
        # Получаем email владельца через relationship
        owner_email = task.owner.email
        subject = f"Task #{task_id} status changed"
        body = f"Task '{task.title}' has new status: {task.status.value}."
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = owner_email

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, [owner_email], msg.as_string())
        except Exception as e:
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e)
    finally:
        db.close()
