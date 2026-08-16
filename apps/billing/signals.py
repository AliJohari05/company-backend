from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Invoice, InvoiceItem, Transaction


def recalculate_invoice_total(invoice_id):
    invoice = Invoice.objects.filter(pk=invoice_id).first()
    if invoice is not None:
        invoice.recalculate_total()


@receiver(post_save, sender=InvoiceItem)
def update_invoice_total_after_item_save(sender, instance, **kwargs):
    recalculate_invoice_total(instance.invoice_id)


@receiver(post_delete, sender=InvoiceItem)
def update_invoice_total_after_item_delete(sender, instance, **kwargs):
    recalculate_invoice_total(instance.invoice_id)


@receiver(post_save, sender=Transaction)
def update_invoice_status_after_transaction_save(sender, instance, **kwargs):
    instance.invoice.refresh_payment_status()


@receiver(post_delete, sender=Transaction)
def update_invoice_status_after_transaction_delete(sender, instance, **kwargs):
    invoice = Invoice.objects.filter(pk=instance.invoice_id).first()
    if invoice is not None:
        invoice.refresh_payment_status()
