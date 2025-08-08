from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'emoji', 'description']

class ProductSerializer(serializers.ModelSerializer):
    # برای نمایش کامل دسته‌بندی
    category = CategorySerializer(read_only=True)

    # برای نوشتن (ارسال) دسته‌بندی با شناسه آن
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'category_id', 'price', 'emoji', 'description']
