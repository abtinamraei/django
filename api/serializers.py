from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'emoji', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)  # برای نمایش کامل دسته بندی

    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'price', 'emoji', 'description']