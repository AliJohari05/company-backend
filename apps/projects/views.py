from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.core.files import (
    FileDownloadContentNegotiation,
    private_file_response,
)

from .models import ProjectRequest, ProjectAttachment
from .serializers import ProjectRequestSerializer, ProjectAttachmentSerializer


class ProjectRequestListCreateView(generics.ListCreateAPIView):
    """
    Create a new project request and retrieve user project requests.
    Supports filtering by status, searching by title, and ordering.
    """
    serializer_class = ProjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter and search fields
    filterset_fields = ['status', 'estimated_budget']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProjectRequest.objects.none()

        user = self.request.user
        # Staff members can inspect all requests; standard users access their own only.
        if user.is_staff or user.is_superuser:
            return ProjectRequest.objects.all().select_related('user').prefetch_related('attachments')
        return ProjectRequest.objects.filter(user=user).prefetch_related('attachments')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProjectRequestDetailView(generics.RetrieveAPIView):
    """
    Retrieve the details of a project request owned by the user or staff.
    """
    serializer_class = ProjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProjectRequest.objects.none()

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return ProjectRequest.objects.all().select_related('user').prefetch_related('attachments')
        return ProjectRequest.objects.filter(user=user).prefetch_related('attachments')


class ProjectAttachmentCreateView(generics.CreateAPIView):
    """
    Upload an attachment for an existing project request.
    """
    serializer_class = ProjectAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        user = self.request.user

        if user.is_staff or user.is_superuser:
            project = get_object_or_404(ProjectRequest, id=project_id)
        else:
            project = get_object_or_404(ProjectRequest, id=project_id, user=user)

        serializer.save(project_request=project)


class ProjectAttachmentDownloadView(APIView):
    """Download an attachment owned by the current user, or any as staff."""

    permission_classes = [permissions.IsAuthenticated]
    content_negotiation_class = FileDownloadContentNegotiation

    @extend_schema(
        responses={(200, 'application/octet-stream'): OpenApiTypes.BINARY}
    )
    def get(self, request, pk):
        queryset = ProjectAttachment.objects.select_related(
            'project_request'
        )
        if not (request.user.is_staff or request.user.is_superuser):
            queryset = queryset.filter(project_request__user=request.user)

        attachment = get_object_or_404(queryset, pk=pk)
        return private_file_response(attachment.file)
