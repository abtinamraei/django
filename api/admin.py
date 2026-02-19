from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from typing import Optional, Dict, Any
from .models import (
    Category, Product, ProductColor, ProductSize, ProductImage,
    CartItem, ProductReview, Favorite, Coupon, EmailVerificationCode
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_price(price: float) -> str:
    """فرمت‌سازی قیمت با جداکننده هزارگان"""
    return f"{price:,.0f}"


def get_status_badge(text: str, color: str, icon: str = "") -> str:
    """ایجاد نشان وضعیت یکسان در سراسر ادمین"""
    colors = {
        'success': '#28a745',
        'info': '#17a2b8',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'secondary': '#6c757d',
        'primary': '#007bff',
        'dark': '#343a40',
        'orange': '#fd7e14',
        'purple': '#9c27b0'
    }
    bg_color = colors.get(color, color)
    return f'<span style="background: {bg_color}; color: white; padding: 3px 10px; border-radius: 15px; font-size: 11px; font-weight: 500;">{icon} {text}</span>'


def get_stars_html(rating: float, size: int = 16) -> str:
    """ایجاد نمایش ستاره برای امتیاز"""
    if not rating or rating <= 0:
        return '<span style="color: #999;">⭐ بدون امتیاز</span>'
    
    full_stars = '★' * int(rating)
    empty_stars = '☆' * (5 - int(rating))
    return f'<span style="color: #ffc107; font-size: {size}px;">{full_stars}{empty_stars}</span>'


# ============================================================================
# MIXINS
# ============================================================================

class JalaliDateMixin:
    """میکسین برای نمایش تاریخ به فرمت شمسی"""
    
    def get_jalali_date(self, date, format_str='%Y/%m/%d'):
        if date:
            return date.strftime(format_str)
        return '-'
    
    def get_jalali_datetime(self, date):
        return self.get_jalali_date(date, '%Y/%m/%d - %H:%M')


class StockStatusMixin:
    """میکسین برای وضعیت موجودی"""
    
    def get_stock_status(self, stock: int) -> Dict[str, Any]:
        if stock > 100:
            return {'text': 'فوق‌العاده', 'color': 'success', 'icon': '🟢'}
        elif stock > 50:
            return {'text': 'عالی', 'color': 'success', 'icon': '🟢'}
        elif stock > 20:
            return {'text': 'خوب', 'color': 'info', 'icon': '🔵'}
        elif stock > 10:
            return {'text': 'متوسط', 'color': 'warning', 'icon': '🟡'}
        elif stock > 5:
            return {'text': 'محدود', 'color': 'warning', 'icon': '🟡'}
        elif stock > 0:
            return {'text': 'کم', 'color': 'orange', 'icon': '🟠'}
        else:
            return {'text': 'ناموجود', 'color': 'danger', 'icon': '🔴'}


# ============================================================================
# INLINES
# ============================================================================

class ProductSizeInline(admin.TabularInline):
    """اینلاین برای مدیریت سایزهای محصول"""
    model = ProductSize
    extra = 1
    fields = ['size', 'price', 'stock', 'sku', 'status_display', 'created_at_short']
    readonly_fields = ['sku', 'status_display', 'created_at_short']
    ordering = ['size']
    classes = ['collapse']
    verbose_name = 'سایز'
    verbose_name_plural = '📏 سایزهای موجود'
    
    def status_display(self, obj):
        """نمایش وضعیت موجودی با رنگ مناسب"""
        status_map = {
            range(21, 1000): ('success', '✅ موجود'),
            range(11, 21): ('info', '🟢 خوب'),
            range(6, 11): ('warning', '🟡 محدود'),
            range(1, 6): ('orange', '🟠 کم'),
        }
        
        for stock_range, (color, text) in status_map.items():
            if obj.stock in stock_range:
                return mark_safe(get_status_badge(f"{text} ({obj.stock})", color))
        
        if obj.stock > 100:
            return mark_safe(get_status_badge(f"✅ فوق‌العاده ({obj.stock})", 'success'))
        elif obj.stock <= 0:
            return mark_safe(get_status_badge("❌ ناموجود", 'danger'))
        
        return mark_safe(get_status_badge(f"⚪ {obj.stock} عدد", 'secondary'))
    
    status_display.short_description = 'وضعیت'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y/%m/%d') if obj.created_at else '-'
    created_at_short.short_description = 'تاریخ'


class ProductColorInline(admin.TabularInline):
    """اینلاین برای مدیریت رنگ‌های محصول"""
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code', 'color_preview', 'order', 'sizes_count', 'total_stock_display']
    readonly_fields = ['color_preview', 'sizes_count', 'total_stock_display']
    show_change_link = True
    ordering = ['order']
    classes = ['collapse']
    verbose_name = 'رنگ'
    verbose_name_plural = '🎨 رنگ‌های محصول'
    
    def color_preview(self, obj):
        """پیش‌نمایش رنگ با کد هگز"""
        if obj.hex_code:
            return mark_safe(
                f'<div style="display: flex; align-items: center;">'
                f'<div style="width: 30px; height: 30px; background-color: {obj.hex_code}; '
                f'border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px #ddd;"></div>'
                f'<span style="margin-right: 8px; font-family: monospace;">{obj.hex_code}</span>'
                f'</div>'
            )
        return '-'
    color_preview.short_description = '🎯 پیش‌نمایش'
    
    def sizes_count(self, obj):
        """تعداد سایزهای هر رنگ"""
        count = obj.sizes.count()
        if count:
            return mark_safe(get_status_badge(f"{count} سایز", 'secondary'))
        return '-'
    sizes_count.short_description = '📊 تعداد سایزها'
    
    def total_stock_display(self, obj):
        """مجموع موجودی هر رنگ"""
        total = sum(size.stock for size in obj.sizes.all())
        if total > 50:
            return mark_safe(get_status_badge(f"{total} عدد", 'success'))
        elif total > 20:
            return mark_safe(get_status_badge(f"{total} عدد", 'info'))
        elif total > 0:
            return mark_safe(get_status_badge(f"{total} عدد", 'warning'))
        return mark_safe(get_status_badge("ناموجود", 'danger'))
    total_stock_display.short_description = '📦 مجموع موجودی'


class ProductImageInline(admin.TabularInline):
    """اینلاین برای مدیریت تصاویر محصول"""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order', 'image_preview']
    readonly_fields = ['image_preview']
    ordering = ['order']
    classes = ['collapse']
    verbose_name = 'تصویر'
    verbose_name_plural = '🖼️ گالری تصاویر'
    
    def image_preview(self, obj):
        """پیش‌نمایش تصویر"""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="width: 60px; height: 60px; '
                f'object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />'
            )
        return '-'
    image_preview.short_description = '👁️ پیش‌نمایش'


