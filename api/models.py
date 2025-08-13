from django.db import models
from django.utils import timezone
from datetime import timedelta

class EmailVerificationCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"{self.email} - {self.code}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="colors")
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductSize(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.color.product.name} - {self.color.name} - {self.size}"
