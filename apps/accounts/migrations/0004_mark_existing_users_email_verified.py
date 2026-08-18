from django.db import migrations
from django.utils import timezone


def mark_existing_users_verified(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(is_email_verified=False).update(
        is_email_verified=True,
        email_verified_at=timezone.now(),
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            'accounts',
            '0003_user_email_verified_at_user_is_email_verified',
        ),
    ]

    operations = [
        migrations.RunPython(
            mark_existing_users_verified,
            migrations.RunPython.noop,
        ),
    ]
