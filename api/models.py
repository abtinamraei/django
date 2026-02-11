from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta

# ---------------------- Email Verification Code ----------------------
class EmailVerificationCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """بررسی اینکه کد منقضی شده یا نه (10 دقیقه اعتبار)"""
        if self.created_at is None:  # ✅ هندل کردن None
            return True
        expiration_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"{self.email} - {self.code}"


# ---------------------- Category ----------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ---------------------- Product ----------------------
class Product(models.Model):
    # ارتباط با دسته‌بندی
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    
    # اطلاعات پایه
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, help_text="Base price if no sizes")
    
    # تصاویر
    main_image = models.ImageField(upload_to='products/main/', blank=True, null=True)
    
    # سئو
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # وضعیت
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show in homepage")
    
    # آمار
    view_count = models.PositiveIntegerField(default=0)
    sold_count = models.PositiveIntegerField(default=0)
    
    # تاریخ
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = self.name
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if not reviews.exists():
            return 0
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    @property
    def reviews_count(self):
        return self.reviews.filter(is_approved=True).count()
    
    @property
    def min_price(self):
        """کمترین قیمت با احتساب سایزها"""
        sizes = ProductSize.objects.filter(color__product=self)
        if sizes.exists():
            return min(size.price for size in sizes)
        return self.price
    
    @property
    def total_stock(self):
        """مجموع موجودی"""
        sizes = ProductSize.objects.filter(color__product=self)
        if sizes.exists():
            return sum(size.stock for size in sizes)
        return 0
    
    @property
    def is_in_stock(self):
        return self.total_stock > 0


# ---------------------- Product Images ----------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=100, blank=True, help_text="توضیح برای سئو")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['product', 'order']),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.product.name
        super().save(*args, **kwargs)


# ---------------------- Product Color ----------------------
class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="colors")
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True, null=True, help_text="مثلاً #FF0000")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product', 'order', 'name']
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"


# ---------------------- Product Size ----------------------
class ProductSize(models.Model):
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="کد انبارداری")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['color', 'size']
        unique_together = ('color', 'size')

    def __str__(self):
        return f"{self.color.product.name} - {self.color.name} - {self.size}"

    def save(self, *args, **kwargs):
        if not self.sku and self.color and self.color.product:
            # ساخت SKU خودکار
            product_code = str(self.color.product.id).zfill(4)
            color_code = self.color.name[:2].upper()
            size_code = self.size.replace(' ', '').upper()
            self.sku = f"PRD-{product_code}-{color_code}-{size_code}"
        super().save(*args, **kwargs)


# ---------------------- Cart Item ----------------------
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product_size')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product_size} x {self.quantity}"

    @property
    def total_price(self):
        return self.product_size.price * self.quantity

    def clean(self):
        """بررسی موجودی قبل از اضافه به سبد خرید"""
        if self.quantity > self.product_size.stock:
            from django.core.exceptions import ValidationError
            raise ValidationError(f"موجودی کافی نیست. حداکثر {self.product_size.stock} عدد موجود است.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# ---------------------- Product Review ----------------------
class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating between 1 and 5"
    )
    comment = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0, help_text="تعداد افرادی که این نظر رو مفید دانستند")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating})"

    @property
    def stars(self):
        """نمایش ستاره‌ها به صورت ⭐"""
        return '⭐' * self.rating
    
    @property
    def stars_html(self):
        """نمایش ستاره‌های رنگی"""
        stars = ''
        for i in range(5):
            if i < self.rating:
                stars += '★'
            else:
                stars += '☆'
        return stars


# ---------------------- Favorite ----------------------
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} ❤️ {self.product.name}"


# ---------------------- Discount Coupon ----------------------
class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    valid_from = models.DateTimeField(null=True, blank=True)  # ✅ اصلاح: اجازه null
    valid_to = models.DateTimeField(null=True, blank=True)    # ✅ اصلاح: اجازه null
    used_count = models.PositiveIntegerField(default=0)
    max_uses = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def is_valid(self):
        """بررسی اعتبار کوپن با هندل کردن مقادیر None"""
        now = timezone.now()
        
        # ✅ اگر تاریخ شروع یا پایان نداشت، کوپن نامعتبر است
        if self.valid_from is None or self.valid_to is None:
            return False
            
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and 
                self.used_count < self.max_uses)