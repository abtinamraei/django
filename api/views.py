from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer

class ProductListByCategory(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        category_name = self.request.query_params.get('category')
        if category_name:
            return Product.objects.filter(category__name__iexact=category_name)
        return Product.objects.all()
