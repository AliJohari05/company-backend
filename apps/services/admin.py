from django.contrib import admin

from .models import Service, ServiceCategory, ServicePlan


class ServicePlanInline(admin.TabularInline):
    model = ServicePlan
    extra = 1


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "slug", "is_active", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("title", "slug", "short_description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ServicePlanInline]


@admin.register(ServicePlan)
class ServicePlanAdmin(admin.ModelAdmin):
    list_display = ("title", "service", "price", "is_popular")
    list_filter = ("service", "is_popular")
    search_fields = ("title",)
