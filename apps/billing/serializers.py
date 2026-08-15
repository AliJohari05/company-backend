from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Invoice, InvoiceItem, Transaction, Contract


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for individual itemized rows in an invoice."""

    total_price = serializers.ReadOnlyField()

    class Meta:
        model = InvoiceItem
        fields = (
            'id',
            'invoice',
            'description',
            'quantity',
            'unit_price',
            'total_price'
        )
        read_only_fields = ('id', 'total_price')


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for manual/offline payment receipt submissions."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            'id',
            'invoice',
            'user',
            'user_email',
            'amount',
            'reference_code',
            'receipt_attachment',
            'status',
            'status_display',
            'created_at'
        )
        read_only_fields = ('id', 'user', 'status', 'created_at')


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for reading invoice details including nested items."""

    items = InvoiceItemSerializer(
        many=True,
        read_only=True
    )
    transactions = TransactionSerializer(
        many=True,
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = Invoice
        fields = (
            'id',
            'invoice_number',
            'user',
            'user_email',
            'project_request',
            'service',
            'total_amount',
            'status',
            'status_display',
            'due_date',
            'created_at',
            'updated_at',
            'items',
            'transactions'
        )
        # user and invoice_number removed from read_only_fields so admins can populate them
        read_only_fields = (
            'id',
            'status',
            'created_at',
            'updated_at'
        )


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for legal customer contracts and documents."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )

    class Meta:
        model = Contract
        fields = (
            'id',
            'user',
            'user_email',
            'title',
            'file',
            'status',
            'status_display',
            'start_date',
            'end_date',
            'created_at'
        )
        # 'user' is writable so admin can assign the contract to a specific user
        read_only_fields = ('id', 'created_at')

    def validate_file(self, value):
        """Accept PDF contracts up to 10 MB."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('Only PDF contract files are allowed.')

        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                'Contract file size must not exceed 10 MB.'
            )

        return value
