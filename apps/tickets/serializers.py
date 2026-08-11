from rest_framework import serializers
from django.db import transaction
from .models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual ticket messages, including sender details."""

    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    is_staff = serializers.BooleanField(
        source='user.is_staff',
        read_only=True
    )

    class Meta:
        model = TicketMessage
        fields = (
            'id',
            'ticket',
            'user',
            'user_email',
            'is_staff',
            'message',
            'attachment',
            'created_at',
            'updated_at'
        )
        read_only_fields = (
            'user',
            'ticket',
            'created_at',
            'updated_at'
        )


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
        allow_null=True
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

        # Atomic transaction to ensure both records are created safely
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