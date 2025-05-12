from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from map_of_popularity_of_locations.api.helpers import (
    get_export_csv_cache_key,
    get_likes_dislikes_cache_key,
    get_location_detail_cache_key,
    get_subscription_cache_key,
)
from .models import LikeDislike, Location, Review, LocationSubscription
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


@receiver([post_save, post_delete], sender=Location)
def invalidate_location_caches(sender, instance, **kwargs):
    location_id = instance.id

    cache.delete(get_location_detail_cache_key(location_id))

    (
        cache.delete_pattern("locations:list:*")
        if hasattr(cache, "delete_pattern")
        else None
    )

    cache.delete(get_export_csv_cache_key())


@receiver([post_save, post_delete], sender=Review)
def invalidate_review_caches(sender, instance, **kwargs):
    location = instance.location
    location_id = location.id

    location.update_average_rating()

    (
        cache.delete_pattern(f"reviews:location:{location_id}*")
        if hasattr(cache, "delete_pattern")
        else None
    )

    cache.delete(get_location_detail_cache_key(location_id))

    (
        cache.delete_pattern("locations:list:*")
        if hasattr(cache, "delete_pattern")
        else None
    )


@receiver([post_save, post_delete], sender=LocationSubscription)
def invalidate_subscription_caches(sender, instance, **kwargs):
    user_id = instance.user.id
    location_id = instance.location.id

    cache.delete(get_subscription_cache_key(user_id, location_id))

    cache.delete(f"reviews:user:{user_id}:subscribed")


@receiver([post_save, post_delete], sender=LikeDislike)
def invalidate_likes_dislikes_caches(sender, instance, **kwargs):
    review_id = instance.review.id

    cache.delete(get_likes_dislikes_cache_key(review_id))
