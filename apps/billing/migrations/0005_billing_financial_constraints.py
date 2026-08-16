from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_invoice_totals_from_items'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name='billing_invoice_total_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='invoiceitem',
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name='billing_invoice_item_quantity_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='invoiceitem',
            constraint=models.CheckConstraint(
                condition=models.Q(unit_price__gt=0),
                name='billing_invoice_item_price_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='transaction',
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name='billing_transaction_amount_positive',
            ),
        ),
        migrations.AddConstraint(
            model_name='transaction',
            constraint=models.UniqueConstraint(
                fields=('invoice', 'reference_code'),
                name='billing_unique_reference_per_invoice',
            ),
        ),
    ]
