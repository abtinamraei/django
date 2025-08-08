from django.urls import path
from .views import ProductListByCategory

urlpatterns = [
    path('products/', ProductListByCategory.as_view(), name='products-list'),
]
