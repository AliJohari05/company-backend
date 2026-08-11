from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import Ticket, TicketMessage
from .serializers import (
    TicketListSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketMessageSerializer,
)


class TicketListCreateView(generics.ListCreateAPIView):
    """
    List user tickets or create a new ticket with its initial message.
    Supports filtering, searching, and ordering.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields for frontend filtering
    filterset_fields = ['status', 'priority']
    
    # Search functionality across title and message contents
    search_fields = ['title', 'messages__content']
    
    # Ordering options
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        user = self.request.user
        # Staff members can view all tickets; regular users only view their own.
        if user.is_staff or user.is_superuser:
            return Ticket.objects.all().select_related('user')
        return Ticket.objects.filter(user=user).select_related('user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific ticket along with all nested messages.
    """
    serializer_class = TicketDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Ticket.objects.all().select_related('user').prefetch_related('messages__user')
        return Ticket.objects.filter(user=user).select_related('user').prefetch_related('messages__user')


class TicketMessageCreateView(generics.CreateAPIView):
    """
    Create a new reply inside an existing ticket.
    """
    serializer_class = TicketMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        user = self.request.user

        # Fetch ticket depending on user authority
        if user.is_staff or user.is_superuser:
            ticket = get_object_or_404(Ticket, id=ticket_id)
        else:
            ticket = get_object_or_404(Ticket, id=ticket_id, user=user)

        # Prevent sending messages to closed tickets
        if ticket.status == 'CLOSED':
            raise ValidationError("You cannot send a message to a closed ticket.")

        # Save message and update ticket status if replied by staff
        message = serializer.save(ticket=ticket, user=user)
        
        # Optionally update ticket timestamp or status when staff replies
        if user.is_staff:
            ticket.status = 'ANSWERED'
        else:
            ticket.status = 'PENDING'
        ticket.save(update_fields=['status', 'updated_at'])


class TicketCloseView(APIView):
    """
    Action endpoint to change a ticket's status to CLOSED or REOPENED.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.is_staff or user.is_superuser:
            ticket = get_object_or_404(Ticket, pk=pk)
        else:
            ticket = get_object_or_404(Ticket, pk=pk, user=user)

        # Toggle status or set to closed
        new_status = request.data.get('status', 'CLOSED')
        if new_status not in dict(Ticket.STATUS_CHOICES):  # Assuming STATUS_CHOICES exists on Model
            return Response({"error": "Invalid status choice."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = new_status
        ticket.save(update_fields=['status', 'updated_at'])

        return Response(
            {"detail": f"Ticket status changed to {ticket.status} successfully."},
            status=status.HTTP_200_OK
        )