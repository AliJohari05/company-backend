from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import IntegrityError, models, transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.projects.models import ProjectRequest
from apps.services.models import Service

from .storage import private_billing_storage

MAX_INVOICE_AMOUNT = Decimal("9999999999.99")


class Invoice(models.Model):
    """
    Financial invoices issued for users regarding project requests or service subscriptions.
    """

    class StatusChoices(models.TextChoices):
        UNPAID = "UNPAID", _("Unpaid")
        PARTIALLY_PAID = "PARTIALLY_PAID", _("Partially Paid")
        PAID = "PAID", _("Paid")
        OVERDUE = "OVERDUE", _("Overdue")
        CANCELED = "CANCELED", _("Canceled")

    invoice_number = models.CharField(
        max_length=50, unique=True, blank=True, verbose_name=_("Invoice Number")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name=_("User"),
    )
    project_request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
        verbose_name=_("Related Project Request"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Related Service"),
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Total Amount"),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.UNPAID,
        verbose_name=_("Status"),
    )
    due_date = models.DateField(verbose_name=_("Due Date"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="billing_invoice_total_non_negative",
            ),
        ]

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.localdate().year
            with transaction.atomic():
                try:
                    with transaction.atomic():
                        sequence, _ = InvoiceSequence.objects.select_for_update().get_or_create(
                            year=year,
                            defaults={"last_value": 0},
                        )
                except IntegrityError:
                    # A concurrent first invoice for a year created the row.
                    sequence = InvoiceSequence.objects.select_for_update().get(year=year)

                prefix = f"INV-{year}-"
                existing_numbers = Invoice.objects.filter(
                    invoice_number__startswith=prefix
                ).exclude(pk=self.pk).values_list("invoice_number", flat=True)
                existing_last_values = (
                    int(number.removeprefix(prefix))
                    for number in existing_numbers
                    if number.removeprefix(prefix).isdigit()
                )
                sequence.last_value = max([sequence.last_value, *existing_last_values])
                sequence.last_value += 1
                sequence.save(update_fields=["last_value"])
                self.invoice_number = f"INV-{year}-{sequence.last_value:06d}"
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    def recalculate_total(self):
        """Persist the invoice total derived from all line items."""
        line_total = ExpressionWrapper(
            F("quantity") * F("unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        total = self.items.aggregate(total=Sum(line_total))["total"] or Decimal("0.00")
        Invoice.objects.filter(pk=self.pk).update(total_amount=total)
        self.total_amount = total
        return total

    def refresh_payment_status(self):
        """Derive payment status from approved transactions."""
        if self.status == self.StatusChoices.CANCELED:
            return self.status

        approved_amount = self.transactions.filter(
            status=Transaction.StatusChoices.APPROVED
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        if self.total_amount > Decimal("0.00") and approved_amount >= self.total_amount:
            new_status = self.StatusChoices.PAID
        elif self.due_date < timezone.localdate():
            new_status = self.StatusChoices.OVERDUE
        elif approved_amount > Decimal("0.00"):
            new_status = self.StatusChoices.PARTIALLY_PAID
        elif self.status == self.StatusChoices.OVERDUE:
            new_status = self.StatusChoices.OVERDUE
        else:
            new_status = self.StatusChoices.UNPAID

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status", "updated_at"])

        return new_status


class InvoiceItem(models.Model):
    """
    Individual itemized rows inside a specific invoice.
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Invoice"),
    )
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name=_("Quantity")
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Unit Price"),
    )

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="billing_invoice_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gt=0),
                name="billing_invoice_item_price_positive",
            ),
        ]

    @property
    def total_price(self):
        quantity = self.quantity or 0
        unit_price = self.unit_price or 0
        return quantity * unit_price

    def _validate_invoice_is_editable(self):
        if not self.invoice_id:
            return

        invoice = self.invoice
        if invoice.status in {
            Invoice.StatusChoices.PARTIALLY_PAID,
            Invoice.StatusChoices.PAID,
            Invoice.StatusChoices.CANCELED,
        }:
            raise ValidationError(
                _(
                    "Items of a paid, partially paid, or canceled invoice cannot be changed."
                )
            )

        if invoice.transactions.filter(
            status=Transaction.StatusChoices.APPROVED
        ).exists():
            raise ValidationError(
                _("Invoice items cannot be changed after a payment is approved.")
            )

    def _validate_projected_invoice_total(self):
        if not self.invoice_id or self.quantity is None or self.unit_price is None:
            return

        line_total = ExpressionWrapper(
            F("quantity") * F("unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        other_items_total = InvoiceItem.objects.filter(
            invoice_id=self.invoice_id
        ).exclude(pk=self.pk).aggregate(total=Sum(line_total))["total"] or Decimal(
            "0.00"
        )

        if other_items_total + self.total_price > MAX_INVOICE_AMOUNT:
            raise ValidationError(
                {
                    "unit_price": _(
                        "The sum of invoice items exceeds the maximum invoice amount."
                    )
                }
            )

    def clean(self):
        super().clean()
        self._validate_invoice_is_editable()
        self._validate_projected_invoice_total()

    def save(self, *args, **kwargs):
        self._validate_invoice_is_editable()
        self._validate_projected_invoice_total()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._validate_invoice_is_editable()
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.invoice.invoice_number})"


class Transaction(models.Model):
    """
    Offline/Manual payment receipts uploaded by the user for invoice verification.
    """

    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", _("Pending Verification")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Related Invoice"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Amount Paid"),
    )
    reference_code = models.CharField(
        max_length=100, verbose_name=_("Reference Code / Tracking Number")
    )
    receipt_attachment = models.FileField(
        upload_to="receipts/",
        storage=private_billing_storage,
        null=True,
        blank=True,
        verbose_name=_("Receipt Attachment"),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Verification Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="billing_transaction_amount_positive",
            ),
            models.UniqueConstraint(
                fields=("invoice", "reference_code"),
                name="billing_unique_reference_per_invoice",
            ),
        ]

    def clean(self):
        super().clean()

        if self.invoice_id and self.user_id:
            if self.user_id != self.invoice.user_id:
                raise ValidationError(
                    {"user": _("Transaction user must match the invoice user.")}
                )

        if self.invoice_id and self._state.adding:
            if self.invoice.status == Invoice.StatusChoices.CANCELED:
                raise ValidationError(
                    {
                        "invoice": _(
                            "A receipt cannot be submitted for a canceled invoice."
                        )
                    }
                )

            if self.invoice.status == Invoice.StatusChoices.PAID:
                raise ValidationError(
                    {"invoice": _("This invoice has already been paid in full.")}
                )

            if self.invoice.total_amount <= Decimal("0.00"):
                raise ValidationError(
                    {
                        "invoice": _(
                            "Add at least one invoice item before submitting a receipt."
                        )
                    }
                )

            committed_total = self.invoice.transactions.filter(
                status__in=(self.StatusChoices.PENDING, self.StatusChoices.APPROVED)
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            if (
                self.amount is not None
                and self.amount > self.invoice.total_amount - committed_total
            ):
                raise ValidationError(
                    {
                        "amount": _(
                            "Receipt amount exceeds the invoice remaining amount."
                        )
                    }
                )

        if (
            self.invoice_id
            and self.status == self.StatusChoices.APPROVED
            and self.amount is not None
        ):
            if self.invoice.status == Invoice.StatusChoices.CANCELED:
                raise ValidationError(
                    {
                        "status": _(
                            "A receipt cannot be approved for a canceled invoice."
                        )
                    }
                )

            approved_total = Transaction.objects.filter(
                invoice_id=self.invoice_id,
                status=self.StatusChoices.APPROVED,
            ).exclude(pk=self.pk).aggregate(total=Sum("amount"))["total"] or Decimal(
                "0.00"
            )
            if approved_total + self.amount > self.invoice.total_amount:
                raise ValidationError(
                    {
                        "status": _(
                            "Approving this receipt would exceed the invoice total."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Tx: {self.reference_code} - {self.amount}"


class Contract(models.Model):
    """
    Legal contracts and PDF documents binding the client and company.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        EXPIRED = "EXPIRED", _("Expired")
        TERMINATED = "TERMINATED", _("Terminated")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contracts",
        verbose_name=_("User"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Contract Title"))
    file = models.FileField(
        upload_to="contracts/",
        storage=private_billing_storage,
        verbose_name=_("Contract Document (PDF)"),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name=_("Contract Status"),
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Contract")
        verbose_name_plural = _("Contracts")

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class InvoiceSequence(models.Model):
    """Database-backed yearly sequence for human-readable invoice numbers."""

    year = models.PositiveIntegerField(unique=True)
    last_value = models.PositiveIntegerField(default=0)


def refresh_expired_statuses():
    """Synchronize date-based billing statuses for requests and scheduled jobs."""
    today = timezone.localdate()
    Invoice.objects.filter(
        due_date__lt=today,
        status__in=(Invoice.StatusChoices.UNPAID, Invoice.StatusChoices.PARTIALLY_PAID),
    ).update(status=Invoice.StatusChoices.OVERDUE)
    Contract.objects.filter(
        end_date__lt=today,
        status=Contract.StatusChoices.ACTIVE,
    ).update(status=Contract.StatusChoices.EXPIRED)


# Module-level alias required by drf-spectacular's enum resolver.
TransactionStatusChoices = Transaction.StatusChoices
