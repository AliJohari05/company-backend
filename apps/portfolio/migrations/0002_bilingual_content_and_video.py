from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("portfolio", "0001_initial")]

    operations = [
        migrations.AddField(model_name="category", name="title_en", field=models.CharField(blank=True, max_length=100, verbose_name="Category Title (English)")),
        migrations.AddField(model_name="technology", name="name_en", field=models.CharField(blank=True, max_length=50, verbose_name="Technology Name (English)")),
        migrations.AddField(model_name="portfolioitem", name="title_en", field=models.CharField(blank=True, max_length=200, verbose_name="Project Title (English)")),
        migrations.AddField(model_name="portfolioitem", name="summary_en", field=models.TextField(blank=True, max_length=500, verbose_name="Short Summary (English)")),
        migrations.AddField(model_name="portfolioitem", name="description_en", field=models.TextField(blank=True, verbose_name="Full Project Description (English)")),
        migrations.AddField(model_name="portfolioitem", name="video_url", field=models.URLField(blank=True, verbose_name="Project Video URL")),
        migrations.AddField(model_name="portfolioimage", name="caption_en", field=models.CharField(blank=True, max_length=200, verbose_name="Caption (English)")),
    ]
