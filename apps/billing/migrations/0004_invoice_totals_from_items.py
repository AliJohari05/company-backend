from decimal import Decimal

import django.core.validators
from django.db import migrations, models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum


def align_existing_invoice_items(apps, schema_editor):
    Invoice = apps.get_model('billing', 'Invoice')
    InvoiceItem = apps.get_model('billing', 'InvoiceItem')

    line_total = ExpressionWrapper(
        F('quantity') * F('unit_price'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    for invoice in Invoice.objects.all().iterator():
        items_total = (
            InvoiceItem.objects.filter(invoice_id=invoice.pk)
            .aggregate(total=Sum(line_total))['total']
            or Decimal('0.00')
        )

        if invoice.total_amount > items_total:
            InvoiceItem.objects.create(
                invoice_id=invoice.pk,
                description='Legacy invoice balance',
                quantity=1,
                unit_price=invoice.total_amount - items_total,
            )
            items_total = invoice.total_amount

        if invoice.total_amount != items_total:
            Invoice.objects.filter(pk=invoice.pk).update(
                total_amount=items_total
            )


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_invoice_status_partially_paid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='total_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=12,
                verbose_name='Total Amount',
            ),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='quantity',
            field=models.PositiveIntegerField(
                default=1,
                validators=[
                    django.core.validators.MinValueValidator(1),
                ],
                verbose_name='Quantity',
            ),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='unit_price',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0.01')),
                ],
                verbose_name='Unit Price',
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0.01')),
                ],
                verbose_name='Amount Paid',
            ),
        ),
        migrations.RunPython(
            align_existing_invoice_items,
            migrations.RunPython.noop,
        ),
    ]
