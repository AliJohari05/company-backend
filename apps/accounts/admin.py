from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    
    # Columns displayed in the admin table
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'phone_number', 'first_name', 'last_name', 'company_name')
    ordering = ('-created_at',)

    # Layout of the user edit form in the admin panel
    fieldsets = (
        (_('Credentials'), {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'phone_number', 'company_name')}),
        (_('Permissions & Roles'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('created_at', 'updated_at','last_login')}),
    )

    # Layout of the new user creation form in the admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'phone_number', 'company_name', 'role', 'is_active', 'is_staff'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')