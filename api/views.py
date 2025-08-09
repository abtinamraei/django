from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# لیست دسته‌بندی‌ها
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

# لیست محصولات بر اساس نام دسته‌بندی از کوئری پارامتر ?category=...
class ProductListByCategory(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category_name = self.request.query_params.get('category')
        if category_name:
            return Product.objects.filter(category__name=category_name)
        return Product.objects.all()

# ثبت نام
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

# دریافت پروفایل کاربر
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
