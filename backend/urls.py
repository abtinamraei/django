from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import home  # مسیر ویو اصلی سایت

urlpatterns = [
    # مسیر صفحه اصلی
    path('', home, name='home'),

    # مسیر ادمین
    path('admin/', admin.site.urls),

    # مسیرهای JWT برای لاگین و ریفرش توکن
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # مسیرهای اپلیکیشن API
    path('api/', include('api.urls')),
]

# اضافه کردن مسیرهای استاتیک و مدیا در حالت DEBUG
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
