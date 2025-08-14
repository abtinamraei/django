from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, Category, EmailVerificationCode,
    ProductColor, ProductSize, CartItem
)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'size', 'price', 'stock']


class ProductColorSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'hex_code', 'sizes']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    colors = ProductColorSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_id', 'price',
            'description', 'image', 'image_url', 'colors'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_price(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class RegisterWithEmailSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def validate_email(self, value):
        try:
            evc = EmailVerificationCode.objects.get(email=value)
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("ابتدا ایمیل را تایید کنید.")

        if evc.is_expired():
            raise serializers.ValidationError("کد تایید ایمیل منقضی شده است.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        EmailVerificationCode.objects.filter(email=validated_data['email']).delete()
        return user


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_size.color.product.name', read_only=True)
    color_name = serializers.CharField(source='product_size.color.name', read_only=True)
    size = serializers.CharField(source='product_size.size', read_only=True)
    price = serializers.DecimalField(source='product_size.price', max_digits=10, decimal_places=0, read_only=True)
    stock = serializers.IntegerField(source='product_size.stock', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_size', 'quantity', 'product_name', 'color_name', 'size', 'price', 'stock']