# ============================================================================
# MODEL ADMINS
# ============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت دسته‌بندی‌ها"""
    
    list_display = ['name', 'slug', 'description_short', 'product_count_badge', 'created_at_jalali']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}
    ordering = ['name']
    list_per_page = 25
    
    fieldsets = (
        ('📁 اطلاعات اصلی', {
            'fields': ('name', 'slug', 'description'),
            'classes': ('wide',)
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def description_short(self, obj):
        """خلاصه توضیحات"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = '📝 توضیحات'
    
    def product_count_badge(self, obj):
        """تعداد محصولات با لینک"""
        count = obj.products.count()
        url = reverse('admin:api_product_changelist') + f'?category__id__exact={obj.id}'
        return mark_safe(
            f'<a href="{url}" style="background: #28a745; color: white; padding: 3px 10px; '
            f'border-radius: 15px; text-decoration: none; display: inline-block;">'
            f'📦 {count} محصول</a>'
        )
    product_count_badge.short_description = 'تعداد محصولات'
    
    def created_at_jalali(self, obj):
        return self.get_jalali_date(obj.created_at)
    created_at_jalali.short_description = '📅 تاریخ ثبت'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin, JalaliDateMixin, StockStatusMixin):
    """مدیریت محصولات"""
    
    list_display = [
        'name', 'category_link', 'main_image_thumbnail', 'price_display',
        'stock_status_aggregated', 'rating_display', 'is_active', 'is_featured',
        'status_badges', 'created_at_jalali'
    ]
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'meta_keywords']
    inlines = [ProductColorInline, ProductImageInline]
    ordering = ['-created_at']
    save_on_top = True
    list_per_page = 25
    date_hierarchy = 'created_at'
    list_editable = ['is_active', 'is_featured']
    
    fieldsets = (
        ('📌 اطلاعات اصلی', {
            'fields': ('category', 'name', 'slug', 'description', 'base_price'),
            'classes': ('wide',)
        }),
        ('🖼️ تصاویر', {
            'fields': ('main_image', 'main_image_preview'),
            'classes': ('wide',)
        }),
        ('⚙️ وضعیت و آمار', {
            'fields': ('is_active', 'is_featured', 'view_count', 'sold_count',
                      'average_rating', 'reviews_count'),
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
    readonly_fields = [
        'created_at', 'updated_at', 'average_rating', 'reviews_count',
        'main_image_preview', 'view_count', 'sold_count', 'price_display',
        'stock_status_aggregated', 'rating_display', 'status_badges'
    ]
    
    # ========================================================================
    # METHOD FIELDS
    # ========================================================================
    
    def category_link(self, obj):
        """لینک به دسته‌بندی"""
        url = reverse('admin:api_category_change', args=[obj.category.id])
        return mark_safe(f'<a href="{url}">{obj.category.name}</a>')
    category_link.short_description = 'دسته‌بندی'
    category_link.admin_order_field = 'category__name'
    
    def main_image_thumbnail(self, obj):
        """تصویر بندانگشتی"""
        if obj.main_image:
            return mark_safe(
                f'<img src="{obj.main_image.url}" style="width: 50px; height: 50px; '
                f'object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />'
            )
        return '-'
    main_image_thumbnail.short_description = '🖼️ تصویر'
    
    def main_image_preview(self, obj):
        """پیش‌نمایش بزرگ تصویر"""
        if obj.main_image:
            return mark_safe(
                f'<img src="{obj.main_image.url}" style="max-width: 200px; max-height: 200px; '
                f'object-fit: contain; border-radius: 8px; border: 1px solid #dee2e6;" />'
            )
        return '-'
    main_image_preview.short_description = '👁️ پیش‌نمایش'
    
    def price_display(self, obj):
        """نمایش قیمت با فرمت مناسب"""
        min_price = obj.min_price
        if min_price != obj.base_price:
            return mark_safe(
                f'<span style="color: #28a745; font-weight: bold;">{format_price(min_price)}</span> - '
                f'<span style="color: #6c757d;">{format_price(obj.base_price)}</span> تومان'
            )
        return mark_safe(
            f'<span style="color: #28a745; font-weight: bold;">{format_price(obj.base_price)}</span> تومان'
        )
    price_display.short_description = '💰 قیمت'
    
    def stock_status_aggregated(self, obj):
        """وضعیت موجودی تجمیعی"""
        total = obj.total_stock
        colors_count = obj.colors.count()
        sizes_count = ProductSize.objects.filter(color__product=obj).count()
        
        status = self.get_stock_status(total)
        badge = get_status_badge(status['text'], status['color'], status['icon'])
        
        return mark_safe(
            f'{badge}<br>'
            f'<small style="color: #6c757d;">{colors_count} رنگ - {sizes_count} سایز</small>'
        )
    stock_status_aggregated.short_description = '📊 وضعیت موجودی'
    
    def rating_display(self, obj):
        """نمایش امتیاز با ستاره"""
        rating = obj.average_rating
        count = obj.reviews_count
        
        if rating and rating > 0:
            stars = get_stars_html(rating)
            return mark_safe(
                f'{stars} '
                f'<span style="color: #6c757d;">({rating:.1f} - {count} نظر)</span>'
            )
        return mark_safe('<span style="color: #999;">⭐ بدون امتیاز</span>')
    rating_display.short_description = '⭐ امتیاز'
    
    def status_badges(self, obj):
        """برچسب‌های وضعیت"""
        badges = []
        
        if obj.is_featured:
            badges.append(get_status_badge('ویژه', 'purple', '✨'))
        if not obj.is_active:
            badges.append(get_status_badge('غیرفعال', 'danger', '⚫'))
        if obj.view_count > 1000:
            badges.append(get_status_badge('پربازدید', 'orange', '👁️'))
        if obj.sold_count > 100:
            badges.append(get_status_badge('پرفروش', 'success', '🔥'))
            
        return mark_safe(' '.join(badges)) if badges else '-'
    status_badges.short_description = '🏷️ برچسب‌ها'
    
    def created_at_jalali(self, obj):
        return self.get_jalali_datetime(obj.created_at)
    created_at_jalali.short_description = '📅 تاریخ ثبت'
    created_at_jalali.admin_order_field = 'created_at'
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    actions = ['duplicate_products', 'toggle_active', 'toggle_featured', 'apply_discount']
    
    def duplicate_products(self, request, queryset):
        """کپی کردن محصولات انتخاب شده"""
        for product in queryset:
            # کپی محصول
            product.pk = None
            product.name = f'{product.name} (کپی)'
            product.slug = f'{product.slug}-copy'
            product.save()
            
            # کپی رنگ‌ها
            for color in product.colors.all():
                color.pk = None
                color.product = product
                color.save()
                
                # کپی سایزها
                for size in color.sizes.all():
                    size.pk = None
                    size.color = color
                    size.save()
        
        self.message_user(
            request,
            f'✅ {queryset.count()} محصول با موفقیت کپی شد.',
            messages.SUCCESS
        )
    duplicate_products.short_description = '📋 کپی کردن محصولات انتخاب شده'
    
    def toggle_active(self, request, queryset):
        """تغییر وضعیت فعال/غیرفعال"""
        count = queryset.count()
        for product in queryset:
            product.is_active = not product.is_active
            product.save()
        self.message_user(request, f'🔄 وضعیت {count} محصول تغییر کرد.', messages.SUCCESS)
    toggle_active.short_description = '🔄 تغییر وضعیت فعال/غیرفعال'
    
    def toggle_featured(self, request, queryset):
        """تغییر وضعیت ویژه"""
        count = queryset.count()
        for product in queryset:
            product.is_featured = not product.is_featured
            product.save()
        self.message_user(request, f'✨ وضعیت ویژه {count} محصول تغییر کرد.', messages.SUCCESS)
    toggle_featured.short_description = '⭐ تغییر وضعیت ویژه'
    
    def apply_discount(self, request, queryset):
        """اعمال تخفیف درصدی"""
        percent = request.POST.get('percent', 10)
        try:
            percent = int(percent)
            if 0 < percent <= 100:
                for product in queryset:
                    product.base_price = product.base_price * (100 - percent) / 100
                    product.save()
                self.message_user(
                    request,
                    f'💰 تخفیف {percent}% روی {queryset.count()} محصول اعمال شد.',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    '❌ درصد تخفیف باید بین 1 تا 100 باشد.',
                    messages.ERROR
                )
        except ValueError:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', messages.ERROR)
    apply_discount.short_description = '💰 اعمال تخفیف درصدی'


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin, JalaliDateMixin, StockStatusMixin):
    """مدیریت رنگ‌های محصول"""
    
    list_display = [
        'name', 'product_link', 'color_preview_large', 'sizes_count',
        'total_stock_detailed', 'order', 'updated_at_short'
    ]
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
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'color_preview_large', 'sizes_count', 'total_stock_detailed']
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return mark_safe(f'<a href="{url}" style="font-weight: bold;">{obj.product.name}</a>')
    product_link.short_description = '📦 محصول'
    product_link.admin_order_field = 'product__name'
    
    def color_preview_large(self, obj):
        if obj.hex_code:
            return mark_safe(
                f'<div style="display: flex; align-items: center;">'
                f'<div style="width: 40px; height: 40px; background-color: {obj.hex_code}; '
                f'border-radius: 8px; border: 2px solid #fff; box-shadow: 0 0 0 1px #ddd;"></div>'
                f'<span style="margin-right: 10px; font-family: monospace;">{obj.hex_code}</span>'
                f'</div>'
            )
        return '-'
    color_preview_large.short_description = '🎯 پیش‌نمایش رنگ'
    
    def sizes_count(self, obj):
        count = obj.sizes.count()
        if count:
            return mark_safe(get_status_badge(f"{count} سایز", 'secondary'))
        return '-'
    sizes_count.short_description = '📏 تعداد سایزها'
    
    def total_stock_detailed(self, obj):
        sizes = obj.sizes.all()
        if sizes:
            total = sum(s.stock for s in sizes)
            details = ', '.join([f'{s.size}: {s.stock}' for s in sizes[:3]])
            if sizes.count() > 3:
                details += ' و ...'
            
            status = self.get_stock_status(total)
            badge = get_status_badge(status['text'], status['color'], status['icon'])
            
            return mark_safe(
                f'{badge}<br>'
                f'<small style="color: #6c757d;">{details}</small>'
            )
        return '-'
    total_stock_detailed.short_description = '📦 جزئیات موجودی'
    
    def updated_at_short(self, obj):
        return self.get_jalali_date(obj.updated_at)
    updated_at_short.short_description = '📅 آخرین بروزرسانی'


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin, JalaliDateMixin, StockStatusMixin):
    """مدیریت سایزهای محصول"""
    
    list_display = [
        'product_link', 'color_link', 'size', 'price_formatted',
        'stock_with_badge', 'sku_short', 'status_badge', 'updated_at_short'
    ]
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
            'fields': ('status_badge',),
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'sku', 'status_badge']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'color', 'color__product', 'color__product__category'
        )
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.color.product.id])
        return mark_safe(f'<a href="{url}" style="font-weight: 600;">{obj.color.product.name}</a>')
    product_link.short_description = '📦 محصول'
    product_link.admin_order_field = 'color__product__name'
    
    def color_link(self, obj):
        url = reverse('admin:api_productcolor_change', args=[obj.color.id])
        color_preview = ''
        if obj.color.hex_code:
            color_preview = (
                f'<span style="display: inline-block; width: 12px; height: 12px; '
                f'background-color: {obj.color.hex_code}; border-radius: 4px; '
                f'margin-left: 5px; border: 1px solid #ddd; vertical-align: middle;"></span> '
            )
        return mark_safe(f'{color_preview}<a href="{url}" style="vertical-align: middle;">{obj.color.name}</a>')
    color_link.short_description = '🎨 رنگ'
    
    def price_formatted(self, obj):
        return mark_safe(
            f'<span style="direction: ltr; display: inline-block; font-family: monospace; '
            f'font-weight: bold; color: #28a745;">{format_price(obj.price)}</span> تومان'
        )
    price_formatted.short_description = '💰 قیمت'
    
    def stock_with_badge(self, obj):
        status = self.get_stock_status(obj.stock)
        return mark_safe(get_status_badge(f"{obj.stock} عدد", status['color'], status['icon']))
    stock_with_badge.short_description = '📦 موجودی'
    
    def sku_short(self, obj):
        if obj.sku:
            return mark_safe(f'<span style="font-family: monospace; color: #6c757d;">{obj.sku}</span>')
        return '-'
    sku_short.short_description = '🏷️ SKU'
    
    def status_badge(self, obj):
        status = self.get_stock_status(obj.stock)
        return mark_safe(get_status_badge(status['text'], status['color'], status['icon']))
    status_badge.short_description = '⚡ وضعیت'
    
    def updated_at_short(self, obj):
        return self.get_jalali_date(obj.updated_at)
    updated_at_short.short_description = '📅 بروزرسانی'
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    actions = ['increase_stock', 'decrease_stock', 'apply_discount', 'generate_sku']
    
    def increase_stock(self, request, queryset):
        """افزایش موجودی"""
        amount = request.POST.get('amount', 10)
        try:
            amount = int(amount)
            updated = queryset.update(stock=models.F('stock') + amount)
            self.message_user(
                request,
                f'✅ موجودی {updated} سایز به مقدار {amount} عدد افزایش یافت.',
                messages.SUCCESS
            )
        except ValueError:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', messages.ERROR)
    increase_stock.short_description = '📈 افزایش موجودی'
    
    def decrease_stock(self, request, queryset):
        """کاهش موجودی"""
        amount = request.POST.get('amount', 5)
        try:
            amount = int(amount)
            for item in queryset:
                if item.stock >= amount:
                    item.stock -= amount
                    item.save()
            self.message_user(
                request,
                f'✅ موجودی {queryset.count()} سایز به مقدار {amount} عدد کاهش یافت.',
                messages.SUCCESS
            )
        except ValueError:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', messages.ERROR)
    decrease_stock.short_description = '📉 کاهش موجودی'
    
    def apply_discount(self, request, queryset):
        """اعمال تخفیف درصدی"""
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
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    '❌ درصد تخفیف باید بین 1 تا 100 باشد.',
                    messages.ERROR
                )
        except ValueError:
            self.message_user(request, '❌ لطفاً یک عدد معتبر وارد کنید.', messages.ERROR)
    apply_discount.short_description = '💰 اعمال تخفیف درصدی'
    
    def generate_sku(self, request, queryset):
        """ایجاد SKU برای سایزهای بدون SKU"""
        count = 0
        for item in queryset:
            if not item.sku:
                item.save()  # save متد generate_sku را صدا می‌زند
                count += 1
        self.message_user(request, f'✅ SKU برای {count} سایز ایجاد شد.', messages.SUCCESS)
    generate_sku.short_description = '🏷️ ایجاد SKU'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت تصاویر محصول"""
    
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
        return mark_safe(f'<a href="{url}">{obj.product.name}</a>')
    product_link.short_description = '📦 محصول'
    
    def image_thumbnail(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="width: 50px; height: 50px; '
                f'object-fit: cover; border-radius: 8px; border: 1px solid #dee2e6;" />'
            )
        return '-'
    image_thumbnail.short_description = '🖼️ تصویر'
    
    def image_preview_large(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-width: 300px; max-height: 200px; '
                f'object-fit: contain; border-radius: 8px; border: 1px solid #dee2e6;" />'
            )
        return '-'
    image_preview_large.short_description = '👁️ پیش‌نمایش بزرگ'
    
    def created_at_short(self, obj):
        return self.get_jalali_date(obj.created_at)
    created_at_short.short_description = '📅 تاریخ'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت آیتم‌های سبد خرید"""
    
    list_display = [
        'user_link', 'product_info', 'quantity_badge',
        'unit_price_display', 'total_price_display', 'created_at_short'
    ]
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
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'total_price_display']
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return mark_safe(f'<a href="{url}">{obj.user.username}</a>')
    user_link.short_description = '👤 کاربر'
    
    def product_info(self, obj):
        return mark_safe(
            f'<span style="font-weight: bold;">{obj.product_size.color.product.name}</span><br>'
            f'<small style="color: #6c757d;">{obj.product_size.color.name} - {obj.product_size.size}</small>'
        )
    product_info.short_description = '📦 محصول'
    
    def quantity_badge(self, obj):
        if obj.quantity > 5:
            color = 'success'
        elif obj.quantity > 2:
            color = 'info'
        else:
            color = 'secondary'
        return mark_safe(get_status_badge(f"{obj.quantity} عدد", color))
    quantity_badge.short_description = '🔢 تعداد'
    
    def unit_price_display(self, obj):
        return mark_safe(
            f'<span style="font-family: monospace;">{format_price(obj.product_size.price)}</span> تومان'
        )
    unit_price_display.short_description = '💰 قیمت واحد'
    
    def total_price_display(self, obj):
        return mark_safe(
            f'<span style="font-family: monospace; font-weight: bold; color: #28a745;">'
            f'{format_price(obj.total_price)}</span> تومان'
        )
    total_price_display.short_description = '💵 قیمت کل'
    
    def created_at_short(self, obj):
        return self.get_jalali_datetime(obj.created_at)
    created_at_short.short_description = '📅 تاریخ'
    
    def save_model(self, request, obj, form, change):
        """مدیریت خطای یکتا بودن"""
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            if 'already exists' in str(e):
                existing = CartItem.objects.get(user=obj.user, product_size=obj.product_size)
                existing.quantity += obj.quantity
                existing.save()
            else:
                raise e


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت نظرات محصولات"""
    
    list_display = [
        'product_link', 'user_link', 'rating_stars', 'comment_short',
        'helpful_badge', 'is_approved', 'approval_status', 'created_at_short'
    ]
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
        }),
        ('📅 تاریخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'helpful_count', 'rating_stars_large']
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return mark_safe(f'<a href="{url}">{obj.product.name[:30]}</a>')
    product_link.short_description = '📦 محصول'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return mark_safe(f'<a href="{url}">{obj.user.username}</a>')
    user_link.short_description = '👤 کاربر'
    
    def rating_stars(self, obj):
        if obj.rating:
            return mark_safe(get_stars_html(obj.rating, 16))
        return '-'
    rating_stars.short_description = '⭐ امتیاز'
    
    def rating_stars_large(self, obj):
        if obj.rating:
            return mark_safe(
                f'{get_stars_html(obj.rating, 24)}<br>'
                f'<span style="color: #6c757d;">{obj.rating} از 5</span>'
            )
        return '-'
    rating_stars_large.short_description = '⭐ امتیاز'
    
    def comment_short(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'
    comment_short.short_description = '💬 نظر'
    
    def helpful_badge(self, obj):
        if obj.helpful_count > 10:
            return mark_safe(get_status_badge(f"{obj.helpful_count} مفید", 'success'))
        elif obj.helpful_count > 5:
            return mark_safe(get_status_badge(f"{obj.helpful_count} مفید", 'info'))
        return str(obj.helpful_count) if obj.helpful_count else '0'
    helpful_badge.short_description = '👍 مفید'
    
    def approval_status(self, obj):
        if obj.is_approved:
            return mark_safe(get_status_badge('تایید شده', 'success', '✅'))
        return mark_safe(get_status_badge('در انتظار', 'warning', '⏳'))
    approval_status.short_description = '⚡ وضعیت'
    
    def created_at_short(self, obj):
        return self.get_jalali_datetime(obj.created_at)
    created_at_short.short_description = '📅 تاریخ'
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    actions = ['approve_reviews', 'unapprove_reviews', 'delete_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'✅ {updated} دیدگاه تایید شد.', messages.SUCCESS)
    approve_reviews.short_description = '✅ تایید دیدگاه‌ها'
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'❌ {updated} دیدگاه رد شد.', messages.SUCCESS)
    unapprove_reviews.short_description = '❌ رد دیدگاه‌ها'
    
    def delete_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'🗑️ {count} دیدگاه حذف شد.', messages.SUCCESS)
    delete_reviews.short_description = '🗑️ حذف دیدگاه‌ها'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت علاقه‌مندی‌ها"""
    
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
        return mark_safe(f'<a href="{url}">{obj.user.username}</a>')
    user_link.short_description = '👤 کاربر'
    
    def product_link(self, obj):
        url = reverse('admin:api_product_change', args=[obj.product.id])
        return mark_safe(f'<a href="{url}">{obj.product.name}</a>')
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
        return self.get_jalali_datetime(obj.created_at)
    created_at_short.short_description = '📅 تاریخ'
    
    actions = ['remove_from_favorites']
    
    def remove_from_favorites(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'🗑️ {count} محصول از علاقه‌مندی‌ها حذف شد.', messages.SUCCESS)
    remove_from_favorites.short_description = '🗑️ حذف از علاقه‌مندی‌ها'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت کوپن‌های تخفیف"""
    
    list_display = [
        'code', 'discount_display', 'valid_period', 'usage_stats',
        'status_badge', 'is_active', 'created_at_short'
    ]
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
        }),
        ('📊 محدودیت‌ها', {
            'fields': ('max_uses', 'used_count', 'is_active'),
        }),
        ('📅 تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'used_count', 'is_valid_display']
    
    def discount_display(self, obj):
        if obj.max_discount_amount:
            return f'{obj.discount_percent}% (حداکثر {format_price(obj.max_discount_amount)} تومان)'
        return f'{obj.discount_percent}%'
    discount_display.short_description = '💰 تخفیف'
    
    def valid_period(self, obj):
        if obj.valid_from and obj.valid_to:
            return (
                f'{obj.valid_from.strftime("%Y/%m/%d")} '
                f'تا {obj.valid_to.strftime("%Y/%m/%d")}'
            )
        return '⚠️ تاریخ مشخص نشده'
    valid_period.short_description = '📆 مدت اعتبار'
    
    def usage_stats(self, obj):
        if obj.max_uses > 0:
            percentage = (obj.used_count / obj.max_uses) * 100
            color = '#28a745' if percentage < 80 else '#dc3545'
            return mark_safe(
                f'<span style="font-weight: bold;">{obj.used_count}/{obj.max_uses}</span><br>'
                f'<div style="width: 80px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin-top: 5px;">'
                f'<div style="width: {percentage}%; background: {color}; height: 4px;"></div>'
                f'</div>'
            )
        return f'{obj.used_count}/∞'
    usage_stats.short_description = '📊 مصرف'
    
    def status_badge(self, obj):
        if obj.is_valid():
            return mark_safe(get_status_badge('فعال', 'success', '✅'))
        return mark_safe(get_status_badge('غیرفعال', 'danger', '❌'))
    status_badge.short_description = '⚡ وضعیت'
    
    def is_valid_display(self, obj):
        if not obj.valid_from or not obj.valid_to:
            return mark_safe('<span style="color: #ffc107;">⚠️ تاریخ اعتبار مشخص نشده</span>')
        
        if obj.is_valid():
            return mark_safe('<span style="color: #28a745;">✅ این کوپن معتبر است</span>')
        
        return mark_safe('<span style="color: #dc3545;">❌ این کوپن منقضی شده یا غیرفعال است</span>')
    is_valid_display.short_description = '🔍 بررسی اعتبار'
    
    def created_at_short(self, obj):
        return self.get_jalali_date(obj.created_at)
    created_at_short.short_description = '📅 تاریخ ایجاد'
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    actions = ['activate_coupons', 'deactivate_coupons', 'reset_usage']
    
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} کوپن فعال شد.', messages.SUCCESS)
    activate_coupons.short_description = '✅ فعال کردن کوپن‌ها'
    
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ {updated} کوپن غیرفعال شد.', messages.SUCCESS)
    deactivate_coupons.short_description = '❌ غیرفعال کردن کوپن‌ها'
    
    def reset_usage(self, request, queryset):
        updated = queryset.update(used_count=0)
        self.message_user(request, f'🔄 تعداد مصرف {updated} کوپن ریست شد.', messages.SUCCESS)
    reset_usage.short_description = '🔄 ریست تعداد مصرف'


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin, JalaliDateMixin):
    """مدیریت کدهای تایید ایمیل"""
    
    list_display = [
        'email', 'code', 'usage_status', 'expiry_status',
        'is_used', 'created_at_short'
    ]
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
        }),
    )
    readonly_fields = ['created_at', 'expiry_status_display']
    
    def usage_status(self, obj):
        if obj.is_used:
            return mark_safe(get_status_badge('استفاده شده', 'secondary', '✅'))
        return mark_safe(get_status_badge('استفاده نشده', 'success', '🆕'))
    usage_status.short_description = '📌 وضعیت مصرف'
    
    def expiry_status(self, obj):
        if not obj.created_at:
            return mark_safe('<span style="color: #ffc107;">⚠️ تاریخ نامشخص</span>')
        
        if obj.is_expired():
            return mark_safe('<span style="color: #dc3545;">❌ منقضی شده</span>')
        
        remaining = max(0, (obj.created_at + timedelta(minutes=10) - timezone.now()).seconds // 60)
        return mark_safe(f'<span style="color: #28a745;">✅ معتبر ({remaining} دقیقه)</span>')
    expiry_status.short_description = '⏳ انقضا'
    
    def expiry_status_display(self, obj):
        if not obj.created_at:
            return mark_safe('<span style="color: #ffc107;">⚠️ تاریخ ایجاد کد نامشخص است</span>')
        
        expiration_time = obj.created_at + timedelta(minutes=10)
        
        if obj.is_expired():
            return mark_safe(
                f'<span style="color: #dc3545;">❌ این کد در '
                f'{expiration_time.strftime("%Y/%m/%d %H:%M")} منقضی شده است</span>'
            )
        
        remaining = max(0, (expiration_time - timezone.now()).seconds // 60)
        return mark_safe(
            f'<span style="color: #28a745;">✅ این کد تا '
            f'{expiration_time.strftime("%Y/%m/%d %H:%M")} معتبر است '
            f'({remaining} دقیقه باقی)</span>'
        )
    expiry_status_display.short_description = '🔍 وضعیت انقضا'
    
    def created_at_short(self, obj):
        return self.get_jalali_datetime(obj.created_at)
    created_at_short.short_description = '📅 تاریخ ایجاد'
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    actions = ['mark_as_used', 'mark_as_unused', 'delete_expired']
    
    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'✅ {updated} کد به عنوان استفاده شده علامت زده شد.', messages.SUCCESS)
    mark_as_used.short_description = '✅ علامت به عنوان استفاده شده'
    
    def mark_as_unused(self, request, queryset):
        updated = queryset.update(is_used=False)
        self.message_user(request, f'🔄 {updated} کد به عنوان استفاده نشده علامت زده شد.', messages.SUCCESS)
    mark_as_unused.short_description = '🔄 علامت به عنوان استفاده نشده'
    
    def delete_expired(self, request, queryset):
        expired = [obj for obj in queryset if obj.is_expired()]
        count = len(expired)
        for obj in expired:
            obj.delete()
        self.message_user(request, f'🗑️ {count} کد منقضی شده حذف شد.', messages.SUCCESS)
    delete_expired.short_description = '🗑️ حذف کدهای منقضی شده'