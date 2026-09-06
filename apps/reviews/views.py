from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from .models import Review
from .permissions import ReviewPermission
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["post", "service"]
    ordering = ["created_at"]

    def get_queryset(self):
        qs = Review.objects.select_related("user", "post", "service").prefetch_related("replies")
        if self.request.user.is_staff:
            return qs
        return qs.filter(is_approved=True, parent__isnull=True)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermission]

    def get_queryset(self):
        qs = Review.objects.select_related("user", "post", "service").prefetch_related("replies")
        if self.request.user.is_staff:
            return qs
        return qs.filter(is_approved=True)

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            serializer.save(is_approved=False)
        else:
            serializer.save()
