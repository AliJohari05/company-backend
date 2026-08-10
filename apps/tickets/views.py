from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser

from .models import Ticket, TicketMessage
from .serializers import (
    TicketListSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketMessageSerializer,
)


class TicketListCreateView(generics.ListCreateAPIView):
    """
    List the user's tickets and create a new ticket
    together with its first message.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCreateSerializer

        return TicketListSerializer

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)


class TicketDetailView(generics.RetrieveAPIView):
    """
    Retrieve the details of a ticket along with all
    messages sent within that ticket.
    """
    serializer_class = TicketDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(
            user=self.request.user
        ).prefetch_related('messages')


class TicketMessageCreateView(generics.CreateAPIView):
    """
    Create a new message within an existing ticket.
    """
    serializer_class = TicketMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')

        ticket = generics.get_object_or_404(
            Ticket,
            id=ticket_id,
            user=self.request.user
        )

        # Prevent users from replying to a closed ticket
        if ticket.status == 'CLOSED':
            raise serializer.ValidationError(
                "You cannot send a message to a closed ticket."
            )

        serializer.save(
            ticket=ticket,
            user=self.request.user
        )
