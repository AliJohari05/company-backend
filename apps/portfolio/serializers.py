from rest_framework import serializers

from apps.core.localization import LocalizedContentSerializerMixin

from .models import Category, PortfolioImage, PortfolioItem, Technology


class PortfolioCategorySerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title",)
    class Meta:
        model = Category
        fields = ("id", "title", "title_en", "slug")


class TechnologySerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("name",)
    class Meta:
        model = Technology
        fields = ("id", "name", "name_en", "icon")


class PortfolioImageSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("caption",)
    class Meta:
        model = PortfolioImage
        fields = ("id", "image", "caption", "caption_en")


class PortfolioItemListSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title", "summary")
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


class PortfolioItemDetailSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title", "summary", "description")
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
