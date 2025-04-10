from rest_framework import serializers
from .models import Product, Category, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)  # Ensure the image URL is absolute

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()
    category_id = serializers.PrimaryKeyRelatedField(source='category', read_only=True)  # Add category ID for debugging
    primary_image = serializers.SerializerMethodField()

    def get_primary_image(self, obj):
        first_image = obj.images.first()
        if first_image:
            return ProductImageSerializer(first_image, context=self.context).data
        return None

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price', 'category', 'category_id', 'images', 'primary_image', 'stock', 'is_active']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'category_type', 'is_active']