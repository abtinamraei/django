from django.http import HttpResponse
from django.urls import path, include
from django.contrib import admin

def home(request):
    return HttpResponse("Welcome to the backend API!")

urlpatterns = [
    path('', home),  # مسیر صفحه اصلی
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]