from enum import Enum
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Category(Enum):
    RESTAURANT = "Restaurant"
    PARK = "Park"
    MUSEUM = "Museum"
    CAFE = "Cafe"
    THEATER = "Theater"
    SHOP = "Shop"
    OTHER = "Other"

    @classmethod
    def choices(cls):
        return [(key.name, key.value) for key in cls]


class Location(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    category = models.CharField(
        max_length=50,
        choices=Category.choices(),
        default=Category.OTHER.name,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    average_rating = models.FloatField(
        default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    def __str__(self):
        return self.title

    def update_average_rating(self):
        """Calculate and update the average rating based on reviews."""
        reviews = self.reviews.all()
        if reviews.exists():
            average = reviews.aggregate(models.Avg("rating"))["rating__avg"]
            self.average_rating = round(
                average, 1
            ) 
        else:
            self.average_rating = 0.0
        self.save()


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(
        Location, related_name="reviews", on_delete=models.CASCADE
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review by {self.user} on {self.location.title}"


class LikeDislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(
        Review, related_name="likes_dislikes", on_delete=models.CASCADE
    )
    is_like = models.BooleanField() 

    class Meta:
        unique_together = ("user", "review")

    def __str__(self):
        return (
            f"{'Like' if self.is_like else 'Dislike'} by {self.user} on {self.review}"
        )


class LocationSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(
        Location, related_name="subscriptions", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Subscription of {self.user} to {self.location.title}"

    class Meta:
        unique_together = ("user", "location")
