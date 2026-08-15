from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ServiceCategory, Service
from .serializers import (
    ServiceCategorySerializer,
    ServiceListSerializer,
    ServiceDetailSerializer
)


class ServiceCategoryListView(generics.ListAPIView):
    """
    Retrieve all active service categories along with their sub-services.
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]


class ServiceListView(generics.ListAPIView):
    """
    Get a list of all active services.
    Supports filtering by `category__slug` (e.g. `?category__slug=web`),
    searching by service title, and ordering.
    """
    queryset = Service.objects.filter(is_active=True).select_related('category')
    serializer_class = ServiceListSerializer
    permission_classes = [permissions.AllowAny]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Allows filtering via URL params like ?category__slug=web or ?category=1
    filterset_fields = ['category__slug', 'category']
    search_fields = ['title', 'short_description', 'full_description']
    ordering_fields = ['created_at', 'title']
    ordering = ['created_at']


class ServiceDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific service along with its pricing plans using its slug.
    """
    queryset = Service.objects.filter(is_active=True).prefetch_related('plans')
    serializer_class = ServiceDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'