from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers
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

    def validate_receipt_attachment(self, value):
        if value is None:
            return value

        allowed_extensions = ('.pdf', '.jpg', '.jpeg', '.png')
        if not value.name.lower().endswith(allowed_extensions):
            raise serializers.ValidationError(
                'Receipt files must be PDF, JPG, JPEG, or PNG.'
            )

        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                'Receipt file size must not exceed 10 MB.'
            )

        return value


class TransactionStatusUpdateSerializer(serializers.ModelSerializer):
    """Staff-only serializer for verifying a payment receipt."""

    class Meta:
        model = Transaction
        fields = ('status',)

    def validate_status(self, value):
        instance = self.instance

        if value != Transaction.StatusChoices.APPROVED or instance is None:
            return value

        if instance.invoice.status == Invoice.StatusChoices.CANCELED:
            raise serializers.ValidationError(
                'A receipt cannot be approved for a canceled invoice.'
            )

        approved_total = (
            Transaction.objects.filter(
                invoice=instance.invoice,
                status=Transaction.StatusChoices.APPROVED,
            )
            .exclude(pk=instance.pk)
            .aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        if approved_total + instance.amount > instance.invoice.total_amount:
            raise serializers.ValidationError(
                'Approving this receipt would exceed the invoice total.'
            )

        return value


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
    approved_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()

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
            'approved_amount',
            'remaining_amount',
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

    def get_approved_amount(self, obj):
        approved_amount = getattr(obj, 'approved_amount', None)
        if approved_amount is not None:
            return approved_amount

        return (
            obj.transactions.filter(
                status=Transaction.StatusChoices.APPROVED
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

    def get_remaining_amount(self, obj):
        approved_amount = self.get_approved_amount(obj)
        return max(obj.total_amount - approved_amount, Decimal('0.00'))


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
