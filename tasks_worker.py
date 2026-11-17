import os
import time
from celery import Celery

BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"
)

celery_app = Celery("tasks", broker=BROKER_URL)


@celery_app.task
def send_email_notification(task_title: str):
    print(
        f"Отправка уведомления по электронной почте для задачи: {task_title}"
    )
    time.sleep(5)  # Симуляция задержки отправки уведомления
    print(
        f"Уведомление по электронной почте для задачи '{task_title}' отправлено."
    )

    return True
