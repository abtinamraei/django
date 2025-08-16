from django.contrib import admin
from .models import Category, Product, ProductColor, ProductSize, ProductImage, CartItem

# Inline برای تصاویر محصول
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'order']
    ordering = ['order']

# Inline برای سایزها
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price', 'stock']

# Inline برای رنگ‌ها
class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code']
    show_change_link = True
    inlines = [ProductSizeInline]  # توجه: این فقط برای مدیریت رابطه است، ممکن است نیاز به Nested admin داشته باشیم

# مدیریت محصول
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'min_price']
    list_filter = ['category']
    search_fields = ['name', 'description']
    inlines = [ProductColorInline, ProductImageInline]

    def min_price(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price
    min_price.short_description = 'کمترین قیمت'

# مدیریت رنگ محصول
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'product']
    inlines = [ProductSizeInline]

# مدیریت سبد خرید
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

# ثبت مدل‌ها در ادمین
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductColor, ProductColorAdmin)
admin.site.register(ProductSize)
admin.site.register(ProductImage)
admin.site.register(CartItem, CartItemAdmin)
