import random
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny

from .models import (
    EmailVerificationCode, Category, Product, CartItem,
    ProductReview, Favorite, Coupon
)
from .serializers import (
    EmailSerializer, VerifyEmailCodeSerializer, RegisterWithEmailSerializer,
    RegisterSerializer, CategorySerializer, ProductListSerializer, 
    ProductDetailSerializer, CartItemSerializer, ProductReviewSerializer,
    FavoriteSerializer, CouponSerializer
)

# ============================== Auth APIs ==============================

@method_decorator(csrf_exempt, name='dispatch')
class SendEmailVerificationCodeView(APIView):
    """ارسال کد تایید ایمیل"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            EmailVerificationCode.objects.update_or_create(
                email=email,
                defaults={'code': code, 'is_used': False}
            )
            
            send_mail(
                'کد تایید ایمیل',
                f'کد تایید شما: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({'detail': 'کد تایید به ایمیل شما ارسال شد.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailCodeView(APIView):
    """تایید کد ایمیل"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            
            try:
                evc = EmailVerificationCode.objects.get(email=email, is_used=False)
            except EmailVerificationCode.DoesNotExist:
                return Response({'detail': 'کد تایید یافت نشد.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if evc.is_expired():
                evc.delete()
                return Response({'detail': 'کد تایید منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if evc.code != code:
                return Response({'detail': 'کد تایید اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)
            
            evc.is_used = True
            evc.save()
            return Response({'detail': 'ایمیل با موفقیت تایید شد.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterWithEmailView(CreateAPIView):
    """ثبت‌نام با ایمیل تایید شده"""
    serializer_class = RegisterWithEmailSerializer
    permission_classes = [AllowAny]


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(CreateAPIView):
    """ثبت‌نام عادی"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserProfileView(APIView):
    """پروفایل کاربر"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordView(APIView):
    """تغییر رمز عبور"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'detail': 'هر دو فیلد old_password و new_password الزامی هستند.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(old_password):
            return Response({'detail': 'رمز عبور فعلی اشتباه است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'رمز عبور با موفقیت تغییر یافت.'}, status=status.HTTP_200_OK)


# ============================== Category & Product APIs ==============================

class CategoryListView(ListAPIView):
    """لیست دسته‌بندی‌ها"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListByCategory(ListAPIView):
    """لیست محصولات با قابلیت فیلتر بر اساس دسته‌بندی و جستجو"""
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        category_name = self.request.query_params.get('category')
        search_term = self.request.query_params.get('search')
        
        queryset = Product.objects.filter(is_active=True)
        
        if category_name and category_name.lower() != 'all':
            queryset = queryset.filter(category__name__icontains=category_name)
        
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | 
                Q(description__icontains=search_term)
            )
        
        return queryset.select_related('category').prefetch_related(
            'colors__sizes', 'images', 'reviews'
        )

    def get_serializer_context(self):
        return {'request': self.request}


class ProductDetailView(RetrieveAPIView):
    """جزئیات محصول"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_object(self):
        obj = super().get_object()
        # افزایش بازدید
        obj.view_count += 1
        obj.save(update_fields=['view_count'])
        return obj


# ============================== Cart APIs ==============================

class CartItemListCreateView(APIView):
    """لیست و افزودن به سبد خرید"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related(
            'product_size__color__product'
        )
        serializer = CartItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CartItemSerializer(
            data=request.data, 
            context={'request': request}
        )
        if serializer.is_valid():
            cart_item = serializer.save()
            return Response(
                CartItemSerializer(cart_item, context={'request': request}).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemUpdateDeleteView(APIView):
    """به‌روزرسانی و حذف آیتم سبد خرید"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return CartItem.objects.select_related(
                'product_size__color__product'
            ).get(pk=pk, user=user)
        except CartItem.DoesNotExist:
            return None

    def put(self, request, pk):
        cart_item = self.get_object(pk, request.user)
        if not cart_item:
            return Response({'detail': 'آیتم سبد یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        
        quantity = request.data.get('quantity')
        if quantity is None:
            return Response({'detail': 'فیلد quantity الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            quantity = int(quantity)
        except ValueError:
            return Response(
                {'detail': 'مقدار quantity باید عدد صحیح باشد.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity <= 0:
            cart_item.delete()
            return Response({'detail': 'آیتم حذف شد.'}, status=status.HTTP_200_OK)
        
        if quantity > cart_item.product_size.stock:
            quantity = cart_item.product_size.stock
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response(
            CartItemSerializer(cart_item, context={'request': request}).data, 
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        cart_item = self.get_object(pk, request.user)
        if not cart_item:
            return Response({'detail': 'آیتم سبد یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item.delete()
        return Response({'detail': 'آیتم حذف شد.'}, status=status.HTTP_200_OK)


# ============================== Reviews APIs ==============================

class ProductReviewListCreateView(APIView):
    """
    لیست و ثبت نظر برای یک محصول
    - کاربران ثبت‌نام‌شده: فقط یک نظر
    - کاربران ناشناس: نمی‌توانند نظر ثبت کنند (فقط مشاهده)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response({'detail': 'محصول یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        reviews = ProductReview.objects.filter(
            product=product, is_approved=True
        ).select_related('user').order_by('-created_at')
        
        serializer = ProductReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'برای ثبت نظر باید وارد شوید.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            product = Product.objects.get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response({'detail': 'محصول یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        # بررسی وجود نظر قبلی
        existing_review = ProductReview.objects.filter(
            product=product, user=request.user
        ).first()
        
        if existing_review:
            # آپدیت نظر قبلی
            serializer = ProductReviewSerializer(
                existing_review, 
                data=request.data, 
                context={'request': request},
                partial=True
            )
        else:
            # ایجاد نظر جدید
            serializer = ProductReviewSerializer(
                data=request.data, 
                context={'request': request}
            )
        
        if serializer.is_valid():
            review = serializer.save(product=product)
            return Response(
                ProductReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_200_OK if existing_review else status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewUpdateDeleteView(APIView):
    """ویرایش و حذف نظر توسط کاربر"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return ProductReview.objects.get(pk=pk, user=user)
        except ProductReview.DoesNotExist:
            return None

    def put(self, request, pk):
        review = self.get_object(pk, request.user)
        if not review:
            return Response({'detail': 'نظر یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductReviewSerializer(
            review, 
            data=request.data, 
            partial=True, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        review = self.get_object(pk, request.user)
        if not review:
            return Response({'detail': 'نظر یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        
        review.delete()
        return Response({'detail': 'نظر حذف شد.'}, status=status.HTTP_200_OK)


# ============================== Favorites APIs ==============================

class FavoriteListCreateView(APIView):
    """لیست و افزودن به علاقه‌مندی‌ها"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).select_related('product')
        serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FavoriteSerializer(
            data=request.data, 
            context={'request': request}
        )
        if serializer.is_valid():
            favorite = serializer.save()
            return Response(
                FavoriteSerializer(favorite, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteDeleteView(APIView):
    """حذف از علاقه‌مندی‌ها"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            favorite = Favorite.objects.get(pk=pk, user=request.user)
            favorite.delete()
            return Response({'detail': 'آیتم مورد علاقه حذف شد.'}, status=status.HTTP_200_OK)
        except Favorite.DoesNotExist:
            return Response({'detail': 'آیتم مورد علاقه یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)


# ============================== Coupon APIs ==============================

class CouponValidateView(APIView):
    """اعتبارسنجی کوپن تخفیف"""
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'detail': 'کد کوپن الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
        except Coupon.DoesNotExist:
            return Response({'detail': 'کوپن یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        
        if not coupon.is_valid():
            return Response({'detail': 'کوپن منقضی شده است.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'code': coupon.code,
            'discount_percent': coupon.discount_percent,
            'max_discount_amount': float(coupon.max_discount_amount) if coupon.max_discount_amount else None
        }, status=status.HTTP_200_OK)