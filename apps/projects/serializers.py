from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.services.serializers import ServiceListSerializer

from .models import ProjectAttachment, ProjectRequest


class ProjectAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for project request file attachments."""

    file = serializers.FileField(write_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectAttachment
        fields = (
            "id",
            "file",
            "download_url",
            "description",
            "created_at",
        )
        read_only_fields = ("id", "download_url", "created_at")

    @extend_schema_field(serializers.URLField())
    def get_download_url(self, obj):
        url = reverse(
            "project_attachment_download",
            kwargs={"pk": obj.pk},
        )
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class ProjectRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user project requests,
    including read-only attached files and nested service details.
    """

    attachments = ProjectAttachmentSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    service_detail = ServiceListSerializer(source="service", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProjectRequest
        fields = (
            "id",
            "user",
            "user_email",
            "service",
            "service_detail",
            "title",
            "description",
            "estimated_budget",
            "status",
            "status_display",
            "attachments",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("user", "status", "created_at", "updated_at")

    def create(self, validated_data):
        """Automatically set the current authenticated user as request owner."""
        request = self.context.get("request")
        user = validated_data.pop("user", getattr(request, "user", None))

        if user and user.is_authenticated:
            validated_data["user"] = user

        return super().create(validated_data)
