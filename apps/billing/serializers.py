from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    MAX_INVOICE_AMOUNT,
    Contract,
    Invoice,
    InvoiceItem,
    Transaction,
)


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for individual itemized rows in an invoice."""

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = InvoiceItem
        fields = (
            "id",
            "invoice",
            "description",
            "quantity",
            "unit_price",
            "total_price",
        )
        read_only_fields = ("id", "total_price")

    def validate(self, attrs):
        invoice = attrs.get(
            "invoice",
            self.instance.invoice if self.instance else None,
        )

        if (
            self.instance
            and "invoice" in attrs
            and attrs["invoice"].pk != self.instance.invoice_id
        ):
            raise serializers.ValidationError(
                {
                    "invoice": "Moving an existing item to another invoice is not allowed."
                }
            )

        if invoice is not None:
            if invoice.status in {
                Invoice.StatusChoices.PARTIALLY_PAID,
                Invoice.StatusChoices.PAID,
                Invoice.StatusChoices.CANCELED,
            }:
                raise serializers.ValidationError(
                    {
                        "invoice": (
                            "Items of a paid, partially paid, or canceled invoice "
                            "cannot be changed."
                        )
                    }
                )

            if invoice.transactions.filter(
                status=Transaction.StatusChoices.APPROVED
            ).exists():
                raise serializers.ValidationError(
                    {
                        "invoice": (
                            "Invoice items cannot be changed after a payment is approved."
                        )
                    }
                )

            quantity = attrs.get(
                "quantity",
                self.instance.quantity if self.instance else 1,
            )
            unit_price = attrs.get(
                "unit_price",
                self.instance.unit_price if self.instance else None,
            )
            if unit_price is not None:
                line_total = ExpressionWrapper(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2,
                    ),
                )
                other_items_total = invoice.items.exclude(
                    pk=self.instance.pk if self.instance else None
                ).aggregate(total=Sum(line_total))["total"] or Decimal("0.00")
                if other_items_total + (quantity * unit_price) > MAX_INVOICE_AMOUNT:
                    raise serializers.ValidationError(
                        {
                            "unit_price": (
                                "The sum of invoice items exceeds the maximum "
                                "invoice amount."
                            )
                        }
                    )

        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for manual/offline payment receipt submissions."""

    receipt_attachment = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    receipt_download_url = serializers.SerializerMethodField()
    invoice_number = serializers.CharField(
        source="invoice.invoice_number",
        read_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "invoice",
            "invoice_number",
            "user",
            "user_email",
            "amount",
            "reference_code",
            "receipt_attachment",
            "receipt_download_url",
            "status",
            "status_display",
            "created_at",
        )
        read_only_fields = ("id", "user", "status", "created_at")

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_receipt_download_url(self, obj):
        if not obj.receipt_attachment:
            return None

        url = reverse(
            "billing:transaction-receipt-download",
            kwargs={"pk": obj.pk},
        )
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Transaction amount must be greater than zero."
            )
        return value

    def validate_receipt_attachment(self, value):
        if value is None:
            return value

        allowed_extensions = (".pdf", ".jpg", ".jpeg", ".png")
        if not value.name.lower().endswith(allowed_extensions):
            raise serializers.ValidationError(
                "Receipt files must be PDF, JPG, JPEG, or PNG."
            )

        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Receipt file size must not exceed 10 MB."
            )

        return value

    def validate(self, attrs):
        invoice = attrs.get(
            "invoice",
            self.instance.invoice if self.instance else None,
        )
        reference_code = attrs.get(
            "reference_code",
            self.instance.reference_code if self.instance else None,
        )
        amount = attrs.get(
            "amount",
            self.instance.amount if self.instance else None,
        )

        if invoice is None:
            return attrs

        if invoice.status == Invoice.StatusChoices.CANCELED:
            raise serializers.ValidationError(
                {"invoice": "A receipt cannot be submitted for a canceled invoice."}
            )

        if invoice.status == Invoice.StatusChoices.PAID:
            raise serializers.ValidationError(
                {"invoice": "This invoice has already been paid in full."}
            )

        if invoice.total_amount <= Decimal("0.00"):
            raise serializers.ValidationError(
                {
                    "invoice": "Add at least one invoice item before submitting a receipt."
                }
            )

        approved_total = invoice.transactions.filter(
            status=Transaction.StatusChoices.APPROVED
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        remaining_amount = max(
            invoice.total_amount - approved_total,
            Decimal("0.00"),
        )
        if amount is not None and amount > remaining_amount:
            raise serializers.ValidationError(
                {"amount": "Transaction amount exceeds the invoice remaining amount."}
            )

        duplicate_reference = Transaction.objects.filter(
            invoice=invoice,
            reference_code=reference_code,
        )
        if self.instance:
            duplicate_reference = duplicate_reference.exclude(pk=self.instance.pk)
        if reference_code and duplicate_reference.exists():
            raise serializers.ValidationError(
                {
                    "reference_code": (
                        "This reference code has already been used for this invoice."
                    )
                }
            )

        return attrs


class TransactionStatusUpdateSerializer(serializers.ModelSerializer):
    """Staff-only serializer for verifying a payment receipt."""

    class Meta:
        model = Transaction
        fields = ("status",)

    def validate_status(self, value):
        instance = self.instance

        if value != Transaction.StatusChoices.APPROVED or instance is None:
            return value

        if instance.invoice.status == Invoice.StatusChoices.CANCELED:
            raise serializers.ValidationError(
                "A receipt cannot be approved for a canceled invoice."
            )

        approved_total = Transaction.objects.filter(
            invoice=instance.invoice,
            status=Transaction.StatusChoices.APPROVED,
        ).exclude(pk=instance.pk).aggregate(total=Sum("amount"))["total"] or Decimal(
            "0.00"
        )

        if approved_total + instance.amount > instance.invoice.total_amount:
            raise serializers.ValidationError(
                "Approving this receipt would exceed the invoice total."
            )

        return value


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for reading invoice details including nested items."""

    items = InvoiceItemSerializer(many=True, read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    approved_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "user",
            "user_email",
            "project_request",
            "service",
            "total_amount",
            "approved_amount",
            "remaining_amount",
            "status",
            "status_display",
            "due_date",
            "created_at",
            "updated_at",
            "items",
            "transactions",
        )
        # user and invoice_number removed from read_only_fields so admins can populate them
        read_only_fields = ("id", "status", "total_amount", "created_at", "updated_at")

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_approved_amount(self, obj):
        approved_amount = getattr(obj, "approved_amount", None)
        if approved_amount is not None:
            return f"{approved_amount:.2f}"

        approved_amount = obj.transactions.filter(
            status=Transaction.StatusChoices.APPROVED
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        return f"{approved_amount:.2f}"

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_remaining_amount(self, obj):
        approved_amount = getattr(obj, "approved_amount", None)
        if approved_amount is None:
            approved_amount = obj.transactions.filter(
                status=Transaction.StatusChoices.APPROVED
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        remaining_amount = max(
            obj.total_amount - approved_amount,
            Decimal("0.00"),
        )
        return f"{remaining_amount:.2f}"


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for legal customer contracts and documents."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    file = serializers.FileField(write_only=True)
    download_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Contract
        fields = (
            "id",
            "user",
            "user_email",
            "title",
            "file",
            "download_url",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "created_at",
        )
        # 'user' is writable so admin can assign the contract to a specific user
        read_only_fields = ("id", "created_at")

    @extend_schema_field(serializers.URLField())
    def get_download_url(self, obj):
        url = reverse(
            "billing:contract-download",
            kwargs={"pk": obj.pk},
        )
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def validate_file(self, value):
        """Accept PDF contracts up to 10 MB."""
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Only PDF contract files are allowed.")

        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                "Contract file size must not exceed 10 MB."
            )

        return value
