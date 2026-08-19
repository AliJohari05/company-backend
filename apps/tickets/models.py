from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.core.storage import private_media_storage


class TicketPriority(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    PENDING = "PENDING", _("Pending User Reply")
    ANSWERED = "ANSWERED", _("Answered")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")


class Ticket(TimeStampedModel):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_("User")
    )
    title = models.CharField(_("Title"), max_length=250)
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN
    )

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class TicketMessage(TimeStampedModel):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Ticket")
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='ticket_messages',
        verbose_name=_("User")
    )
    message = models.TextField(_("Message"))
    attachment = models.FileField(
        _("Attachment"),
        upload_to='tickets/attachments/',
        storage=private_media_storage,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Ticket Message")
        verbose_name_plural = _("Ticket Messages")
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.user.email} on {self.ticket.title}"
