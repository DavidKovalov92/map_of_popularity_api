from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_subcribe_email(user_email, location_title):
    send_mail(
            subject="Ви підписались на локацію",
            message=f'Ви успішно підписались на оновлення по локації "{location_title}".',
            from_email="noreply@example.com",
            recipient_list=[user_email],
            fail_silently=False,
        )
    return send_mail()
