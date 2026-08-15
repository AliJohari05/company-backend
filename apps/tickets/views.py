from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter

from .models import Ticket, TicketStatus
from .serializers import (
    TicketListSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketMessageSerializer,
    TicketMessageCreateSerializer,
    TicketStatusUpdateSerializer,
)


class TicketListCreateView(generics.ListCreateAPIView):
    """
    List user tickets or create a new ticket with its initial message.
    Supports filtering, searching, and ordering.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['status', 'priority']
    search_fields = ['title', 'messages__message']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TicketCreateSerializer
        return TicketListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Ticket.objects.all().select_related('user')
        return Ticket.objects.filter(user=user).select_related('user')

    @extend_schema(
        operation_id="create_ticket",
        request={
            'multipart/form-data': TicketCreateSerializer
        },
        responses={201: TicketDetailSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

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
    serializer_class = TicketMessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    @extend_schema(
        operation_id="create_ticket_message",
        request={
            'multipart/form-data': TicketMessageCreateSerializer
        },
        responses={201: TicketMessageSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        user = self.request.user

        if user.is_staff or user.is_superuser:
            ticket = get_object_or_404(Ticket, id=ticket_id)
        else:
            ticket = get_object_or_404(Ticket, id=ticket_id, user=user)

        if ticket.status == TicketStatus.CLOSED:
            raise ValidationError("You cannot send a message to a closed ticket.")

        serializer.save(ticket=ticket, user=user)

        if user.is_staff or user.is_superuser:
            ticket.status = TicketStatus.ANSWERED
        else:
            ticket.status = TicketStatus.PENDING

        ticket.save(update_fields=['status', 'updated_at'])


class TicketStatusUpdateView(APIView):
    """
    Action endpoint to change a ticket's status manually.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=TicketStatusUpdateSerializer,
        responses={200: dict}
    )
    def post(self, request, pk):
        user = request.user
        if user.is_staff or user.is_superuser:
            ticket = get_object_or_404(Ticket, pk=pk)
        else:
            ticket = get_object_or_404(Ticket, pk=pk, user=user)

        serializer = TicketStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        ticket.status = new_status
        ticket.save(update_fields=['status', 'updated_at'])

        return Response(
            {"detail": f"Ticket status changed to {ticket.status} successfully."},
            status=status.HTTP_200_OK
        )