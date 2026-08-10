from django.contrib import admin
from .models import Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'user__email')
    inlines = [TicketMessageInline]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('ticket__title', 'user__email', 'message')