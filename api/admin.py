from django.contrib import admin
from .models import Category, Product, ProductColor, ProductSize

class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ['size', 'price', 'stock']

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code']
    show_change_link = True

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_display']
    list_filter = ['category']
    search_fields = ['name', 'description']
    inlines = [ProductColorInline]

    def price_display(self, obj):
        sizes = ProductSize.objects.filter(color__product=obj)
        if sizes.exists():
            return min(size.price for size in sizes)
        return obj.price
    price_display.short_description = 'کمترین قیمت'

class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'product']
    inlines = [ProductSizeInline]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductColor, ProductColorAdmin)
admin.site.register(ProductSize)
