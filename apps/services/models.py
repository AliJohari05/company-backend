from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ServiceCategory(TimeStampedModel):
    title = models.CharField(_("Title"), max_length=250)
    title_en = models.CharField(_("Title (English)"), max_length=250, blank=True)
    slug = models.SlugField(_("Slug"), unique=True, allow_unicode=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    description_en = models.TextField(_("Description (English)"), blank=True)
    icon = models.CharField(
        _("Icon Class or URL"), max_length=100, blank=True, null=True
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
        ordering = ["title"]

    def __str__(self):
        return self.title


class Service(TimeStampedModel):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("Category"),
    )
    title = models.CharField(_("Title"), max_length=250)
    title_en = models.CharField(_("Title (English)"), max_length=250, blank=True)
    slug = models.SlugField(_("Slug"), unique=True, allow_unicode=True)
    short_description = models.TextField(_("Short Description"), blank=True, null=True)
    short_description_en = models.TextField(_("Short Description (English)"), blank=True)
    full_description = models.TextField(_("Full Description"), blank=True, null=True)
    full_description_en = models.TextField(_("Full Description (English)"), blank=True)
    icon = models.CharField(
        _("Icon Class or URL"), max_length=100, blank=True, null=True
    )
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.category.title})"


class ServicePlan(TimeStampedModel):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="plans",
        verbose_name=_("Service"),
    )
    title = models.CharField(_("Title"), max_length=250)
    title_en = models.CharField(_("Title (English)"), max_length=250, blank=True)
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    features = models.JSONField(_("Features"), default=list, blank=True)
    features_en = models.JSONField(_("Features (English)"), default=list, blank=True)
    is_popular = models.BooleanField(_("Is Popular"), default=False)

    class Meta:
        verbose_name = _("Service Plan")
        verbose_name_plural = _("Service Plans")
        ordering = ["price"]

    def __str__(self):
        return f"{self.service.title} - {self.title}"
