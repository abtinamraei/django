from django.urls import path
from .views import RegisterView, ProductCreateView, ProductListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/add/', ProductCreateView.as_view(), name='product-add'),
]