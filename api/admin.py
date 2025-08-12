from django.contrib import admin
from .models import Category, Product, ProductVariant

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # فرم‌های خالی برای افزودن وریانت جدید

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    inlines = [ProductVariantInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
# admin.site.register(ProductVariant)  # چون وریانت‌ها در محصول inline هستند، نیازی به ثبت جداگانه نیست
