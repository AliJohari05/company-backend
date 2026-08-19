from pathlib import PurePosixPath

from django.db import connection
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, generics, permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .files import (
    FileDownloadContentNegotiation,
    private_file_response,
)
from .models import FAQ, SiteSetting, SocialLink
from .serializers import FAQSerializer, SiteSettingSerializer, SocialLinkSerializer


def health_check(request):
    """Readiness probe that verifies Django and its primary database."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {"status": "unhealthy", "database": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok", "database": "ok"})


class PrivateMediaFileDownloadView(APIView):
    """Authenticated storage URL used by Django Admin file widgets."""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    content_negotiation_class = FileDownloadContentNegotiation

    @extend_schema(exclude=True)
    def get(self, request, file_path):
        from apps.projects.models import ProjectAttachment
        from apps.tickets.models import TicketMessage

        path = PurePosixPath(file_path)
        if path.is_absolute() or ".." in path.parts:
            raise exceptions.NotFound()

        normalized_path = path.as_posix()
        if normalized_path.startswith("project_attachments/"):
            queryset = ProjectAttachment.objects.filter(file=normalized_path)
            owner_filter = {"project_request__user": request.user}
            field_name = "file"
        elif normalized_path.startswith("tickets/attachments/"):
            queryset = TicketMessage.objects.filter(attachment=normalized_path)
            owner_filter = {"ticket__user": request.user}
            field_name = "attachment"
        else:
            raise exceptions.NotFound()

        if not (request.user.is_staff or request.user.is_superuser):
            queryset = queryset.filter(**owner_filter)

        instance = queryset.first()
        if instance is None:
            raise exceptions.NotFound()
        return private_file_response(getattr(instance, field_name))


class SiteSettingDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve site general settings, contact info, and social links in a single request.
    """

    serializer_class = SiteSettingSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        setting, _ = SiteSetting.objects.get_or_create(id=1)
        return setting


class SocialLinkListView(generics.ListAPIView):
    """
    GET: List all active social media links.
    """

    queryset = SocialLink.objects.filter(is_active=True)
    serializer_class = SocialLinkSerializer
    permission_classes = [permissions.AllowAny]


class FAQListView(generics.ListAPIView):
    """
    GET: List all active frequently asked questions.
    """

    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
