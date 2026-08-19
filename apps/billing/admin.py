from django.contrib import admin

from .models import Contract, Invoice, InvoiceItem, Transaction


class InvoiceItemInline(admin.TabularInline):
    """
    Allows editing itemized rows directly inside the Invoice detail view.
    """

    model = InvoiceItem
    extra = 1
    fields = ("description", "quantity", "unit_price", "total_price")
    readonly_fields = ("total_price",)


class TransactionInline(admin.TabularInline):
    """
    Displays related payment receipts inside the Invoice detail view.
    """

    model = Transaction
    extra = 0
    fields = ("user", "amount", "reference_code", "status", "created_at")
    readonly_fields = ("user", "amount", "reference_code", "created_at")

    def has_add_permission(self, request, obj):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "user",
        "total_amount",
        "status",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "due_date", "created_at")
    search_fields = (
        "invoice_number",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = ("total_amount", "created_at", "updated_at")
    inlines = [InvoiceItemInline, TransactionInline]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "quantity", "unit_price", "total_price")
    search_fields = ("description", "invoice__invoice_number")
    readonly_fields = ("total_price",)

    def delete_queryset(self, request, queryset):
        for item in queryset.select_related("invoice"):
            item.delete()


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "invoice",
        "user",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("reference_code", "invoice__invoice_number", "user__email")
    readonly_fields = ("created_at",)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.readonly_fields
        return (
            "invoice",
            "user",
            "amount",
            "reference_code",
            "receipt_attachment",
            "created_at",
        )


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "start_date", "end_date", "created_at")
    list_filter = ("status", "start_date", "end_date", "created_at")
    search_fields = ("title", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at",)
