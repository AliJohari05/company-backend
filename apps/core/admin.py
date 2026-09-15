from django.contrib import admin

from .models import ContactMessage, FAQ, SiteSetting, SocialLink


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("site_name", "email", "phone_number", "updated_at")

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "url")
    list_editable = ("is_active",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("question", "answer")
    list_editable = ("order", "is_active")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    list_editable = ("is_read",)
    readonly_fields = ("name", "email", "phone_number", "subject", "message", "created_at", "updated_at")
