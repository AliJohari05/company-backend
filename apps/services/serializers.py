from rest_framework import serializers
from .models import ServiceCategory, Service, ServicePlan


class ServicePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePlan
        fields = ('id', 'title', 'price', 'features', 'is_popular')


class ServiceListSerializer(serializers.ModelSerializer):
    # For the list of services (without needing all the details or plans)  
    class Meta:
        model = Service
        fields = ('id', 'title', 'slug', 'short_description', 'icon', 'is_active')


class ServiceDetailSerializer(serializers.ModelSerializer):
    # For a service detail page featuring pricing plans
    plans = ServicePlanSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.title', read_only=True)

    class Meta:
        model = Service
        fields = (
            'id', 'category', 'category_name', 'title', 'slug',
            'short_description', 'full_description', 'icon',
            'is_active', 'plans'
        )


class ServiceCategorySerializer(serializers.ModelSerializer):
    services = ServiceListSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceCategory
        fields = ('id', 'title', 'slug', 'description', 'icon', 'services')