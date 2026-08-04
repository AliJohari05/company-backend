from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import ServiceCategory, Service
from .serializers import (
    ServiceCategorySerializer,
    ServiceListSerializer,
    ServiceDetailSerializer
)


class ServiceCategoryListView(generics.ListAPIView):
    """
Retrieve the list of all active categories along with their sub-services.
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]


class ServiceListView(generics.ListAPIView):
    """
Get a list of all active services
Ability to filter by `category_slug` via query parameter (e.g., `?category=web`)
    """
    serializer_class = ServiceListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True).select_related('category')
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset


class ServiceDetailView(generics.RetrieveAPIView):
    """
    Retrieve the details of a service along with its related pricing plans based on the slug
    """
    queryset = Service.objects.filter(is_active=True).prefetch_related('plans')
    serializer_class = ServiceDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'