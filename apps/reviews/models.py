from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Review(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    post = models.ForeignKey("blog.Post", on_delete=models.CASCADE, null=True, blank=True, related_name="reviews")
    service = models.ForeignKey("services.Service", on_delete=models.CASCADE, null=True, blank=True, related_name="reviews")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField(_("Content"), max_length=2000)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(condition=(Q(post__isnull=False) & Q(service__isnull=True)) | (Q(post__isnull=True) & Q(service__isnull=False)), name="review_one_target"),
            models.CheckConstraint(condition=Q(rating__isnull=True) | Q(rating__gte=1, rating__lte=5), name="review_rating_range"),
        ]

    def clean(self):
        if (self.post_id is None) == (self.service_id is None):
            raise ValidationError(_("A review must target exactly one post or service."))
        if self.parent_id and (self.parent.post_id != self.post_id or self.parent.service_id != self.service_id):
            raise ValidationError(_("Reply must belong to the same target."))
        if self.parent_id and self.parent.parent_id:
            raise ValidationError(_("Replies cannot be nested more than one level."))

    def __str__(self):
        return f"Review #{self.pk}"
