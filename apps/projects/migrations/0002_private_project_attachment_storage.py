import apps.core.storage
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectattachment',
            name='file',
            field=models.FileField(
                storage=apps.core.storage.PrivateMediaStorage(),
                upload_to='project_attachments/%Y/%m/',
                verbose_name='File',
            ),
        ),
    ]
