from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
import logging

# Configurer un logger
logger = logging.getLogger(__name__)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            category_id = self.request.query_params.get('category')
            if category_id:
                queryset = queryset.filter(category_id=category_id)
            logger.info(f"ProductViewSet: Queryset returned {queryset.count()} products")
            return queryset
        except Exception as e:
            logger.error(f"Erreur dans ProductViewSet.get_queryset: {str(e)}", exc_info=True)
            raise

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True, category_type='product')  # Filter by product type by default
    serializer_class = CategorySerializer

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            logger.info(f"CategoryViewSet: Initial queryset {queryset.count()} categories")
            category_type = self.request.query_params.get('type')
            if category_type:
                queryset = queryset.filter(category_type=category_type)
                logger.info(f"CategoryViewSet: Filtered queryset {queryset.count()} categories with type={category_type}")
            else:
                logger.info(f"CategoryViewSet: Default filter applied, {queryset.count()} product categories")
            return queryset
        except Exception as e:
            logger.error(f"Erreur dans CategoryViewSet.get_queryset: {str(e)}", exc_info=True)
            raise

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"CategoryViewSet: Successfully serialized {len(serializer.data)} categories")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Erreur dans CategoryViewSet.list: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Une erreur est survenue lors de la récupération des catégories: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )