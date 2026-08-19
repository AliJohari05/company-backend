from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    """Categories for portfolio projects (e.g., Web App, Mobile App, AI/ML)."""

    title = models.CharField(max_length=100, verbose_name=_("Category Title"))
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name=_("Slug"))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title


class Technology(models.Model):
    """Technologies used in projects (e.g., Python, Django, React, Docker)."""

    name = models.CharField(
        max_length=50, unique=True, verbose_name=_("Technology Name")
    )
    icon = models.FileField(
        upload_to="technologies/icons/",
        null=True,
        blank=True,
        verbose_name=_("Icon / SVG"),
    )

    class Meta:
        verbose_name = _("Technology")
        verbose_name_plural = _("Technologies")

    def __str__(self):
        return self.name


class PortfolioItem(models.Model):
    """Main model representing a portfolio project showcase."""

    title = models.CharField(max_length=200, verbose_name=_("Project Title"))
    slug = models.SlugField(unique=True, allow_unicode=True, verbose_name=_("Slug"))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="portfolios",
        verbose_name=_("Category"),
    )
    technologies = models.ManyToManyField(
        Technology, related_name="portfolios", verbose_name=_("Technologies Used")
    )
    cover_image = models.ImageField(
        upload_to="portfolio/covers/", verbose_name=_("Cover Image")
    )
    summary = models.TextField(max_length=500, verbose_name=_("Short Summary"))
    description = models.TextField(verbose_name=_("Full Project Description"))

    # External Links & GitHub Integration
    github_url = models.URLField(
        blank=True, null=True, verbose_name=_("GitHub Repository URL")
    )
    live_demo_url = models.URLField(
        blank=True, null=True, verbose_name=_("Live Demo URL")
    )
    client_name = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_("Client Name")
    )

    is_featured = models.BooleanField(
        default=False, verbose_name=_("Show on Home Page")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Portfolio Item")
        verbose_name_plural = _("Portfolio Items")

    def __str__(self):
        return self.title


class PortfolioImage(models.Model):
    """Gallery images for a specific portfolio project."""

    portfolio = models.ForeignKey(
        PortfolioItem,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Portfolio Project"),
    )
    image = models.ImageField(upload_to="portfolio/gallery/", verbose_name=_("Image"))
    caption = models.CharField(
        max_length=200, blank=True, null=True, verbose_name=_("Caption")
    )

    class Meta:
        verbose_name = _("Portfolio Image")
        verbose_name_plural = _("Portfolio Images")
