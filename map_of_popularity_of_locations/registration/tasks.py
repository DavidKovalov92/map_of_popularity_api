from celery import shared_task
from .utils import Util
from django.conf import settings

@shared_task
def send_subcribe_email(email_body, user_email):
    data = {
                "email_body": email_body,
                "to_email": user_email,
                "email_subject": "Reset your password",
            }
    send_mail = Util.send_email(data)
    return send_mail
