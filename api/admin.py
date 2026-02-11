from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import (
    Category, Product, ProductColor, ProductSize, ProductImage,
    CartItem, ProductReview, Favorite
)

# ---------------------- Category Admin ----------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}
    ordering = ['name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'description')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

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
    ordering = ['size']

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code']
    show_change_link = True
    ordering = ['name']

# ---------------------- Product Admin ----------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'min_price', 'stock_status', 'average_rating', 'reviews_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ProductColorInline, ProductImageInline]
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('category', 'name', 'slug', 'description', 'price')
        }),
        ('تصویر شاخص', {
            'fields': ('main_image',),
            'classes': ('wide',)
        }),
        ('تنظیمات سئو', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'reviews_count']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def min_price(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price
    min_price.short_description = 'کمترین قیمت'
    min_price.admin_order_field = 'price'
    
    def stock_status(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            total_stock = sum(size.stock for size in sizes)
            if total_stock > 10:
                return '✅ موجود'
            elif total_stock > 0:
                return '⚠️ محدود'
            return '❌ ناموجود'
        return '❌ ناموجود'
    stock_status.short_description = 'وضعیت موجودی'
    
    def average_rating(self, obj):
        return f'{obj.average_rating:.1f} ⭐'
    average_rating.short_description = 'امتیاز'
    
    def reviews_count(self, obj):
        return obj.reviews_count
    reviews_count.short_description = 'دیدگاه'
    
    actions = ['duplicate_product', 'update_prices']
    
    def duplicate_product(self, request, queryset):
        for product in queryset:
            product.pk = None
            product.name = f'{product.name} (کپی)'
            product.slug = f'{product.slug}-copy'
            product.save()
            
            # کپی کردن رنگ‌ها و سایزها
            for color in product.productcolor_set.all():
                color.pk = None
                color.product = product
                color.save()
                
                for size in color.productsize_set.all():
                    size.pk = None
                    size.color = color
                    size.save()
            
        self.message_user(request, f'{queryset.count()} محصول با موفقیت کپی شد.')
    duplicate_product.short_description = 'کپی کردن محصولات انتخاب شده'
    
    def update_prices(self, request, queryset):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.contrib import messages
        
        selected = queryset.values_list('pk', flat=True)
        return HttpResponseRedirect(
            f"{reverse('admin:update-prices')}?ids={','.join(map(str, selected))}"
        )
    update_prices.short_description = 'به‌روزرسانی قیمت'

# ---------------------- ProductColor Admin ----------------------
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'hex_code_preview', 'created_at']
    list_filter = ['product__category', 'product']
    search_fields = ['name', 'product__name']
    inlines = [ProductSizeInline]
    ordering = ['product', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'name', 'hex_code')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'hex_code_preview']
    
    def hex_code_preview(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 5px;"></div>',
            obj.hex_code or '#000000'
        )
    hex_code_preview.short_description = 'پیش‌نمایش رنگ'
    
    list_per_page = 25

# ---------------------- ProductSize Admin ----------------------
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelArchive):
    list_display = ['product_name', 'color_name', 'size', 'price', 'stock', 'is_available']
    list_filter = ['color__product', 'color__name', 'size']
    search_fields = ['color__product__name', 'color__name', 'size']
    ordering = ['color__product', 'color__name', 'size']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('color', 'size', 'price', 'stock')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['price', 'stock']
    list_per_page = 50
    
    def product_name(self, obj):
        return obj.color.product.name
    product_name.short_description = 'محصول'
    product_name.admin_order_field = 'color__product__name'
    
    def color_name(self, obj):
        return obj.color.name
    color_name.short_description = 'رنگ'
    color_name.admin_order_field = 'color__name'
    
    def is_available(self, obj):
        if obj.stock > 0:
            return '✅'
        return '❌'
    is_available.short_description = 'موجود'

# ---------------------- CartItem Admin ----------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_name', 'color_name', 'size_name', 'quantity', 'unit_price', 'total_price', 'created_at']
    list_filter = ['user', 'product_size__color__product', 'created_at']
    search_fields = ['user__username', 'user__email', 'product_size__color__product__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات محصول', {
            'fields': ('product_size', 'quantity')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def product_name(self, obj):
        return obj.product_size.color.product.name
    product_name.short_description = 'محصول'
    
    def color_name(self, obj):
        return obj.product_size.color.name
    color_name.short_description = 'رنگ'
    
    def size_name(self, obj):
        return obj.product_size.size
    size_name.short_description = 'سایز'
    
    def unit_price(self, obj):
        return f'{obj.product_size.price:,.0f} تومان'
    unit_price.short_description = 'قیمت واحد'
    
    def total_price(self, obj):
        return f'{obj.product_size.price * obj.quantity:,.0f} تومان'
    total_price.short_description = 'قیمت کل'
    
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
    list_display = ['product_name', 'user', 'rating_stars', 'comment_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'product', 'created_at']
    search_fields = ['product__name', 'user__username', 'user__email', 'comment']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات محصول و کاربر', {
            'fields': ('product', 'user')
        }),
        ('نظر و امتیاز', {
            'fields': ('rating', 'comment', 'is_approved')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'محصول'
    product_name.admin_order_field = 'product__name'
    
    def rating_stars(self, obj):
        from django.utils.html import format_html
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold;">{}</span>', stars)
    rating_stars.short_description = 'امتیاز'
    
    def comment_preview(self, obj):
        if len(obj.comment) > 50:
            return obj.comment[:50] + '...'
        return obj.comment
    comment_preview.short_description = 'نظر'
    
    actions = ['approve_reviews', 'unapprove_reviews', 'delete_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} دیدگاه با موفقیت تایید شد.')
    approve_reviews.short_description = '✅ تایید دیدگاه‌های انتخاب شده'
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} دیدگاه با موفقیت رد شد.')
    unapprove_reviews.short_description = '❌ رد دیدگاه‌های انتخاب شده'
    
    def delete_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} دیدگاه با موفقیت حذف شد.')
    delete_reviews.short_description = '🗑️ حذف دیدگاه‌های انتخاب شده'

# ---------------------- Favorite Admin ----------------------
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_name', 'created_at']
    list_filter = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'user__email', 'product__name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات', {
            'fields': ('user', 'product')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'محصول'
    
    actions = ['remove_from_favorites']
    
    def remove_from_favorites(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} محصول از علاقه‌مندی‌ها حذف شد.')
    remove_from_favorites.short_description = '🗑️ حذف از علاقه‌مندی‌ها'