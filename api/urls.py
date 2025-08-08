from django.urls import path
from .views import ProductListByCategory

urlpatterns = [
    path('products/', ProductListByCategory.as_view(), name='products-list'),
    path('api/categories/', CategoryList.as_view(), name='category-list'),
]
