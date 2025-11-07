import random
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import (
    EmailVerificationCode, Category, Product, CartItem,
    ProductReview, Favorite
)
from .serializers import (
    EmailSerializer, VerifyEmailCodeSerializer, RegisterWithEmailSerializer,
    RegisterSerializer, CategorySerializer, ProductSerializer, CartItemSerializer,
    ProductReviewSerializer, FavoriteSerializer
)

# ---------------------- Auth APIs ----------------------
@method_decorator(csrf_exempt, name='dispatch')
class SendEmailVerificationCodeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            EmailVerificationCode.objects.update_or_create(
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
            return Response({'detail': 'کد تایید به ایمیل شما ارسال شد.'}, status=status.HTTP_200_OK)
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
            return Response({'detail': 'ایمیل با موفقیت تایید شد.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterWithEmailView(CreateAPIView):
    serializer_class = RegisterWithEmailSerializer
    permission_classes = []


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = []


# ---------------------- Category & Product APIs ----------------------
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
            queryset = queryset.filter(category__name__icontains=category_name)
        if search_term:
            queryset = queryset.filter(Q(name__icontains=search_term) | Q(description__icontains=search_term))
        return queryset

    def get_serializer_context(self):
        return {'request': self.request}


class ProductDetailView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}


# ---------------------- User APIs ----------------------
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

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


# ---------------------- Cart APIs ----------------------
class CartItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CartItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product_size = serializer.validated_data['product_size']
            quantity = serializer.validated_data.get('quantity', 1)
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product_size=product_size,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                if cart_item.quantity > product_size.stock:
                    cart_item.quantity = product_size.stock
                cart_item.save()
            return Response(CartItemSerializer(cart_item, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return CartItem.objects.get(pk=pk, user=user)
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
            return Response({'detail': 'مقدار quantity باید عدد صحیح باشد.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity <= 0:
            cart_item.delete()
            return Response({'detail': 'آیتم حذف شد.'}, status=status.HTTP_200_OK)
        if quantity > cart_item.product_size.stock:
            quantity = cart_item.product_size.stock
        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item, context={'request': request}).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        cart_item = self.get_object(pk, request.user)
        if not cart_item:
            return Response({'detail': 'آیتم سبد یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        cart_item.delete()
        return Response({'detail': 'آیتم حذف شد.'}, status=status.HTTP_200_OK)


# ---------------------- Reviews APIs ----------------------
class ProductReviewListCreateView(APIView):
    """
    لیست و ثبت نظر برای یک محصول
    - کاربران ثبت‌نام‌شده: فقط یک نظر، اگر دوباره ثبت کنند، آپدیت می‌شود
    - کاربران ناشناس: می‌توانند چند نظر ثبت کنند
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'محصول یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        reviews = ProductReview.objects.filter(product=product).order_by('-created_at')
        serializer = ProductReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'detail': 'محصول یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user if request.user.is_authenticated else None
        data = request.data.copy()

        if user:
            # کاربران ثبت‌نام‌شده محدود به یک نظر هستند
            obj, created = ProductReview.objects.update_or_create(
                product=product,
                user=user,
                defaults={
                    'rating': data.get('rating'),
                    'comment': data.get('comment', '')
                }
            )
            serializer = ProductReviewSerializer(obj, context={'request': request})
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        else:
            # کاربران ناشناس می‌توانند چند نظر ثبت کنند
            serializer = ProductReviewSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save(product=product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewUpdateDeleteView(APIView):
    """
    ویرایش و حذف نظر توسط کاربر
    """
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

        serializer = ProductReviewSerializer(review, data=request.data, partial=True, context={'request': request})
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


# ---------------------- Favorites APIs ----------------------
class FavoriteListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user)
        serializer = FavoriteSerializer(favorites, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FavoriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Favorite.objects.get(pk=pk, user=user)
        except Favorite.DoesNotExist:
            return None

    def delete(self, request, pk):
        favorite = self.get_object(pk, request.user)
        if not favorite:
            return Response({'detail': 'آیتم مورد علاقه یافت نشد.'}, status=status.HTTP_404_NOT_FOUND)
        favorite.delete()
        return Response({'detail': 'آیتم مورد علاقه حذف شد.'}, status=status.HTTP_200_OK)
