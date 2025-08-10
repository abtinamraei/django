from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# لیست دسته‌بندی‌ها
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

# لیست محصولات بر اساس نام دسته‌بندی و جستجو
class ProductListByCategory(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category_name = self.request.query_params.get('category')
        search_term = self.request.query_params.get('search')

        queryset = Product.objects.all()

        if category_name and category_name.lower() != 'all':
            queryset = queryset.filter(category__name=category_name)

        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term)
            )

        return queryset

# ثبت نام
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

# پروفایل کاربر
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

# تغییر رمز عبور
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'detail': 'هر دو فیلد old_password و new_password الزامی هستند.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'detail': 'رمز عبور فعلی اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'رمز عبور با موفقیت تغییر یافت.'}, status=status.HTTP_200_OK)
