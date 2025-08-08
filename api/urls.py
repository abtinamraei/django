from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import ProductListByCategory, CategoryListView, RegisterView

urlpatterns = [
    path('products/', ProductListByCategory.as_view(), name='products-list'),
    path('categories/', CategoryListView.as_view(), name='categories-list'),

    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
]
