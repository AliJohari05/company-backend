from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.projects.models import ProjectRequest
from apps.services.models import Service


class Invoice(models.Model):
    """
    Financial invoices issued for users regarding project requests or service subscriptions.
    """
    class StatusChoices(models.TextChoices):
        UNPAID = 'UNPAID', _('Unpaid')
        PARTIALLY_PAID = 'PARTIALLY_PAID', _('Partially Paid')
        PAID = 'PAID', _('Paid')
        OVERDUE = 'OVERDUE', _('Overdue')
        CANCELED = 'CANCELED', _('Canceled')

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Invoice Number")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_("User")
    )
    project_request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_("Related Project Request")
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Related Service")
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Total Amount")
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.UNPAID,
        verbose_name=_("Status")
    )
    due_date = models.DateField(verbose_name=_("Due Date"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.user.email}"


class InvoiceItem(models.Model):
    """
    Individual itemized rows inside a specific invoice.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Invoice")
    )
    description = models.CharField(max_length=255, verbose_name=_("Description"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Quantity"))
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Unit Price")
    )

    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    @property
    def total_price(self):
        quantity = self.quantity or 0
        unit_price = self.unit_price or 0
        return quantity * unit_price

    def __str__(self):
        return f"{self.description} ({self.invoice.invoice_number})"


class Transaction(models.Model):
    """
    Offline/Manual payment receipts uploaded by the user for invoice verification.
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('Pending Verification')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_("Related Invoice")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Amount Paid")
    )
    reference_code = models.CharField(
        max_length=100,
        verbose_name=_("Reference Code / Tracking Number")
    )
    receipt_attachment = models.FileField(
        upload_to='receipts/',
        null=True,
        blank=True,
        verbose_name=_("Receipt Attachment")
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Verification Status")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        return f"Tx: {self.reference_code} - {self.amount}"


class Contract(models.Model):
    """
    Legal contracts and PDF documents binding the client and company.
    """
    class StatusChoices(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        EXPIRED = 'EXPIRED', _('Expired')
        TERMINATED = 'TERMINATED', _('Terminated')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name=_("User")
    )
    title = models.CharField(max_length=255, verbose_name=_("Contract Title"))
    file = models.FileField(upload_to='contracts/', verbose_name=_("Contract Document (PDF)"))
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name=_("Contract Status")
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Contract")
        verbose_name_plural = _("Contracts")

    def __str__(self):
        return f"{self.title} - {self.user.email}"
