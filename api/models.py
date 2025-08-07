from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # در صورت نیاز می‌تونی فیلدهای اضافه هم بزاری
    pass

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
