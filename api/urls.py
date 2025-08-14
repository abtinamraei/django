from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    ProductListByCategory,
    CategoryListView,
    RegisterView,
    UserProfileView,
    ChangePasswordView,
    SendEmailVerificationCodeView,
    VerifyEmailCodeView,
    RegisterWithEmailView,
    ProductDetailView,
    CartItemListCreateView,
    CartItemUpdateDeleteView
)

urlpatterns = [
    path('products/', ProductListByCategory.as_view(), name='products-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/', CategoryListView.as_view(), name='categories-list'),

    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/send-verification-code/', SendEmailVerificationCodeView.as_view(), name='send-verification-code'),
    path('auth/verify-email-code/', VerifyEmailCodeView.as_view(), name='verify-email-code'),
    path('auth/register-with-email/', RegisterWithEmailView.as_view(), name='register-with-email'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Cart
    path('cart/', CartItemListCreateView.as_view(), name='cart-list-create'),
    path('cart/<int:pk>/', CartItemUpdateDeleteView.as_view(), name='cart-update-delete'),
]
