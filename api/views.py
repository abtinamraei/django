import random
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.generics import RetrieveAPIView

from .models import EmailVerificationCode, Category, Product
from .serializers import (
    EmailSerializer, VerifyEmailCodeSerializer, RegisterWithEmailSerializer,
    RegisterSerializer, CategorySerializer, ProductSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


@method_decorator(csrf_exempt, name='dispatch')
class SendEmailVerificationCodeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            obj, created = EmailVerificationCode.objects.update_or_create(
                email=email,
                defaults={'code': code}
            )

            send_mail(
                'کد تایید ایمیل',
                f'کد تایید شما: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return Response({'detail': 'کد تایید به ایمیل شما ارسال شد.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
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


@method_decorator(csrf_exempt, name='dispatch')
class RegisterWithEmailView(generics.CreateAPIView):
    serializer_class = RegisterWithEmailSerializer
    permission_classes = []


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = []


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

    def get_serializer_context(self):
        return {'request': self.request}


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}


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


@method_decorator(csrf_exempt, name='dispatch')
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
