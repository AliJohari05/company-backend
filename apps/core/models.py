from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        abstract = True


class SiteSetting(TimeStampedModel):
    """
    Singleton model to hold general site configurations, contact info, and 'About Us' content.
    """

    site_name = models.CharField(
        max_length=150, default="Agency Name", verbose_name=_("Site Name")
    )
    site_logo = models.ImageField(
        upload_to="core/logos/", null=True, blank=True, verbose_name=_("Site Logo")
    )
    about_us = models.TextField(blank=True, null=True, verbose_name=_("About Us Text"))

    email = models.EmailField(blank=True, null=True, verbose_name=_("Contact Email"))
    phone_number = models.CharField(
        max_length=30, blank=True, null=True, verbose_name=_("Phone Number")
    )
    address = models.TextField(
        blank=True, null=True, verbose_name=_("Physical Address")
    )
    working_hours = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_("Working Hours")
    )

    class Meta:
        verbose_name = _("Site Setting")
        verbose_name_plural = _("Site Settings")

    def save(self, *args, **kwargs):
        if not self.pk and SiteSetting.objects.exists():
            self.pk = SiteSetting.objects.first().pk
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.site_name)


class SocialLink(TimeStampedModel):
    """
    Social media profiles (e.g., GitHub, LinkedIn, Telegram, Instagram, Twitter).
    """

    title = models.CharField(max_length=50, verbose_name=_("Platform Name"))
    url = models.URLField(verbose_name=_("Profile URL"))
    icon = models.FileField(
        upload_to="core/social_icons/",
        null=True,
        blank=True,
        verbose_name=_("Icon / SVG"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        ordering = ["id"]
        verbose_name = _("Social Link")
        verbose_name_plural = _("Social Links")

    def __str__(self):
        return f"{self.title} - {self.url}"


class FAQ(TimeStampedModel):
    """
    Frequently Asked Questions displayed on the website.
    """

    question = models.CharField(max_length=255, verbose_name=_("Question"))
    answer = models.TextField(verbose_name=_("Answer"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")

    def __str__(self):
        return self.question
