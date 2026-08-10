from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ProjectRequest, ProjectAttachment
from .serializers import ProjectRequestSerializer, ProjectAttachmentSerializer


class ProjectRequestListCreateView(generics.ListCreateAPIView):
    """
    Create a new project request and retrieve the user's project requests.
    """

    serializer_class = ProjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProjectRequest.objects.filter(user=self.request.user).prefetch_related('attachments')


class ProjectRequestDetailView(generics.RetrieveAPIView):
    """
    Retrieve the details of a project request owned by the authenticated user.
    """

    serializer_class = ProjectRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only project requests belonging to the authenticated user.
        # This prevents users from accessing other users' project requests.
        return ProjectRequest.objects.filter(
            user=self.request.user
        ).prefetch_related('attachments')


class ProjectAttachmentCreateView(generics.CreateAPIView):
    """
    Upload an attachment for a project request.
    """

    serializer_class = ProjectAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Enable multipart/form-data and form-data requests for file uploads.
    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    def perform_create(self, serializer):
        # Get the project request ID from the URL.
        project_id = self.kwargs.get('project_id')

        # Make sure the project exists and belongs to the authenticated user.
        project = generics.get_object_or_404(
            ProjectRequest,
            id=project_id,
            user=self.request.user
        )

        # Save the attachment and associate it with the project request.
        serializer.save(project_request=project)