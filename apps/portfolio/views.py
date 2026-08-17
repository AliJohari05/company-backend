from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, PortfolioItem
from .serializers import (
    PortfolioCategorySerializer,
    PortfolioItemListSerializer,
    PortfolioItemDetailSerializer
)


class CategoryListView(generics.ListAPIView):
    """GET: List all portfolio categories."""
    queryset = Category.objects.order_by('id')
    serializer_class = PortfolioCategorySerializer
    permission_classes = [permissions.AllowAny]


class PortfolioListView(generics.ListAPIView):
    """
    GET: List all portfolios with filtering by category, technology, or featured status.
    """
    queryset = PortfolioItem.objects.all().select_related('category').prefetch_related('technologies')
    serializer_class = PortfolioItemListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'is_featured', 'technologies__name']
    search_fields = ['title', 'summary', 'description']
    ordering_fields = ['created_at', 'title']


class PortfolioDetailView(generics.RetrieveAPIView):
    """GET: Retrieve full details of a specific portfolio project using slug."""
    queryset = PortfolioItem.objects.all().select_related('category').prefetch_related('technologies', 'images')
    serializer_class = PortfolioItemDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
