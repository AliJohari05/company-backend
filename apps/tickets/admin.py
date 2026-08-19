from django.contrib import admin

from .models import Ticket, TicketMessage, TicketStatus


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 1
    readonly_fields = ("created_at", "user")
    fields = ("user", "message", "attachment", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "priority",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "priority", "created_at")
    search_fields = ("title", "user__email", "user__first_name", "user__last_name")
    inlines = [TicketMessageInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TicketMessage) and not instance.pk:
                instance.user = request.user
                instance.save()

                ticket = instance.ticket
                if request.user.is_staff or request.user.is_superuser:
                    ticket.status = TicketStatus.ANSWERED
                else:
                    ticket.status = TicketStatus.PENDING
                ticket.save(update_fields=["status", "updated_at"])

        formset.save_m2m()


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("ticket__title", "user__email", "message")
    readonly_fields = ("user", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user

        super().save_model(request, obj, form, change)

        ticket = obj.ticket
        if request.user.is_staff or request.user.is_superuser:
            ticket.status = TicketStatus.ANSWERED
        else:
            ticket.status = TicketStatus.PENDING
        ticket.save(update_fields=["status", "updated_at"])
