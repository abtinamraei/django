from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
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
        ('📁 اطلاعات اصلی', {
            'fields': ('name', 'slug', 'description')
        }),
        ('📅 تاریخ', {
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
    description_short.short_description = '📝 توضیحات'
    
    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:api_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}" style="background: #28a745; color: white; padding: 3px 10px; border-radius: 15px; text-decoration: none;">{} محصول</a>', url, count)
    product_count.short_description = '📦 تعداد محصولات'


# ---------------------- ProductSize Inline (تودرتو) ----------------------
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price', 'stock', 'sku', 'is_available_display', 'created_at_short']
    readonly_fields = ['sku', 'is_available_display', 'created_at_short']
    ordering = ['size']
    classes = ['collapse']
    verbose_name = 'سایز'
    verbose_name_plural = '📏 سایزهای موجود'
    
    def is_available_display(self, obj):
        if obj.stock > 20:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ موجود ({})</span>', obj.stock)
        elif obj.stock > 10:
            return format_html('<span style="color: #17a2b8; font-weight: bold;">🟢 خوب ({})</span>', obj.stock)
        elif obj.stock > 5:
            return format_html('<span style="color: #ffc107; font-weight: bold;">🟡 محدود ({})</span>', obj.stock)
        elif obj.stock > 0:
            return format_html('<span style="color: #fd7e14; font-weight: bold;">🟠 کم ({})</span>', obj.stock)
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">❌ ناموجود</span>')
    is_available_display.short_description = 'وضعیت'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_short.short_description = 'تاریخ'


# ---------------------- ProductColor Inline (تودرتو) ----------------------
class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code', 'color_preview', 'order', 'sizes_count', 'total_stock_display']
    readonly_fields = ['color_preview', 'sizes_count', 'total_stock_display']
    show_change_link = True
    ordering = ['order']
    classes = ['collapse']
    verbose_name = 'رنگ'
    verbose_name_plural = '🎨 رنگ‌های محصول'
    inlines = [ProductSizeInline]  # ✅ سایزها داخل رنگها
    
    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px #ddd;"></div>',
                obj.hex_code
            )
        return format_html('<span style="color: #999;">ندارد</span>')
    color_preview.short_description = '🎯 پیش‌نمایش'
    
    def sizes_count(self, obj):
        count = obj.sizes.count()
        if count > 0:
            return format_html('<span style="background: #6c757d; color: white; padding: 2px 8px; border-radius: 12px;">{} سایز</span>', count)
        return format_html('<span style="color: #999;">بدون سایز</span>')
    sizes_count.short_description = '📊 تعداد سایزها'
    
    def total_stock_display(self, obj):
        total = sum(size.stock for size in obj.sizes.all())
        if total > 50:
            return format_html('<span style="color: #28a745; font-weight: bold;">{} عدد</span>', total)
        elif total > 20:
            return format_html('<span style="color: #17a2b8; font-weight: bold;">{} عدد</span>', total)
        elif total > 0:
            return format_html('<span style="color: #ffc107; font-weight: bold;">{} عدد</span>', total)
        return format_html('<span style="color: #dc3545; font-weight: bold;">ناموجود</span>')
    total_stock_display.short_description = '📦 مجموع موجودی'


# ---------------------- ProductImage Inline ----------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    ordering = ['order']
    classes = ['collapse']
    verbose_name = 'تصویر'
    verbose_name_plural = '🖼️ گالری تصاویر'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = '👁️ پیش‌نمایش'


