from django.urls import path
from .views import ProductListByCategory

urlpatterns = [
    path('products/', ProductListByCategory.as_view(), name='product-list-by-category'),
]
