from django.contrib import admin
from .models import Category, Product, ProductColor, ProductSize

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    inlines = [ProductColorInline, ProductSizeInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductColor)
admin.site.register(ProductSize)