# ---------------------- Product Admin (اصلی) ----------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'main_image_preview', 'price_range', 
                    'stock_status_full', 'rating_display', 'status_badges', 'created_at_jalali']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'meta_keywords']
    inlines = [ProductColorInline, ProductImageInline]  # ✅ رنگ‌ها با سایزهای تودرتو
    ordering = ['-created_at']
    save_on_top = True
    list_per_page = 25
    date_hierarchy = 'created_at'
    list_editable = ['is_active', 'is_featured']
    
    fieldsets = (
        ('📌 اطلاعات اصلی', {
            'fields': ('category', 'name', 'slug', 'description', 'price'),
            'classes': ('wide',)
        }),
        ('🖼️ تصویر شاخص', {
            'fields': ('main_image', 'main_image_preview'),
            'classes': ('wide',)
        }),
        ('⚙️ وضعیت و تنظیمات', {
            'fields': ('is_active', 'is_featured', 'view_count', 'sold_count'),
            'classes': ('wide',)
        }),
        ('🔍 تنظیمات سئو', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    prepopulated_fields = {'slug': ['name']}
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'reviews_count', 
                      'main_image_preview', 'view_count', 'sold_count', 'price_range', 
                      'stock_status_full', 'rating_display', 'status_badges']
    
    # ============= متدهای نمایشی =============
    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />',
                obj.main_image.url
            )
        return format_html('<span style="color: #999;">❌ ندارد</span>')
    main_image_preview.short_description = '🖼️ تصویر'
    
    def price_range(self, obj):
        min_p = obj.min_price
        if min_p != obj.price:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{:,.0f}</span> - <span style="color: #6c757d;">{:,.0f}</span> تومان',
                min_p, obj.price
            )
        return format_html('<span style="color: #28a745; font-weight: bold;">{:,.0f}</span> تومان', obj.price)
    price_range.short_description = '💰 قیمت'
    
    def stock_status_full(self, obj):
        total = obj.total_stock
        colors_count = obj.colors.count()
        sizes_count = ProductSize.objects.filter(color__product=obj).count()
        
        if total > 100:
            status = '🟢 فوق‌العاده'
            color = '#28a745'
        elif total > 50:
            status = '🟢 عالی'
            color = '#28a745'
        elif total > 20:
            status = '🔵 خوب'
            color = '#17a2b8'
        elif total > 10:
            status = '🟡 متوسط'
            color = '#ffc107'
        elif total > 0:
            status = '🟠 کم'
            color = '#fd7e14'
        else:
            status = '🔴 ناموجود'
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span><br>'
            '<small style="color: #6c757d;">{} رنگ - {} سایز</small>',
            color, status, colors_count, sizes_count
        )
    stock_status_full.short_description = '📊 وضعیت موجودی'
    
    def rating_display(self, obj):
        rating = obj.average_rating
        count = obj.reviews_count
        
        if rating > 0:
            stars = '★' * int(rating) + '☆' * (5 - int(rating))
            return format_html(
                '<span style="color: #ffc107; font-size: 16px;">{}</span> '
                '<span style="color: #6c757d;">({:.1f} - {} نظر)</span>',
                stars, rating, count
            )
        return format_html('<span style="color: #999;">بدون امتیاز</span>')
    rating_display.short_description = '⭐ امتیاز'
    
    def status_badges(self, obj):
        badges = []
        if obj.is_featured:
            badges.append('<span style="background: #9c27b0; color: white; padding: 3px 10px; border-radius: 15px; font-size: 11px; margin: 2px;">✨ ویژه</span>')
        if not obj.is_active:
            badges.append('<span style="background: #dc3545; color: white; padding: 3px 10px; border-radius: 15px; font-size: 11px; margin: 2px;">⚫ غیرفعال</span>')
        if obj.view_count > 1000:
            badges.append('<span style="background: #fd7e14; color: white; padding: 3px 10px; border-radius: 15px; font-size: 11px; margin: 2px;">🔥 پرفروش</span>')
        
        return format_html(''.join(badges)) if badges else '-'
    status_badges.short_description = '🏷️ برچسب‌ها'
    
    def created_at_jalali(self, obj):
        return obj.created_at.strftime('%Y/%m/%d - %H:%M')
    created_at_jalali.short_description = '📅 تاریخ ثبت'
    
    # ============= اکشن‌های گروهی =============
    actions = ['duplicate_product', 'toggle_active', 'toggle_featured', 'bulk_discount']
    
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
            
        self.message_user(request, f'✅ {queryset.count()} محصول با موفقیت کپی شد.')
    duplicate_product.short_description = '📋 کپی کردن محصولات انتخاب شده'
    
    def toggle_active(self, request, queryset):
        count = queryset.count()
        for product in queryset:
            product.is_active = not product.is_active
            product.save()
        self.message_user(request, f'🔄 وضعیت {count} محصول تغییر کرد.')
    toggle_active.short_description = '🔄 تغییر وضعیت فعال/غیرفعال'
    
    def toggle_featured(self, request, queryset):
        count = queryset.count()
        for product in queryset:
            product.is_featured = not product.is_featured
            product.save()
        self.message_user(request, f'✨ وضعیت ویژه {count} محصول تغییر کرد.')
    toggle_featured.short_description = '⭐ تغییر وضعیت ویژه'
    
    def bulk_discount(self, request, queryset):
        from django.contrib import messages
        percent = request.POST.get('percent', 10)
        try:
            percent = int(percent)
            if 0 < percent <= 100:
                for product in queryset:
                    product.price = product.price * (100 - percent) / 100
                    product.save()
                self.message_user(request, f'💰 تخفیف {percent}% روی {queryset.count()} محصول اعمال شد.')
            else:
                self.message_user(request, '❌ درصد تخفیف باید بین 1 تا 100 باشد.', level='ERROR')
        except:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', level='ERROR')
    bulk_discount.short_description = '💰 اعمال تخفیف درصدی'


