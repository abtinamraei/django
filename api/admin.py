from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import (
    Category, Product, ProductColor, ProductSize, ProductImage,
    CartItem, ProductReview, Favorite
)

# ---------------------- Inline ها ----------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'order']
    ordering = ['order']

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price', 'stock']

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code']
    show_change_link = True

# ---------------------- Product Admin ----------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'min_price', 'average_rating', 'reviews_count']
    list_filter = ['category']
    search_fields = ['name', 'description']
    inlines = [ProductColorInline, ProductImageInline]

    def min_price(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price
    min_price.short_description = 'کمترین قیمت'

    def average_rating(self, obj):
        return obj.average_rating
    average_rating.short_description = 'میانگین امتیاز'

    def reviews_count(self, obj):
        return obj.reviews_count
    reviews_count.short_description = 'تعداد دیدگاه'

# ---------------------- ProductColor Admin ----------------------
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'product']
    inlines = [ProductSizeInline]
    search_fields = ['name', 'product__name']

# ---------------------- ProductSize Admin ----------------------
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'color_name', 'size', 'price', 'stock']
    list_filter = ['color__product', 'color__name']
    search_fields = ['color__product__name', 'color__name', 'size']

    def product_name(self, obj):
        return obj.color.product.name
    product_name.short_description = 'محصول'

    def color_name(self, obj):
        return obj.color.name
    color_name.short_description = 'رنگ'

# ---------------------- CartItem Admin ----------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_name', 'color_name', 'size_name', 'quantity']
    list_filter = ['user', 'product_size__color__product']
    search_fields = ['user__username', 'product_size__color__product__name']

    def product_name(self, obj):
        return obj.product_size.color.product.name
    product_name.short_description = 'محصول'

    def color_name(self, obj):
        return obj.product_size.color.name
    color_name.short_description = 'رنگ'

    def size_name(self, obj):
        return obj.product_size.size
    size_name.short_description = 'سایز'

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            if 'already exists' in str(e):
                existing = CartItem.objects.get(
                    user=obj.user,
                    product_size=obj.product_size
                )
                existing.quantity += obj.quantity
                existing.save()
            else:
                raise e

# ---------------------- ProductReview Admin ----------------------
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'product']
    search_fields = ['product__name', 'user__username', 'comment']
    actions = ['approve_reviews', 'unapprove_reviews']

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'محصول'

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = 'تایید دیدگاه‌ها'

    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_reviews.short_description = 'عدم تایید دیدگاه‌ها'

# ---------------------- Favorite Admin ----------------------
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']  # اصلاح added_at به created_at
    list_filter = ['user', 'product']
    search_fields = ['user__username', 'product__name']
