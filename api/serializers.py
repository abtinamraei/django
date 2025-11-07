from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, Category, EmailVerificationCode,
    ProductColor, ProductSize, CartItem, ProductImage,
    ProductReview, Favorite
)

# ------------------ کاربران ------------------
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

# ------------------ دسته‌بندی ------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# ------------------ سایز و رنگ ------------------
class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'size', 'price', 'stock']

class ProductColorSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'hex_code', 'sizes']

# ------------------ تصاویر محصول ------------------
class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'order']

    def get_image_url(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

# ------------------ دیدگاه و امتیاز ------------------
class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

# ------------------ علاقه‌مندی ------------------
class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'product', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

# ------------------ محصول ------------------
class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    colors = ProductColorSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_id', 'price',
            'description', 'colors', 'images',
            'average_rating', 'reviews_count', 'is_favorite'
        ]

    def get_price(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_is_favorite(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = getattr(request, 'user', None) if request else None
        if user and user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False

# ------------------ ایمیل و ثبت‌نام با کد ------------------
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

# ------------------ سبد خرید ------------------
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_size.color.product.name', read_only=True)
    color_name = serializers.CharField(source='product_size.color.name', read_only=True)
    size = serializers.CharField(source='product_size.size', read_only=True)
    price = serializers.DecimalField(source='product_size.price', max_digits=10, decimal_places=0, read_only=True)
    stock = serializers.IntegerField(source='product_size.stock', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_size', 'quantity', 'product_name', 'color_name', 'size', 'price', 'stock']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد باید بزرگتر از صفر باشد.")
        return value

    def create(self, validated_data):
        request = self.context.get('request') if hasattr(self, 'context') else None
        user = request.user if request and hasattr(request, 'user') else None

        if not user:
            raise serializers.ValidationError("کاربر مشخص نیست.")

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product_size=validated_data['product_size'],
            defaults={'quantity': validated_data.get('quantity', 1)}
        )
        if not created:
            cart_item.quantity += validated_data.get('quantity', 1)
            if cart_item.quantity > cart_item.product_size.stock:
                cart_item.quantity = cart_item.product_size.stock
            cart_item.save()
        return cart_item
