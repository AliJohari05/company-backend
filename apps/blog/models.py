from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, allow_unicode=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    pagination_class = None

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, allow_unicode=True)
    pagination_class = None

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(TimeStampedModel):
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("Author"),
    )
    title = models.CharField(_("Title"), max_length=250)
    slug = models.SlugField(_("Slug"), max_length=250, unique=True, allow_unicode=True)
    content = models.TextField(_("Content"))
    featured_image = models.ImageField(
        _("Featured Image"), upload_to="blog/featured_images/", blank=True, null=True
    )
    meta_description = models.CharField(
        _("Meta Description"), max_length=160, blank=True, null=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name=_("Category"),
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        Tag, related_name="posts", verbose_name=_("Tags"), blank=True
    )
    is_published = models.BooleanField(_("Is Published"), default=False)
    published_at = models.DateTimeField(_("Published At"), blank=True, null=True)
    views_count = models.PositiveIntegerField(_("Views Count"), default=0)

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def excerpt(self):
        """Generating a summary of the article text for display in lists."""
        if not self.content:
            return ""
        clean_text = self.content.strip()
        if len(clean_text) <= 180:
            return clean_text
        return clean_text[:180].rsplit(" ", 1)[0] + "..."
