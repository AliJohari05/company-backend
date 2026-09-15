from rest_framework import serializers

from apps.core.localization import LocalizedContentSerializerMixin

from .models import Service, ServiceCategory, ServicePlan


class ServicePlanSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title", "features")
    """Serializer for pricing plans within a specific service."""

    class Meta:
        model = ServicePlan
        fields = ("id", "title", "title_en", "price", "features", "features_en", "is_popular")


class ServiceListSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title", "short_description")
    """Compact serializer for service listings and category lists."""

    category_name = serializers.CharField(source="category.title", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    class Meta:
        model = Service
        fields = (
            "id",
            "category",
            "category_name",
            "category_slug",
            "title",
            "title_en",
            "slug",
            "short_description",
            "short_description_en",
            "icon",
            "is_active",
        )


class ServiceDetailSerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title", "short_description", "full_description")
    """Full detail serializer for a single service including nested plans."""

    plans = ServicePlanSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.title", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    class Meta:
        model = Service
        fields = (
            "id",
            "category",
            "category_name",
            "category_slug",
            "title",
            "title_en",
            "slug",
            "short_description",
            "short_description_en",
            "full_description",
            "full_description_en",
            "icon",
            "is_active",
            "plans",
        )


class ServiceCategorySerializer(LocalizedContentSerializerMixin, serializers.ModelSerializer):
    localized_fields = ("title", "description")
    """Serializer for categories along with their nested services."""

    services = ServiceListSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceCategory
        fields = ("id", "title", "title_en", "slug", "description", "description_en", "icon", "services")
