from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import (
    Category, Product, ProductColor, ProductSize, ProductImage,
    CartItem, ProductReview, Favorite, Coupon, EmailVerificationCode
)
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect

# ---------------------- Category Admin ----------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description_short', 'product_count', 'created_at']
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
    list_per_page = 25
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'توضیحات'
    
    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:api_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} محصول</a>', url, count)
    product_count.short_description = 'تعداد محصولات'

# ---------------------- Inline ها ----------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    ordering = ['order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'پیش‌نمایش'

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price', 'stock', 'sku', 'is_available']
    readonly_fields = ['sku', 'is_available']
    ordering = ['size']
    
    def is_available(self, obj):
        if obj.stock > 0:
            return format_html('<span style="color: green;">✅ موجود</span>')
        return format_html('<span style="color: red;">❌ ناموجود</span>')
    is_available.short_description = 'وضعیت'

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code', 'color_preview', 'order']
    readonly_fields = ['color_preview']
    show_change_link = True
    ordering = ['order']
    
    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 5px; border: 1px solid #ddd;"></div>',
                obj.hex_code
            )
        return '-'
    color_preview.short_description = 'پیش‌نمایش'

# ---------------------- Product Admin ----------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'main_image_preview', 'price', 'min_price', 
                    'stock_status', 'average_rating', 'reviews_count', 'is_active', 
                    'is_featured', 'created_at']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'meta_keywords']
    inlines = [ProductColorInline, ProductImageInline]
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('category', 'name', 'slug', 'description', 'price')
        }),
        ('تصاویر', {
            'fields': ('main_image', 'main_image_preview'),
            'classes': ('wide',)
        }),
        ('وضعیت', {
            'fields': ('is_active', 'is_featured', 'view_count', 'sold_count')
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
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'reviews_count', 
                      'main_image_preview', 'view_count', 'sold_count']
    list_per_page = 25
    date_hierarchy = 'created_at'
    list_editable = ['is_active', 'is_featured']
    
    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />', 
                             obj.main_image.url)
        return '-'
    main_image_preview.short_description = 'تصویر اصلی'
    
    def min_price(self, obj):
        return f'{obj.min_price:,.0f} تومان'
    min_price.short_description = 'کمترین قیمت'
    min_price.admin_order_field = 'price'
    
    def stock_status(self, obj):
        total_stock = obj.total_stock
        if total_stock > 10:
            return format_html('<span style="color: green;">✅ موجود ({})</span>', total_stock)
        elif total_stock > 0:
            return format_html('<span style="color: orange;">⚠️ محدود ({})</span>', total_stock)
        return format_html('<span style="color: red;">❌ ناموجود</span>')
    stock_status.short_description = 'وضعیت موجودی'
    
    def average_rating(self, obj):
        rating = obj.average_rating
        if rating > 0:
            stars = '★' * int(rating) + '☆' * (5 - int(rating))
            return format_html('<span style="color: gold;">{}</span> {:.1f}', stars, rating)
        return 'بدون امتیاز'
    average_rating.short_description = 'امتیاز'
    
    def reviews_count(self, obj):
        count = obj.reviews_count
        url = reverse('admin:api_productreview_changelist') + f'?product__id__exact={obj.id}'
        return format_html('<a href="{}">{} دیدگاه</a>', url, count)
    reviews_count.short_description = 'دیدگاه‌ها'
    
    actions = ['duplicate_product', 'toggle_active', 'toggle_featured']
    
    def duplicate_product(self, request, queryset):
        for product in queryset:
            product.pk = None
            product.name = f'{product.name} (کپی)'
            product.slug = f'{product.slug}-copy'
            product.save()
            
            for color in product.colors.all():
                color.pk = None
                color.product = product
                color.save()
                
                for size in color.sizes.all():
                    size.pk = None
                    size.color = color
                    size.save()
            
        self.message_user(request, f'{queryset.count()} محصول با موفقیت کپی شد.')
    duplicate_product.short_description = '📋 کپی کردن محصولات انتخاب شده'
    
    def toggle_active(self, request, queryset):
        for product in queryset:
            product.is_active = not product.is_active
            product.save()
        self.message_user(request, f'وضعیت فعال/غیرفعال {queryset.count()} محصول تغییر کرد.')
    toggle_active.short_description = '🔄 تغییر وضعیت فعال/غیرفعال'
    
    def toggle_featured(self, request, queryset):
        for product in queryset:
            product.is_featured = not product.is_featured
            product.save()
        self.message_user(request, f'وضعیت ویژه {queryset.count()} محصول تغییر کرد.')
    toggle_featured.short_description = '⭐ تغییر وضعیت ویژه'

