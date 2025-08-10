import random
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import EmailVerificationCode
from .serializers import (
    EmailSerializer, VerifyEmailCodeSerializer, RegisterWithEmailSerializer,
    RegisterSerializer, CategorySerializer, ProductSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from django.db.models import Q

# ارسال کد تایید ایمیل
class SendEmailVerificationCodeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = ''.join([str(random.randint(0,9)) for _ in range(6)])

            obj, created = EmailVerificationCode.objects.update_or_create(
                email=email,
                defaults={'code': code}
            )

            send_mail(
                'کد تایید ایمیل',
                f'کد تایید شما: {code}',
                'no-reply@example.com',
                [email],
                fail_silently=False,
            )

            return Response({'detail': 'کد تایید به ایمیل شما ارسال شد.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# بررسی کد تایید ایمیل
class VerifyEmailCodeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']

            try:
                evc = EmailVerificationCode.objects.get(email=email)
            except EmailVerificationCode.DoesNotExist:
                return Response({'detail': 'کد تایید یافت نشد.'}, status=status.HTTP_400_BAD_REQUEST)

            if evc.is_expired():
                return Response({'detail': 'کد تایید منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)

            if evc.code != code:
                return Response({'detail': 'کد تایید اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'detail': 'ایمیل با موفقیت تایید شد.'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ثبت نام با ایمیل و کد تایید
class RegisterWithEmailView(generics.CreateAPIView):
    serializer_class = RegisterWithEmailSerializer
    permission_classes = []

# بقیه ویوهای شما (مثلاً دسته‌بندی‌ها و محصولات)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

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

# پروفایل و تغییر رمز هم مثل قبلی خودت
