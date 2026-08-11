from rest_framework import serializers
from .models import ServiceCategory, Service, ServicePlan


class ServicePlanSerializer(serializers.ModelSerializer):
    """Serializer for pricing plans within a specific service."""

    class Meta:
        model = ServicePlan
        fields = ('id', 'title', 'price', 'features', 'is_popular')


class ServiceListSerializer(serializers.ModelSerializer):
    """Compact serializer for service listings and category lists."""

    category_name = serializers.CharField(
        source='category.title',
        read_only=True
    )
    category_slug = serializers.CharField(
        source='category.slug',
        read_only=True
    )

    class Meta:
        model = Service
        fields = (
            'id',
            'category',
            'category_name',
            'category_slug',
            'title',
            'slug',
            'short_description',
            'icon',
            'is_active'
        )


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a single service including nested plans."""

    plans = ServicePlanSerializer(
        many=True,
        read_only=True
    )
    category_name = serializers.CharField(
        source='category.title',
        read_only=True
    )
    category_slug = serializers.CharField(
        source='category.slug',
        read_only=True
    )

    class Meta:
        model = Service
        fields = (
            'id',
            'category',
            'category_name',
            'category_slug',
            'title',
            'slug',
            'short_description',
            'full_description',
            'icon',
            'is_active',
            'plans'
        )


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for categories along with their nested services."""

    services = ServiceListSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = ServiceCategory
        fields = ('id', 'title', 'slug', 'description', 'icon', 'services')