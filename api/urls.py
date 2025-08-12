from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    CategoryListView, ProductListByCategory, ProductDetailView,
    RegisterView, RegisterWithEmailView,
    UserProfileView, ChangePasswordView,
    SendEmailVerificationCodeView, VerifyEmailCodeView,
    ProductColorListCreateView, ProductColorDetailView,
    ProductSizeListCreateView, ProductSizeDetailView,
)

urlpatterns = [
    # محصولات و دسته‌بندی‌ها
    path('categories/', CategoryListView.as_view(), name='categories-list'),
    path('products/', ProductListByCategory.as_view(), name='products-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # رنگ‌ها
    path('colors/', ProductColorListCreateView.as_view(), name='colors-list-create'),
    path('colors/<int:pk>/', ProductColorDetailView.as_view(), name='color-detail'),

    # سایزها
    path('sizes/', ProductSizeListCreateView.as_view(), name='sizes-list-create'),
    path('sizes/<int:pk>/', ProductSizeDetailView.as_view(), name='size-detail'),

    # احراز هویت و کاربران
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/register-with-email/', RegisterWithEmailView.as_view(), name='register-with-email'),

    # ایمیل و تایید کد
    path('auth/send-verification-code/', SendEmailVerificationCodeView.as_view(), name='send-verification-code'),
    path('auth/verify-email-code/', VerifyEmailCodeView.as_view(), name='verify-email-code'),

    # پروفایل و تغییر رمز
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
]
