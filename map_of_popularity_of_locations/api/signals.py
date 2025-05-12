from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Review, LocationSubscription
from registration.utils import Util


@receiver(post_save, sender=Review)
def notify_subscribers(sender, instance, created, **kwargs):
    if created:
        location = instance.location
        subscriptions = LocationSubscription.objects.filter(location=location)

        for subscription in subscriptions:
            user = subscription.user
            email_data = {
                "email_subject": f"New review for {location.title}",
                "email_body": f"A new review has been posted for {location.title}: {instance.comment}",
                "to_email": user.email,
            }
            Util.send_email(email_data)
