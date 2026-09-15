from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("billing", "0006_private_billing_file_storage")]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="invoice_number",
            field=models.CharField(blank=True, max_length=50, unique=True, verbose_name="Invoice Number"),
        ),
    ]
