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
    """Serializer for invoices including nested items and transaction history."""

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
        read_only_fields = (
            'id',
            'invoice_number',
            'user',
            'status',
            'created_at',
            'updated_at'
        )


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for legal customer contracts and documents."""

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
        read_only_fields = ('id', 'user', 'created_at')