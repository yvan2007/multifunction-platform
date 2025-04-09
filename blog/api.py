# blog/api.py
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Article
from .serializers import ArticleSerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(status='published')
    serializer_class = ArticleSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def retrieve(self, request, slug=None):
        try:
            article = Article.objects.get(slug=slug, status='published')
            serializer = self.get_serializer(article)
            return Response(serializer.data)
        except Article.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)