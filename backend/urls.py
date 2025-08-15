from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({"message": "API is running"})

urlpatterns = [
    path('', api_root),  # مسیر روت تست API
    path('auth/', include('api.auth_urls')),  # مسیرهای احراز هویت
    path('categories/', include('api.categories_urls')),  # مسیرهای دسته‌بندی
    path('products/', include('api.products_urls')),  # مسیرهای محصولات
]