# ---------------------- ProductColor Admin ----------------------
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_link', 'color_preview_large', 'sizes_count', 
                   'total_stock_detailed', 'order', 'updated_at_short']
    list_filter = ['product__category', 'product']
    search_fields = ['name', 'product__name']
    inlines = [ProductSizeInline]
    ordering = ['product', 'order', 'name']
    list_editable = ['order']
    list_per_page = 25
    
    fieldsets = (
        ('🎨 اطلاعات رنگ', {
            'fields': ('product', 'name', 'hex_code', 'color_preview_large', 'order')
        }),
        ('📊 آمار', {
            'fields': ('sizes_count', 'total_stock_detailed'),
            'classes': ('wide',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'color_preview_large', 'sizes_count', 'total_stock_detailed']
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}" style="font-weight: bold;">{}</a>', url, obj.product.name)
    product_link.short_description = '📦 محصول'
    
    def color_preview_large(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<div style="width: 40px; height: 40px; background-color: {}; border-radius: 8px; border: 2px solid #fff; box-shadow: 0 0 0 1px #ddd;"></div>'
                '<span style="margin-right: 10px; font-family: monospace;">{}</span>'
                '</div>',
                obj.hex_code, obj.hex_code
            )
        return '-'
    color_preview_large.short_description = '🎯 پیش‌نمایش رنگ'
    
    def sizes_count(self, obj):
        count = obj.sizes.count()
        if count > 0:
            return format_html('<span style="background: #6c757d; color: white; padding: 3px 12px; border-radius: 20px;">{} سایز</span>', count)
        return '-'
    sizes_count.short_description = '📏 تعداد سایزها'
    
    def total_stock_detailed(self, obj):
        sizes = obj.sizes.all()
        if sizes:
            total = sum(s.stock for s in sizes)
            details = ', '.join([f'{s.size}: {s.stock}' for s in sizes[:3]])
            if sizes.count() > 3:
                details += ' و ...'
            return format_html(
                '<span style="font-weight: bold;">{} عدد</span><br>'
                '<small style="color: #6c757d;">{}</small>',
                total, details
            )
        return '-'
    total_stock_detailed.short_description = '📦 جزئیات موجودی'
    
    def updated_at_short(self, obj):
        return obj.updated_at.strftime('%Y/%m/%d')
    updated_at_short.short_description = '📅 آخرین بروزرسانی'


# ---------------------- ProductSize Admin ----------------------
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['product_name_link', 'color_name_link', 'size', 'price_formatted', 
                    'stock_progress', 'sku_short', 'status_with_badge', 'updated_at_short']
    list_filter = ['color__product', 'color__name', 'size', 'color__product__category']
    search_fields = ['color__product__name', 'color__name', 'size', 'sku']
    ordering = ['color__product', 'color__name', 'size']
    list_editable = ['price', 'stock']
    list_per_page = 50
    save_on_top = True
    
    fieldsets = (
        ('📏 اطلاعات سایز', {
            'fields': ('color', 'size', 'price', 'stock', 'sku'),
            'classes': ('wide',)
        }),
        ('📊 وضعیت', {
            'fields': ('stock_progress', 'status_with_badge'),
            'classes': ('wide',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'sku', 'stock_progress', 'status_with_badge']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'color', 'color__product', 'color__product__category'
        )
    
    # ============= متدهای نمایشی =============
    def product_name_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.color.product.id])
        return format_html('<a href="{}" style="font-weight: 600;">{}</a>', url, obj.color.product.name)
    product_name_link.short_description = '📦 محصول'
    
    def color_name_link(self, obj):
        url = reverse('admin:api_productcolor_change', args=[obj.color.id])
        color_preview = ''
        if obj.color.hex_code:
            color_preview = format_html(
                '<span style="display: inline-block; width: 12px; height: 12px; '
                'background-color: {}; border-radius: 4px; margin-left: 5px; '
                'border: 1px solid #ddd; vertical-align: middle;"></span> ',
                obj.color.hex_code
            )
        return format_html('{}<a href="{}" style="vertical-align: middle;">{}</a>', 
                         color_preview, url, obj.color.name)
    color_name_link.short_description = '🎨 رنگ'
    
    def price_formatted(self, obj):
        return format_html(
            '<span style="direction: ltr; display: inline-block; font-family: monospace; font-weight: bold; color: #28a745;">{:,.0f}</span> تومان',
            obj.price
        )
    price_formatted.short_description = '💰 قیمت'
    
    def sku_short(self, obj):
        if obj.sku:
            return format_html('<span style="font-family: monospace; color: #6c757d;">{}</span>', obj.sku)
        return '-'
    sku_short.short_description = '🏷️ SKU'
    
    def stock_progress(self, obj):
        percentage = min(100, (obj.stock / 100) * 100)
        if obj.stock > 50:
            color = '#28a745'
        elif obj.stock > 20:
            color = '#17a2b8'
        elif obj.stock > 10:
            color = '#ffc107'
        elif obj.stock > 0:
            color = '#fd7e14'
        else:
            color = '#dc3545'
        
        return format_html(
            '<div style="width: 100px; background: #e9ecef; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; height: 8px;"></div>'
            '</div>'
            '<span style="font-size: 12px; color: {};">{} عدد</span>',
            percentage, color, color, obj.stock
        )
    stock_progress.short_description = '📊 موجودی'
    
    def status_with_badge(self, obj):
        if obj.stock > 20:
            return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;">✅ موجود</span>')
        elif obj.stock > 10:
            return format_html('<span style="background: #17a2b8; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;">🟢 خوب</span>')
        elif obj.stock > 5:
            return format_html('<span style="background: #ffc107; color: black; padding: 4px 12px; border-radius: 20px; font-size: 12px;">🟡 محدود</span>')
        elif obj.stock > 0:
            return format_html('<span style="background: #fd7e14; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;">🟠 کم</span>')
        else:
            return format_html('<span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;">❌ ناموجود</span>')
    status_with_badge.short_description = '⚡ وضعیت'
    
    def updated_at_short(self, obj):
        return obj.updated_at.strftime('%Y/%m/%d')
    updated_at_short.short_description = '📅 بروزرسانی'
    
    # ============= اکشن‌های گروهی =============
    actions = ['increase_stock', 'decrease_stock', 'apply_discount', 'set_sku']
    
    def increase_stock(self, request, queryset):
        amount = request.POST.get('amount', 10)
        try:
            amount = int(amount)
            updated = queryset.update(stock=models.F('stock') + amount)
            self.message_user(request, f'✅ موجودی {updated} سایز به مقدار {amount} عدد افزایش یافت.')
        except:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', level='ERROR')
    increase_stock.short_description = '📈 افزایش موجودی'
    
    def decrease_stock(self, request, queryset):
        amount = request.POST.get('amount', 5)
        try:
            amount = int(amount)
            for item in queryset:
                if item.stock >= amount:
                    item.stock -= amount
                    item.save()
            self.message_user(request, f'✅ موجودی {queryset.count()} سایز به مقدار {amount} عدد کاهش یافت.')
        except:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', level='ERROR')
    decrease_stock.short_description = '📉 کاهش موجودی'
    
    def apply_discount(self, request, queryset):
        percent = request.POST.get('percent', 10)
        try:
            percent = int(percent)
            if 0 < percent <= 100:
                for item in queryset:
                    item.price = item.price * (100 - percent) / 100
                    item.save()
                self.message_user(request, f'💰 تخفیف {percent}% روی {queryset.count()} سایز اعمال شد.')
            else:
                self.message_user(request, '❌ درصد تخفیف باید بین 1 تا 100 باشد.', level='ERROR')
        except:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', level='ERROR')
    apply_discount.short_description = '💰 اعمال تخفیف درصدی'
    
    def set_sku(self, request, queryset):
        count = 0
        for item in queryset:
            if not item.sku:
                item.save()  # save متد sku میسازه
                count += 1
        self.message_user(request, f'✅ SKU برای {count} سایز ایجاد شد.')
    set_sku.short_description = '🏷️ ایجاد SKU'


# ---------------------- ProductImage Admin ----------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product_link', 'image_thumbnail', 'alt_text', 'order', 'created_at_short']
    list_filter = ['product__category', 'product']
    search_fields = ['product__name', 'alt_text']
    ordering = ['product', 'order']
    list_editable = ['order', 'alt_text']
    list_per_page = 50
    
    fieldsets = (
        ('🖼️ اطلاعات تصویر', {
            'fields': ('product', 'image', 'image_preview_large', 'alt_text', 'order')
        }),
        ('📅 تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'image_preview_large']
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = '📦 محصول'
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />',
                obj.image.url
            )
        return '-'
    image_thumbnail.short_description = '🖼️ تصویر'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; object-fit: contain; border-radius: 8px; border: 1px solid #dee2e6;" />',
                obj.image.url
            )
        return '-'
    image_preview_large.short_description = '👁️ پیش‌نمایش بزرگ'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_short.short_description = '📅 تاریخ'


# ---------------------- CartItem Admin ----------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'product_info', 'quantity_badge', 'unit_price', 'total_price', 'created_at_short']
    list_filter = ['user', 'created_at']
    search_fields = ['user__username', 'user__email', 'product_size__color__product__name']
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('👤 اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('🛒 اطلاعات محصول', {
            'fields': ('product_size', 'quantity', 'total_price_display'),
            'classes': ('wide',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'total_price_display']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = '👤 کاربر'
    
    def product_info(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{}</span><br>'
            '<small style="color: #6c757d;">{} - {}</small>',
            obj.product_size.color.product.name,
            obj.product_size.color.name,
            obj.product_size.size
        )
    product_info.short_description = '📦 محصول'
    
    def quantity_badge(self, obj):
        if obj.quantity > 5:
            color = '#28a745'
        elif obj.quantity > 2:
            color = '#17a2b8'
        else:
            color = '#6c757d'
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;">{} عدد</span>',
            color, obj.quantity
        )
    quantity_badge.short_description = '🔢 تعداد'
    
    def unit_price(self, obj):
        return format_html('<span style="font-family: monospace;">{:,.0f}</span> تومان', obj.product_size.price)
    unit_price.short_description = '💰 قیمت واحد'
    
    def total_price(self, obj):
        return format_html(
            '<span style="font-family: monospace; font-weight: bold; color: #28a745;">{:,.0f}</span> تومان',
            obj.total_price
        )
    total_price.short_description = '💵 قیمت کل'
    
    def total_price_display(self, obj):
        return format_html(
            '<span style="font-size: 16px; font-weight: bold; color: #28a745;">{:,.0f} تومان</span>',
            obj.total_price
        )
    total_price_display.short_description = '💵 قیمت کل'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_short.short_description = '📅 تاریخ'
    
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
    list_display = ['product_link', 'user_link', 'rating_stars', 'comment_short', 
                    'helpful_badge', 'approval_status', 'created_at_short']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    list_editable = ['is_approved']
    
    fieldsets = (
        ('📝 اطلاعات نظر', {
            'fields': ('product', 'user', 'rating', 'comment')
        }),
        ('⚙️ وضعیت', {
            'fields': ('is_approved', 'helpful_count', 'rating_stars_large'),
            'classes': ('wide',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'helpful_count', 'rating_stars_large']
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name[:30])
    product_link.short_description = '📦 محصول'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = '👤 کاربر'
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #ffc107; font-size: 16px;">{}</span>', stars)
    rating_stars.short_description = '⭐ امتیاز'
    
    def rating_stars_large(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: #ffc107; font-size: 24px;">{}</span><br>'
            '<span style="color: #6c757d;">{} از 5</span>',
            stars, obj.rating
        )
    rating_stars_large.short_description = '⭐ امتیاز'
    
    def comment_short(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    comment_short.short_description = '💬 نظر'
    
    def helpful_badge(self, obj):
        if obj.helpful_count > 10:
            return format_html('<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px;">{} مفید</span>', obj.helpful_count)
        elif obj.helpful_count > 5:
            return format_html('<span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 12px;">{} مفید</span>', obj.helpful_count)
        return str(obj.helpful_count)
    helpful_badge.short_description = '👍 مفید'
    
    def approval_status(self, obj):
        if obj.is_approved:
            return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px;">✅ تایید شده</span>')
        return format_html('<span style="background: #ffc107; color: black; padding: 4px 12px; border-radius: 20px;">⏳ در انتظار</span>')
    approval_status.short_description = '⚡ وضعیت'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_short.short_description = '📅 تاریخ'
    
    actions = ['approve_reviews', 'unapprove_reviews', 'delete_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'✅ {updated} دیدگاه تایید شد.')
    approve_reviews.short_description = '✅ تایید دیدگاه‌ها'
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'❌ {updated} دیدگاه رد شد.')
    unapprove_reviews.short_description = '❌ رد دیدگاه‌ها'
    
    def delete_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'🗑️ {count} دیدگاه حذف شد.')
    delete_reviews.short_description = '🗑️ حذف دیدگاه‌ها'


# ---------------------- Favorite Admin ----------------------
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'product_link', 'favorite_since', 'created_at_short']
    list_filter = ['user', 'created_at']
    search_fields = ['user__username', 'product__name']
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('❤️ اطلاعات علاقه‌مندی', {
            'fields': ('user', 'product')
        }),
        ('📅 تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = '👤 کاربر'
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = '📦 محصول'
    
    def favorite_since(self, obj):
        days = (timezone.now() - obj.created_at).days
        if days == 0:
            return 'امروز'
        elif days == 1:
            return 'دیروز'
        else:
            return f'{days} روز پیش'
    favorite_since.short_description = '⏳ زمان افزودن'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_short.short_description = '📅 تاریخ'
    
    actions = ['remove_from_favorites']
    
    def remove_from_favorites(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'🗑️ {count} محصول از علاقه‌مندی‌ها حذف شد.')
    remove_from_favorites.short_description = '🗑️ حذف از علاقه‌مندی‌ها'


# ---------------------- Coupon Admin ----------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_display', 'valid_period', 'usage_stats', 
                   'status_badge', 'created_at_short']
    list_filter = ['is_active', 'valid_from', 'valid_to']
    search_fields = ['code']
    ordering = ['-created_at']
    list_per_page = 25
    list_editable = ['is_active']
    
    fieldsets = (
        ('🏷️ اطلاعات کوپن', {
            'fields': ('code', 'discount_percent', 'max_discount_amount')
        }),
        ('📅 مدت اعتبار', {
            'fields': ('valid_from', 'valid_to', 'is_valid_display'),
            'classes': ('wide',)
        }),
        ('📊 محدودیت‌ها', {
            'fields': ('max_uses', 'used_count', 'is_active'),
            'classes': ('wide',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'used_count', 'is_valid_display']
    
    def discount_display(self, obj):
        if obj.max_discount_amount:
            return f'{obj.discount_percent}% (حداکثر {obj.max_discount_amount:,.0f} تومان)'
        return f'{obj.discount_percent}%'
    discount_display.short_description = '💰 تخفیف'
    
    def valid_period(self, obj):
        return f'{obj.valid_from.strftime("%Y/%m/%d")} تا {obj.valid_to.strftime("%Y/%m/%d")}'
    valid_period.short_description = '📆 مدت اعتبار'
    
    def usage_stats(self, obj):
        percentage = (obj.used_count / obj.max_uses) * 100 if obj.max_uses > 0 else 0
        return format_html(
            '<span style="font-weight: bold;">{}/{}</span><br>'
            '<div style="width: 80px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin-top: 5px;">'
            '<div style="width: {}%; background: {}; height: 4px;"></div>'
            '</div>',
            obj.used_count, obj.max_uses,
            percentage, '#28a745' if percentage < 80 else '#dc3545'
        )
    usage_stats.short_description = '📊 مصرف'
    
    def status_badge(self, obj):
        if obj.is_valid():
            return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px;">✅ فعال</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 20px;">❌ غیرفعال</span>')
    status_badge.short_description = '⚡ وضعیت'
    
    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: #28a745; font-size: 16px;">✅ این کوپن معتبر است</span>')
        return format_html('<span style="color: #dc3545; font-size: 16px;">❌ این کوپن منقضی شده یا غیرفعال است</span>')
    is_valid_display.short_description = '🔍 بررسی اعتبار'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')
    created_at_short.short_description = '📅 تاریخ ایجاد'
    
    actions = ['activate_coupons', 'deactivate_coupons', 'reset_usage']
    
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} کوپن فعال شد.')
    activate_coupons.short_description = '✅ فعال کردن کوپن‌ها'
    
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ {updated} کوپن غیرفعال شد.')
    deactivate_coupons.short_description = '❌ غیرفعال کردن کوپن‌ها'
    
    def reset_usage(self, request, queryset):
        updated = queryset.update(used_count=0)
        self.message_user(request, f'🔄 تعداد مصرف {updated} کوپن ریست شد.')
    reset_usage.short_description = '🔄 ریست تعداد مصرف'


# ---------------------- Email Verification Code Admin ----------------------
@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'usage_status', 'expiry_status', 'created_at_short']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'code']
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    list_editable = ['is_used']
    
    fieldsets = (
        ('📧 اطلاعات ایمیل', {
            'fields': ('email', 'code', 'is_used')
        }),
        ('🔍 وضعیت', {
            'fields': ('expiry_status_display', 'created_at'),
            'classes': ('wide',)
        }),
    )
    readonly_fields = ['created_at', 'expiry_status_display']
    
    def usage_status(self, obj):
        if obj.is_used:
            return format_html('<span style="background: #6c757d; color: white; padding: 4px 12px; border-radius: 20px;">✅ استفاده شده</span>')
        return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px;">🆕 استفاده نشده</span>')
    usage_status.short_description = '📌 وضعیت مصرف'
    
    def expiry_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: #dc3545; font-weight: bold;">❌ منقضی شده</span>')
        remaining = (obj.created_at + timedelta(minutes=10) - timezone.now()).seconds // 60
        return format_html('<span style="color: #28a745; font-weight: bold;">✅ معتبر ({} دقیقه)</span>', remaining)
    expiry_status.short_description = '⏳ انقضا'
    
    def expiry_status_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: #dc3545; font-size: 16px;">❌ این کد در {} منقضی شده است</span>', 
                             (obj.created_at + timedelta(minutes=10)).strftime('%Y/%m/%d %H:%M'))
        remaining = (obj.created_at + timedelta(minutes=10) - timezone.now()).seconds // 60
        return format_html('<span style="color: #28a745; font-size: 16px;">✅ این کد تا {} معتبر است ({} دقیقه باقی)</span>',
                         (obj.created_at + timedelta(minutes=10)).strftime('%Y/%m/%d %H:%M'), remaining)
    expiry_status_display.short_description = '🔍 وضعیت انقضا'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d %H:%M')
    created_at_short.short_description = '📅 تاریخ ایجاد'
    
    actions = ['mark_as_used', 'mark_as_unused', 'delete_expired']
    
    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'✅ {updated} کد به عنوان استفاده شده علامت زده شد.')
    mark_as_used.short_description = '✅ علامت به عنوان استفاده شده'
    
    def mark_as_unused(self, request, queryset):
        updated = queryset.update(is_used=False)
        self.message_user(request, f'🔄 {updated} کد به عنوان استفاده نشده علامت زده شد.')
    mark_as_unused.short_description = '🔄 علامت به عنوان استفاده نشده'
    
    def delete_expired(self, request, queryset):
        expired = [obj for obj in queryset if obj.is_expired()]
        count = len(expired)
        for obj in expired:
            obj.delete()
        self.message_user(request, f'🗑️ {count} کد منقضی شده حذف شد.')
    delete_expired.short_description = '🗑️ حذف کدهای منقضی شده'