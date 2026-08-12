from rest_framework import generics, permissions, filters
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Tag, Post
from .serializers import (
    CategorySerializer,
    TagSerializer,
    PostListSerializer,
    PostDetailSerializer,
)
from apps.core.pagination import BlogPostsPagination

class CategoryListCreateView(generics.ListCreateAPIView):
    """
   GET: List of categories (public)
    POST: Create a new category (logged-in user/admin only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / DELETE category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]


class TagListCreateView(generics.ListCreateAPIView):
    """
    GET: List of tags (public)
    POST: Create a new tag (admin only)
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class TagDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET / PUT / DELETE tag (admin only)
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAdminUser]

class PostListCreateView(generics.ListCreateAPIView):
    """
    GET: List of published posts (public)
    POST: Create a new post (by author/admin)
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'tags__slug', 'is_published']
    search_fields = ['title', 'content', 'meta_description']
    ordering_fields = ['published_at', 'views_count', 'created_at']
    ordering = ['-published_at']
    pagination_class = BlogPostsPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostDetailSerializer
        return PostListSerializer

    def get_queryset(self):
        #Regular users only see published posts, but the admin/author sees everything.
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Post.objects.all().select_related('author', 'category').prefetch_related('tags')
        return Post.objects.filter(is_published=True).select_related('author', 'category').prefetch_related('tags')

    def perform_create(self, serializer):
        #Automatically setting the article author based on the logged-in user
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: View post (increase view count by 1)
    PUT / PATCH / DELETE: Edit or delete post (author or admin only)
    """
    serializer_class = PostDetailSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Post.objects.all().select_related('author', 'category').prefetch_related('tags')

    def get_object(self):
        instance = super().get_object()
        # The visit count should only be incremented upon receiving a GET request.
        if self.request.method == 'GET':
            Post.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
            instance.refresh_from_db()
        return instance