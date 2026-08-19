from django.urls import path

from .views import (
    TicketAttachmentDownloadView,
    TicketDetailView,
    TicketListCreateView,
    TicketMessageCreateView,
    TicketStatusUpdateView,
)

app_name = "tickets"

urlpatterns = [
    path("", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("<int:pk>/", TicketDetailView.as_view(), name="ticket-detail"),
    path(
        "<int:ticket_id>/messages/",
        TicketMessageCreateView.as_view(),
        name="ticket-message-create",
    ),
    path(
        "<int:pk>/status/",
        TicketStatusUpdateView.as_view(),
        name="ticket-status-update",
    ),
    path(
        "messages/<int:pk>/attachment/",
        TicketAttachmentDownloadView.as_view(),
        name="ticket-attachment-download",
    ),
]