# ---------------------- ProductColor Admin ----------------------
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'color_preview', 'sizes_count', 'total_stock', 'order']
    list_filter = ['product__category', 'product']
    search_fields = ['name', 'product__name']
    inlines = [ProductSizeInline]
    ordering = ['product', 'order', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'name', 'hex_code', 'color_preview', 'order')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'color_preview']
    list_editable = ['order']
    list_per_page = 25
    
    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 5px; border: 1px solid #ddd;"></div>',
                obj.hex_code
            )
        return '-'
    color_preview.short_description = 'پیش‌نمایش'
    
    def sizes_count(self, obj):
        return obj.sizes.count()
    sizes_count.short_description = 'تعداد سایزها'
    
    def total_stock(self, obj):
        total = sum(size.stock for size in obj.sizes.all())
        return total
    total_stock.short_description = 'مجموع موجودی'

# ---------------------- ProductSize Admin ----------------------
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'color_name', 'size', 'price', 'price_formatted', 
                    'stock', 'sku', 'is_available', 'updated_at']
    list_filter = ['color__product', 'color__name', 'size', 'color__product__category']
    search_fields = ['color__product__name', 'color__name', 'size', 'sku']
    ordering = ['color__product', 'color__name', 'size']
    list_editable = ['price', 'stock']
    list_per_page = 50
    list_select_related = ['color', 'color__product']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('color', 'size', 'price', 'stock', 'sku')
        }),
        ('وضعیت', {
            'fields': ('is_available',),
            'classes': ('wide',)
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'sku', 'is_available']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'color', 
            'color__product', 
            'color__product__category'
        )
    
    def product_name(self, obj):
        """نمایش نام محصول با لینک به صفحه ویرایش"""
        url = reverse('admin:api_product_change', args=[obj.color.product.id])
        return format_html('<a href="{}" style="font-weight: 500;">{}</a>', 
                         url, obj.color.product.name)
    product_name.short_description = 'محصول'
    product_name.admin_order_field = 'color__product__name'
    product_name.allow_tags = True
    
    def color_name(self, obj):
        """نمایش نام رنگ با لینک به صفحه ویرایش"""
        url = reverse('admin:api_productcolor_change', args=[obj.color.id])
        # نمایش پیش‌نمایش رنگ کنار نام
        color_preview = ''
        if obj.color.hex_code:
            color_preview = format_html(
                '<span style="display: inline-block; width: 12px; height: 12px; '
                'background-color: {}; border-radius: 3px; margin-left: 5px; '
                'border: 1px solid #ddd; vertical-align: middle;"></span> ',
                obj.color.hex_code
            )
        return format_html('{}<a href="{}" style="vertical-align: middle;">{}</a>', 
                         color_preview, url, obj.color.name)
    color_name.short_description = 'رنگ'
    color_name.admin_order_field = 'color__name'
    color_name.allow_tags = True
    
    def price_formatted(self, obj):
        """نمایش قیمت با فرمت تومان"""
        return format_html(
            '<span style="direction: ltr; display: inline-block; font-family: monospace;">{:,.0f}</span> تومان',
            obj.price
        )
    price_formatted.short_description = 'قیمت (تومان)'
    price_formatted.admin_order_field = 'price'
    
    def is_available(self, obj):
        """نمایش وضعیت موجودی با رنگ و آیکون"""
        if obj.stock > 20:
            return format_html(
                '<span style="color: #28a745; font-weight: 500;">'
                '<span style="font-size: 16px;">✅</span> موجود ({})</span>',
                obj.stock
            )
        elif obj.stock > 10:
            return format_html(
                '<span style="color: #17a2b8; font-weight: 500;">'
                '<span style="font-size: 16px;">🟢</span> خوب ({})</span>',
                obj.stock
            )
        elif obj.stock > 5:
            return format_html(
                '<span style="color: #ffc107; font-weight: 500;">'
                '<span style="font-size: 16px;">🟡</span> محدود ({})</span>',
                obj.stock
            )
        elif obj.stock > 0:
            return format_html(
                '<span style="color: #fd7e14; font-weight: 500;">'
                '<span style="font-size: 16px;">🟠</span> کم ({})</span>',
                obj.stock
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: 500;">'
                '<span style="font-size: 16px;">❌</span> ناموجود</span>'
            )
    is_available.short_description = 'وضعیت موجودی'
    is_available.admin_order_field = 'stock'
    
    def get_readonly_fields(self, request, obj=None):
        """مدیریت فیلدهای فقط خواندنی بر اساس وضعیت"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        
        if obj:  # در حال ویرایش
            # sku فقط در ویرایش غیرفعال باشه
            if 'sku' not in readonly_fields:
                readonly_fields.append('sku')
        else:  # در حال ایجاد
            # موقع ایجاد جدید، sku قابل ویرایش باشه
            if 'sku' in readonly_fields:
                readonly_fields.remove('sku')
        
        return readonly_fields
    
    def get_list_display(self, request):
        """شخصی‌سازی list_display بر اساس درخواست"""
        list_display = super().get_list_display(request)
        
        # اضافه کردن ستون‌های شرطی
        if request.user.is_superuser:
            # سوپریوزرها می‌تونن sku رو ببینن
            if 'sku' not in list_display:
                list_display = list(list_display)
                sku_index = list_display.index('stock') + 1
                list_display.insert(sku_index, 'sku')
        
        return list_display
    
    def get_actions(self, request):
        """تعریف اکشن‌های گروهی"""
        actions = super().get_actions(request)
        
        # اضافه کردن اکشن‌های جدید
        actions['increase_stock'] = (
            self.increase_stock,
            'increase_stock',
            '📈 افزایش موجودی'
        )
        actions['decrease_stock'] = (
            self.decrease_stock,
            'decrease_stock',
            '📉 کاهش موجودی'
        )
        actions['apply_discount'] = (
            self.apply_discount,
            'apply_discount',
            '💰 اعمال تخفیف درصدی'
        )
        
        return actions
    
    def increase_stock(self, request, queryset):
        """افزایش موجودی سایزهای انتخاب شده"""
        amount = request.POST.get('amount', 10)
        try:
            amount = int(amount)
            updated = queryset.update(stock=models.F('stock') + amount)
            self.message_user(
                request, 
                f'✅ موجودی {updated} سایز به مقدار {amount} عدد افزایش یافت.',
                level='SUCCESS'
            )
        except (ValueError, TypeError):
            self.message_user(
                request,
                '❌ لطفاً یک عدد معتبر وارد کنید.',
                level='ERROR'
            )
    increase_stock.short_description = '📈 افزایش موجودی'
    
    def decrease_stock(self, request, queryset):
        """کاهش موجودی سایزهای انتخاب شده"""
        amount = request.POST.get('amount', 5)
        try:
            amount = int(amount)
            for item in queryset:
                if item.stock >= amount:
                    item.stock -= amount
                    item.save()
                else:
                    self.message_user(
                        request,
                        f'⚠️ موجودی {item} کمتر از {amount} است.',
                        level='WARNING'
                    )
            self.message_user(
                request,
                f'✅ موجودی {queryset.count()} سایز به مقدار {amount} عدد کاهش یافت.',
                level='SUCCESS'
            )
        except (ValueError, TypeError):
            self.message_user(
                request,
                '❌ لطفاً یک عدد معتبر وارد کنید.',
                level='ERROR'
            )
    decrease_stock.short_description = '📉 کاهش موجودی'
    
    def apply_discount(self, request, queryset):
        """اعمال تخفیف درصدی روی قیمت‌ها"""
        percent = request.POST.get('percent', 10)
        try:
            percent = int(percent)
            if 0 < percent <= 100:
                for item in queryset:
                    item.price = item.price * (100 - percent) / 100
                    item.save()
                self.message_user(
                    request,
                    f'💰 تخفیف {percent}% روی {queryset.count()} سایز اعمال شد.',
                    level='SUCCESS'
                )
            else:
                self.message_user(
                    request,
                    '❌ درصد تخفیف باید بین 1 تا 100 باشد.',
                    level='ERROR'
                )
        except (ValueError, TypeError):
            self.message_user(
                request,
                '❌ لطفاً یک عدد معتبر وارد کنید.',
                level='ERROR'
            )
    apply_discount.short_description = '💰 اعمال تخفیف درصدی'
    
    def changelist_view(self, request, extra_context=None):
        """اضافه کردن فرم برای اکشن‌ها"""
        extra_context = extra_context or {}
        extra_context['title'] = 'مدیریت سایزهای محصولات'
        return super().changelist_view(request, extra_context)
    
    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }
        js = ('admin/js/product_size_actions.js',)
# ---------------------- ProductImage Admin ----------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'alt_text', 'order', 'created_at']
    list_filter = ['product__category', 'product']
    search_fields = ['product__name', 'alt_text']
    ordering = ['product', 'order']
    list_editable = ['order', 'alt_text']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'image', 'image_preview', 'alt_text', 'order')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'image_preview']
    list_per_page = 50
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />', 
                             obj.image.url)
        return '-'
    image_preview.short_description = 'پیش‌نمایش'

# ---------------------- CartItem Admin ----------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_name', 'color_name', 'size_name', 'quantity', 
                    'unit_price_formatted', 'total_price_formatted', 'created_at']
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
    
    def unit_price_formatted(self, obj):
        return f'{obj.product_size.price:,.0f} تومان'
    unit_price_formatted.short_description = 'قیمت واحد'
    
    def total_price_formatted(self, obj):
        return f'{obj.total_price:,.0f} تومان'
    total_price_formatted.short_description = 'قیمت کل'
    
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
    list_display = ['product_name', 'user', 'rating_stars', 'comment_preview', 
                    'helpful_count', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'product', 'created_at']
    search_fields = ['product__name', 'user__username', 'user__email', 'comment']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات محصول و کاربر', {
            'fields': ('product', 'user')
        }),
        ('نظر و امتیاز', {
            'fields': ('rating', 'comment', 'is_approved', 'helpful_count')
        }),
        ('تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'helpful_count']
    list_per_page = 50
    date_hierarchy = 'created_at'
    list_editable = ['is_approved']
    
    def product_name(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_name.short_description = 'محصول'
    product_name.admin_order_field = 'product__name'
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_stars.short_description = 'امتیاز'
    
    def comment_preview(self, obj):
        if obj.comment:
            if len(obj.comment) > 50:
                return obj.comment[:50] + '...'
            return obj.comment
        return '-'
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
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_name.short_description = 'محصول'
    
    actions = ['remove_from_favorites']
    
    def remove_from_favorites(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} محصول از علاقه‌مندی‌ها حذف شد.')
    remove_from_favorites.short_description = '🗑️ حذف از علاقه‌مندی‌ها'

# ---------------------- Coupon Admin ----------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'max_discount_amount_formatted', 
                    'valid_period', 'used_count', 'max_uses', 'is_active', 'is_valid_status']
    list_filter = ['is_active', 'valid_from', 'valid_to']
    search_fields = ['code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات کوپن', {
            'fields': ('code', 'discount_percent', 'max_discount_amount')
        }),
        ('مدت اعتبار', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('محدودیت‌ها', {
            'fields': ('max_uses', 'used_count', 'is_active')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'used_count']
    list_per_page = 25
    list_editable = ['is_active']
    
    def max_discount_amount_formatted(self, obj):
        if obj.max_discount_amount:
            return f'{obj.max_discount_amount:,.0f} تومان'
        return '-'
    max_discount_amount_formatted.short_description = 'حداکثر تخفیف'
    
    def valid_period(self, obj):
        return f'{obj.valid_from.strftime("%Y/%m/%d")} تا {obj.valid_to.strftime("%Y/%m/%d")}'
    valid_period.short_description = 'مدت اعتبار'
    
    def is_valid_status(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✅ معتبر</span>')
        return format_html('<span style="color: red;">❌ نامعتبر</span>')
    is_valid_status.short_description = 'وضعیت اعتبار'
    
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} کوپن فعال شد.')
    activate_coupons.short_description = '✅ فعال کردن کوپن‌های انتخاب شده'
    
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} کوپن غیرفعال شد.')
    deactivate_coupons.short_description = '❌ غیرفعال کردن کوپن‌های انتخاب شده'

# ---------------------- Email Verification Code Admin ----------------------
@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'is_used', 'is_expired_status', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('اطلاعات', {
            'fields': ('email', 'code', 'is_used')
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    list_editable = ['is_used']
    
    def is_expired_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">❌ منقضی شده</span>')
        return format_html('<span style="color: green;">✅ معتبر</span>')
    is_expired_status.short_description = 'وضعیت انقضا'
    
    actions = ['mark_as_used', 'mark_as_unused']
    
    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'{updated} کد به عنوان استفاده شده علامت زده شد.')
    mark_as_used.short_description = '✅ علامت زدن به عنوان استفاده شده'
    
    def mark_as_unused(self, request, queryset):
        updated = queryset.update(is_used=False)
        self.message_user(request, f'{updated} کد به عنوان استفاده نشده علامت زده شد.')
    mark_as_unused.short_description = '🔄 علامت زدن به عنوان استفاده نشده'