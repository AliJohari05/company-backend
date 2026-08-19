from rest_framework import serializers
from django.db import transaction
from django.urls import reverse
from drf_spectacular.utils import extend_schema_field

from .models import Ticket, TicketMessage, TicketStatus


class TicketMessageSerializer(serializers.ModelSerializer):
    """Serializer for displaying ticket messages in thread views."""

    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    is_staff = serializers.BooleanField(
        source='user.is_staff',
        read_only=True
    )
    attachment_download_url = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = (
            'id',
            'ticket',
            'user',
            'user_email',
            'is_staff',
            'message',
            'attachment_download_url',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'user',
            'ticket',
            'created_at',
            'updated_at'
        )

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_attachment_download_url(self, obj):
        if not obj.attachment:
            return None
        url = reverse(
            'tickets:ticket-attachment-download',
            kwargs={'pk': obj.pk},
        )
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class TicketMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer explicitly used for creating a new message reply."""

    attachment = serializers.FileField(
        required=False,
        allow_null=True,
        allow_empty_file=False
    )

    class Meta:
        model = TicketMessage
        fields = ('message', 'attachment')


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer for displaying summary lists of tickets."""

    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = (
            'id',
            'user',
            'user_email',
            'title',
            'priority',
            'priority_display',
            'status',
            'status_display',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'user',
            'status',
            'created_at',
            'updated_at'
        )


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for atomic creation of a ticket and its first message."""

    message = serializers.CharField(
        write_only=True,
        required=True
    )
    attachment = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True,
        allow_empty_file=False
    )

    class Meta:
        model = Ticket
        fields = (
            'id',
            'title',
            'priority',
            'message',
            'attachment',
            'created_at'
        )
        read_only_fields = ('created_at',)

    def create(self, validated_data):
        message_text = validated_data.pop('message')
        attachment_file = validated_data.pop('attachment', None)
        request = self.context.get('request')
        user = validated_data.pop('user', getattr(request, 'user', None))

        with transaction.atomic():
            ticket = Ticket.objects.create(
                user=user,
                **validated_data
            )

            TicketMessage.objects.create(
                ticket=ticket,
                user=user,
                message=message_text,
                attachment=attachment_file
            )

        return ticket


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying ticket details along with thread messages."""

    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    messages = TicketMessageSerializer(
        many=True,
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )

    class Meta:
        model = Ticket
        fields = (
            'id',
            'user',
            'user_email',
            'title',
            'priority',
            'priority_display',
            'status',
            'status_display',
            'created_at',
            'updated_at',
            'messages'
        )
        read_only_fields = (
            'user',
            'status',
            'created_at',
            'updated_at'
        )


class TicketStatusUpdateSerializer(serializers.Serializer):
    """Serializer for validating status update requests."""

    status = serializers.ChoiceField(choices=TicketStatus.choices)
