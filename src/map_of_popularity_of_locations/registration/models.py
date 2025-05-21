from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_subscribed = models.BooleanField(default=False, help_text="Отримувати email про нові відгуки.")

    def __str__(self):
        return self.username


