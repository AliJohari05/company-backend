from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0002_alter_category_created_at_alter_category_updated_at_and_more")]

    operations = [
        migrations.AddField(model_name="category", name="name_en", field=models.CharField(blank=True, max_length=100, verbose_name="Name (English)")),
        migrations.AddField(model_name="category", name="description_en", field=models.TextField(blank=True, verbose_name="Description (English)")),
        migrations.AddField(model_name="tag", name="name_en", field=models.CharField(blank=True, max_length=100, verbose_name="Name (English)")),
        migrations.AddField(model_name="post", name="title_en", field=models.CharField(blank=True, max_length=250, verbose_name="Title (English)")),
        migrations.AddField(model_name="post", name="content_en", field=models.TextField(blank=True, verbose_name="Content (English)")),
        migrations.AddField(model_name="post", name="meta_description_en", field=models.CharField(blank=True, max_length=160, verbose_name="Meta Description (English)")),
    ]
