from django.contrib import admin
from .models import Category, Product, ProductColor, ProductSize

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    inlines = [ProductSizeInline]  # اینجا نمی‌شود مستقیم اینلاین توی اینلاین گذاشت، باید روش جایگزین داشته باشی

class ProductColorAdmin(admin.ModelAdmin):
    inlines = [ProductSizeInline]

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    inlines = [ProductColorInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductColor, ProductColorAdmin)
# admin.site.register(ProductSize)  # چون در رنگ به صورت inline هست، نیازی به ثبت جداگانه نیست
