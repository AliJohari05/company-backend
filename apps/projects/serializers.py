from rest_framework import serializers
from .models import ProjectRequest, ProjectAttachment
from apps.services.serializers import ServiceListSerializer


class ProjectAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for project request file attachments."""

    class Meta:
        model = ProjectAttachment
        fields = ('id', 'file', 'description', 'created_at')


class ProjectRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user project requests,
    including read-only attached files and nested service details.
    """

    attachments = ProjectAttachmentSerializer(
        many=True,
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    service_detail = ServiceListSerializer(
        source='service',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = ProjectRequest
        fields = (
            'id',
            'user',
            'user_email',
            'service',
            'service_detail',
            'title',
            'description',
            'estimated_budget',
            'status',
            'status_display',
            'attachments',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'user',
            'status',
            'created_at',
            'updated_at'
        )

    def create(self, validated_data):
        """Automatically set the current authenticated user as request owner."""
        request = self.context.get('request')
        user = validated_data.pop('user', getattr(request, 'user', None))

        if user and user.is_authenticated:
            validated_data['user'] = user

        return super().create(validated_data)