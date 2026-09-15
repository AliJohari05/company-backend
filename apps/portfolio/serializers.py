from rest_framework import serializers

from .models import Category, PortfolioImage, PortfolioItem, Technology


class PortfolioCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "title", "title_en", "slug")


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ("id", "name", "name_en", "icon")


class PortfolioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioImage
        fields = ("id", "image", "caption", "caption_en")


class PortfolioItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing portfolio items on main pages."""

    category = PortfolioCategorySerializer(read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioItem
        fields = (
            "id",
            "title",
            "title_en",
            "slug",
            "category",
            "technologies",
            "cover_image",
            "summary",
            "summary_en",
            "video_url",
            "github_url",
            "live_demo_url",
            "is_featured",
        )


class PortfolioItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer including gallery images for full single project view."""

    category = PortfolioCategorySerializer(read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)
    images = PortfolioImageSerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioItem
        fields = (
            "id",
            "title",
            "title_en",
            "slug",
            "category",
            "technologies",
            "cover_image",
            "summary",
            "summary_en",
            "description",
            "description_en",
            "video_url",
            "github_url",
            "live_demo_url",
            "client_name",
            "is_featured",
            "created_at",
            "images",
        )
