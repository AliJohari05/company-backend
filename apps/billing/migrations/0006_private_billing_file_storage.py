import apps.billing.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_billing_financial_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='file',
            field=models.FileField(
                storage=apps.billing.storage.PrivateBillingStorage(),
                upload_to='contracts/',
                verbose_name='Contract Document (PDF)',
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='receipt_attachment',
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.billing.storage.PrivateBillingStorage(),
                upload_to='receipts/',
                verbose_name='Receipt Attachment',
            ),
        ),
    ]
