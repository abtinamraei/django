from django.contrib import admin
from .models import Category, Product, ProductColor, ProductSize

# Inline برای رنگ‌های محصول
class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    # نمایش فیلدهای قابل ویرایش
    fields = ['name', 'hex_code']

# Inline برای سایزهای محصول
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    # نمایش فیلدهای قابل ویرایش
    fields = ['size', 'price', 'stock']

# مدیریت مدل Product
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_display']
    list_filter = ['category']
    search_fields = ['name', 'description']
    inlines = [ProductColorInline, ProductSizeInline]

    # نمایش حداقل قیمت محصول بر اساس سایزها
    def price_display(self, obj):
        sizes = obj.sizes.all()
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price
    price_display.short_description = 'قیمت'

# ثبت مدل‌ها در ادمین
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductColor)
admin.site.register(ProductSize)
