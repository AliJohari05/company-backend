from rest_framework import serializers
from .models import ProjectRequest, ProjectAttachment
from apps.services.serializers import ServiceListSerializer


# Serializer for project attachments (uploaded files)
class ProjectAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectAttachment

        # Fields exposed through the API
        fields = ('id', 'file', 'description', 'created_at')


# Serializer for project requests submitted by users
class ProjectRequestSerializer(serializers.ModelSerializer):

    # Include related attachments in the response
    # Read-only because attachments are managed separately
    attachments = ProjectAttachmentSerializer(
        many=True,
        read_only=True
    )

    # Human-readable status value
    # Example: "Pending" instead of "PENDING"
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = ProjectRequest

        # Fields exposed through the API
        fields = (
            'id',
            'user',
            'service',
            'title',
            'description',
            'estimated_budget',
            'status',
            'status_display',
            'attachments',
            'created_at',
            'updated_at'
        )

        # These fields are automatically managed by the system
        # and cannot be modified by clients
        read_only_fields = (
            'user',
            'status',
            'created_at',
            'updated_at'
        )

    def create(self, validated_data):
        """
        Automatically assign the authenticated user
        as the owner of the project request.
        """
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        return super().create(validated_data)