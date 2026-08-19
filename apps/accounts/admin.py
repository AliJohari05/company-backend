from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating new users in Django Admin."""

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "company_name",
            "role",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure email is required during creation
        if "email" in self.fields:
            self.fields["email"].required = True


class CustomUserChangeForm(UserChangeForm):
    """Custom form for updating existing users in Django Admin."""

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom User model."""

    model = User
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    # List view display configuration
    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "role",
        "is_email_verified",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "role",
        "is_email_verified",
        "is_active",
        "is_staff",
        "created_at",
    )
    search_fields = ("email", "phone_number", "first_name", "last_name", "company_name")
    ordering = ("-created_at",)

    # User edit page layout
    fieldsets = (
        (_("Credentials"), {"fields": ("email", "password")}),
        (
            _("Personal Info"),
            {"fields": ("first_name", "last_name", "phone_number", "company_name")},
        ),
        (
            _("Permissions & Roles"),
            {
                "fields": (
                    "role",
                    "is_email_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "last_login",
                    "email_verified_at",
                )
            },
        ),
    )

    # New user creation page layout
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "company_name",
                    "role",
                    "is_email_verified",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "email_verified_at",
    )
