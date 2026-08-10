from django.contrib import admin
from .models import ProjectRequest, ProjectAttachment


class ProjectAttachmentInline(admin.TabularInline):
    model = ProjectAttachment
    extra = 1


@admin.register(ProjectRequest)
class ProjectRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'service', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'user__email', 'service__title')
    inlines = [ProjectAttachmentInline]


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ('project_request', 'file', 'description', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('project_request__title', 'description')