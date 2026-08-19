import apps.core.storage
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tickets', '0003_alter_ticket_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketmessage',
            name='attachment',
            field=models.FileField(
                blank=True,
                null=True,
                storage=apps.core.storage.PrivateMediaStorage(),
                upload_to='tickets/attachments/',
                verbose_name='Attachment',
            ),
        ),
    ]
