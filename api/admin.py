import nested_admin
from django.contrib import admin
from .models import Category, Product, ProductColor, ProductSize

class ProductSizeInline(nested_admin.NestedTabularInline):
    model = ProductSize
    extra = 1

class ProductColorInline(nested_admin.NestedStackedInline):
    model = ProductColor
    extra = 1
    inlines = [ProductSizeInline]

class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ['name', 'category', 'price']
    inlines = [ProductColorInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
