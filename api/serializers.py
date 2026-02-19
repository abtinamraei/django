from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, Category, EmailVerificationCode,
    ProductColor, ProductSize, CartItem, ProductImage,
    ProductReview, Favorite, Coupon
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
        fields = ['id', 'name', 'slug', 'description', 'created_at']


# ------------------ سایز و رنگ ------------------
class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'size', 'price', 'stock', 'sku']


class ProductColorSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta:
        model = ProductColor
        fields = ['id', 'name', 'hex_code', 'order', 'sizes']


# ------------------ تصاویر محصول ------------------
class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'order']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


# ------------------ دیدگاه و امتیاز ------------------
class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_id', 'user_name', 'rating', 'comment', 
                  'is_approved', 'helpful_count', 'created_at']
        read_only_fields = ['user', 'is_approved', 'helpful_count', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


# ------------------ علاقه‌مندی ------------------
class FavoriteSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    product_price = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'product', 'product_name', 'product_image', 'product_price', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.main_image:
            if request:
                return request.build_absolute_uri(obj.product.main_image.url)
            return obj.product.main_image.url
        return None

    def get_product_price(self, obj):
        return float(obj.product.min_price)

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


# ------------------ محصول ------------------
class ProductListSerializer(serializers.ModelSerializer):
    """سریالایزر خلاصه برای لیست محصولات"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image_url = serializers.SerializerMethodField()
    min_price = serializers.FloatField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category_name', 'description',
            'main_image_url', 'min_price', 'average_rating', 
            'reviews_count', 'is_favorite', 'is_active'
        ]

    def get_main_image_url(self, obj):
        request = self.context.get('request')
        if obj.main_image:
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if user and user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False


class ProductDetailSerializer(serializers.ModelSerializer):
    """سریالایزر کامل برای جزئیات محصول"""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    colors = ProductColorSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    
    # فیلدهای محاسباتی
    min_price = serializers.FloatField(read_only=True)
    max_price = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'category_id', 'description',
            'main_image', 'main_image_url', 'price', 'min_price', 'max_price',
            'colors', 'images', 'average_rating', 'reviews_count', 
            'total_stock', 'is_in_stock', 'is_favorite',
            'is_active', 'is_featured', 'view_count', 'sold_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['view_count', 'sold_count', 'created_at', 'updated_at']

    def get_main_image_url(self, obj):
        request = self.context.get('request')
        if obj.main_image:
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None

    def get_max_price(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return max(float(s.price) for s in sizes)
        return float(obj.price)

    def get_is_favorite(self, obj):
        request = self.context.get('request')
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
    product_id = serializers.IntegerField(source='product_size.color.product.id', read_only=True)
    product_name = serializers.CharField(source='product_size.color.product.name', read_only=True)
    product_slug = serializers.CharField(source='product_size.color.product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    
    color_id = serializers.IntegerField(source='product_size.color.id', read_only=True)
    color_name = serializers.CharField(source='product_size.color.name', read_only=True)
    color_hex = serializers.CharField(source='product_size.color.hex_code', read_only=True)
    
    size_id = serializers.IntegerField(source='product_size.id', read_only=True)
    size = serializers.CharField(source='product_size.size', read_only=True)
    price = serializers.FloatField(source='product_size.price', read_only=True)
    stock = serializers.IntegerField(source='product_size.stock', read_only=True)
    sku = serializers.CharField(source='product_size.sku', read_only=True)
    
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'user', 'product_size', 'quantity',
            'product_id', 'product_name', 'product_slug', 'product_image',
            'color_id', 'color_name', 'color_hex',
            'size_id', 'size', 'price', 'stock', 'sku', 'total_price',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_product_image(self, obj):
        request = self.context.get('request')
        product = obj.product_size.color.product
        if product.main_image:
            if request:
                return request.build_absolute_uri(product.main_image.url)
            return product.main_image.url
        return None

    def get_total_price(self, obj):
        return float(obj.product_size.price) * obj.quantity

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("تعداد باید بزرگتر از صفر باشد.")
        return value

    def validate(self, data):
        product_size = data.get('product_size')
        quantity = data.get('quantity', 1)
        
        if product_size and quantity > product_size.stock:
            raise serializers.ValidationError(
                f"موجودی کافی نیست. حداکثر {product_size.stock} عدد موجود است."
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        if not user:
            raise serializers.ValidationError("کاربر مشخص نیست.")

        product_size = validated_data['product_size']
        quantity = validated_data.get('quantity', 1)

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product_size=product_size,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product_size.stock:
                cart_item.quantity = product_size.stock
            cart_item.save()
            
        return cart_item


# ------------------ کوپن تخفیف ------------------
class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_percent', 'max_discount_amount',
            'valid_from', 'valid_to', 'used_count', 'max_uses',
            'is_active', 'is_valid', 'created_at'
        ]
        read_only_fields = ['used_count', 'created_at']