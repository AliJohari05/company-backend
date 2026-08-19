from django.contrib import admin

from .models import Category, PortfolioImage, PortfolioItem, Technology


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title",)


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "client_name", "is_featured", "created_at")
    list_filter = ("category", "is_featured", "technologies")
    search_fields = ("title", "summary", "description", "client_name")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_featured",)
    filter_horizontal = ("technologies",)
    inlines = [PortfolioImageInline]
