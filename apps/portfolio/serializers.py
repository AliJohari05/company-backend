from rest_framework import serializers
from .models import Category, Technology, PortfolioItem, PortfolioImage


class PortfolioCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title', 'slug')


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ('id', 'name', 'icon')


class PortfolioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioImage
        fields = ('id', 'image', 'caption')


class PortfolioItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing portfolio items on main pages."""
    category = PortfolioCategorySerializer(read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioItem
        fields = (
            'id',
            'title',
            'slug',
            'category',
            'technologies',
            'cover_image',
            'summary',
            'github_url',
            'live_demo_url',
            'is_featured'
        )


class PortfolioItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer including gallery images for full single project view."""
    category = PortfolioCategorySerializer(read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)
    images = PortfolioImageSerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioItem
        fields = (
            'id',
            'title',
            'slug',
            'category',
            'technologies',
            'cover_image',
            'summary',
            'description',
            'github_url',
            'live_demo_url',
            'client_name',
            'is_featured',
            'created_at',
            'images'
        )
