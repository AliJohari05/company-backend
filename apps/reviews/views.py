from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from .models import Review
from .permissions import ReviewPermission
from .serializers import AdminReplySerializer, ReviewSerializer


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


class ReviewReplyView(generics.GenericAPIView):
    serializer_class = AdminReplySerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Review.objects.select_related("post", "service", "parent")

    @extend_schema(
        request=AdminReplySerializer,
        responses={201: ReviewSerializer},
        description="Create and immediately approve an administrator reply.",
    )
    @transaction.atomic
    def post(self, request, pk):
        review = self.get_queryset().filter(pk=pk).first()
        if review is None:
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)
        parent = review.parent or review
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = Review.objects.create(
            user=request.user,
            post=parent.post,
            service=parent.service,
            parent=parent,
            content=serializer.validated_data["content"],
            is_approved=True,
        )
        return Response(ReviewSerializer(reply, context={"request": request}).data, status=status.HTTP_201_CREATED)
