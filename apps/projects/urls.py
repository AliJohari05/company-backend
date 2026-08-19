from django.urls import path

from .views import (
    ProjectAttachmentCreateView,
    ProjectAttachmentDownloadView,
    ProjectRequestDetailView,
    ProjectRequestListCreateView,
)

urlpatterns = [
    path("", ProjectRequestListCreateView.as_view(), name="project_list_create"),
    path("<uuid:pk>/", ProjectRequestDetailView.as_view(), name="project_detail"),
    path(
        "<uuid:project_id>/attachments/",
        ProjectAttachmentCreateView.as_view(),
        name="project_attachment_create",
    ),
    path(
        "attachments/<uuid:pk>/download/",
        ProjectAttachmentDownloadView.as_view(),
        name="project_attachment_download",
    ),
]
