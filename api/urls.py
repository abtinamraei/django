from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    ProductListByCategory,
    ProductDetailView,
    CategoryListView,
    RegisterView,
    UserProfileView,
    ChangePasswordView,
    SendEmailVerificationCodeView,
    VerifyEmailCodeView,
    RegisterWithEmailView,
    CartItemListCreateView,
    CartItemUpdateDeleteView,
    ProductReviewListCreateView,
    ProductReviewUpdateDeleteView,
    FavoriteListCreateView,
    FavoriteDeleteView
)

app_name = "api"  # برای جلوگیری از تداخل نام‌ها در پروژه‌های بزرگ

urlpatterns = [
    # Products
    path("products/", ProductListByCategory.as_view(), name="products-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),

    # Categories
    path("categories/", CategoryListView.as_view(), name="categories-list"),

    # Authentication
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/send-verification-code/", SendEmailVerificationCodeView.as_view(), name="send-verification-code"),
    path("auth/verify-email-code/", VerifyEmailCodeView.as_view(), name="verify-email-code"),
    path("auth/register-with-email/", RegisterWithEmailView.as_view(), name="register-with-email"),
    path("auth/profile/", UserProfileView.as_view(), name="user-profile"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),

    # Cart
    path("cart/", CartItemListCreateView.as_view(), name="cart-list-create"),
    path("cart/<int:pk>/", CartItemUpdateDeleteView.as_view(), name="cart-update-delete"),

    # Reviews (نظرات محصول)
    path("products/<int:pk>/reviews/", ProductReviewListCreateView.as_view(), name="product-review-list-create"),
    path("reviews/<int:pk>/", ProductReviewUpdateDeleteView.as_view(), name="product-review-update-delete"),

    # Favorites
    path("favorites/", FavoriteListCreateView.as_view(), name="favorite-list-create"),
    path("favorites/<int:pk>/", FavoriteDeleteView.as_view(), name="favorite-delete"),
]
