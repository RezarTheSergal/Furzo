from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class AdvancedUser(AbstractBaseUser):
    prefered_tags = ArrayField(models.CharField(max_length=50, blank=True))
    excluded_tags = ArrayField(models.CharField(max_length=50, blank=True))
    is_banned = models.BooleanField(default=False)
    is_banned_until = models.DateTimeField()
    last_username_change = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_username()}"