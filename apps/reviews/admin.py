from django import forms
from django.contrib import admin

from .models import Review


class ReviewAdminForm(forms.ModelForm):
    admin_reply = forms.CharField(
        required=False,
        label="Reply as administrator",
        help_text="Enter a reply here; it will be published immediately.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    class Meta:
        model = Review
        fields = "__all__"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = ("id", "user", "target", "short_content", "rating", "reply_count", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "post", "service", "created_at")
    search_fields = ("content", "user__email")
    list_editable = ("is_approved",)
    actions = ("approve_reviews", "unapprove_reviews")
    readonly_fields = ("user", "post", "service", "parent", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("user", "post", "service", "parent", "content", "rating", "is_approved")}),
        ("Administrator reply", {"fields": ("admin_reply",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
            obj.is_approved = True
        super().save_model(request, obj, form, change)
        reply_text = form.cleaned_data.get("admin_reply")
        if change and reply_text:
            parent = obj.parent or obj
            Review.objects.create(
                user=request.user,
                post=obj.post,
                service=obj.service,
                parent=parent,
                content=reply_text,
                is_approved=True,
            )

    @admin.display(description="Target")
    def target(self, obj):
        return obj.post or obj.service

    @admin.display(description="Comment")
    def short_content(self, obj):
        content = obj.content
        return content if len(content) <= 80 else f"{content[:77]}..."

    @admin.display(description="Replies")
    def reply_count(self, obj):
        return obj.replies.count()

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Unapprove selected reviews")
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "post", "service", "parent").prefetch_related("replies")
