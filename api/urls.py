from django.urls import path
from .views import ProductListByCategory, CategoryListView

urlpatterns = [
    path('products/', ProductListByCategory.as_view(), name='products-list'),
    path('categories/', CategoryListView.as_view(), name='categories-list'),
]
