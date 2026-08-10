from rest_framework import serializers
from .models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = TicketMessage
        fields = (
            'id',
            'ticket',
            'user',
            'user_email',
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

    def create(self, validated_data):
        # Automatically set the message sender to the currently authenticated user
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer for displaying the user's tickets without loading all messages."""

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
    """Serializer for creating a new ticket together with its first message."""

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

        # Create the main ticket
        ticket = Ticket.objects.create(
            user=request.user,
            **validated_data
        )

        # Create the first message and associate it with the ticket
        TicketMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=message_text,
            attachment=attachment_file
        )

        return ticket


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer for displaying a ticket with all of its messages."""

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
