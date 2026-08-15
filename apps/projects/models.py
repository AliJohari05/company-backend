import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class ProjectStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    COMPLETED = "COMPLETED", _("Completed")
    REJECTED = "REJECTED", _("Rejected")


class ProjectRequest(TimeStampedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='project_requests',
        null=True,
        blank=True,
        verbose_name=_("User")
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        related_name='project_requests',
        null=True,
        blank=True,
        verbose_name=_("Service")
    )
    title = models.CharField(_("Title"), max_length=250)
    description = models.TextField(_("Description"))
    estimated_budget = models.DecimalField(
        _("Estimated Budget"),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PENDING
    )

    class Meta:
        verbose_name = _("Project Request")
        verbose_name_plural = _("Project Requests")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ProjectAttachment(TimeStampedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    project_request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_("Project Request")
    )
    file = models.FileField(
        _("File"),
        upload_to='project_attachments/%Y/%m/'
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Project Attachment")
        verbose_name_plural = _("Project Attachments")
        ordering = ['-created_at']

    def __str__(self):
        return f"Attachment for {self.project_request.title}"