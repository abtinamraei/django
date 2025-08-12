from django.db import models
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)  # قیمت پایه (می‌توان قیمت variant را جدا کرد)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50)  # رنگ مثل "قرمز"، "آبی"
    size = models.CharField(max_length=50)   # سایز مثل "S"، "M"، "L"
    price = models.DecimalField(max_digits=10, decimal_places=2)  # قیمت برای این وریانت خاص
    stock = models.PositiveIntegerField(default=0)  # موجودی انبار برای این وریانت

    def __str__(self):
        return f"{self.product.name} - رنگ: {self.color} - سایز: {self.size}"


class EmailVerificationCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)
