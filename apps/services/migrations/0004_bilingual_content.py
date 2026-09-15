from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("services", "0003_alter_service_created_at_alter_service_updated_at_and_more")]

    operations = [
        migrations.AddField(model_name="servicecategory", name="title_en", field=models.CharField(blank=True, max_length=250, verbose_name="Title (English)")),
        migrations.AddField(model_name="servicecategory", name="description_en", field=models.TextField(blank=True, verbose_name="Description (English)")),
        migrations.AddField(model_name="service", name="title_en", field=models.CharField(blank=True, max_length=250, verbose_name="Title (English)")),
        migrations.AddField(model_name="service", name="short_description_en", field=models.TextField(blank=True, verbose_name="Short Description (English)")),
        migrations.AddField(model_name="service", name="full_description_en", field=models.TextField(blank=True, verbose_name="Full Description (English)")),
        migrations.AddField(model_name="serviceplan", name="title_en", field=models.CharField(blank=True, max_length=250, verbose_name="Title (English)")),
        migrations.AddField(model_name="serviceplan", name="features_en", field=models.JSONField(blank=True, default=list, verbose_name="Features (English)")),
    ]
