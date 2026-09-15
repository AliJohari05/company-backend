from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.AddField(model_name="faq", name="answer_en", field=models.TextField(blank=True, verbose_name="Answer (English)")),
        migrations.AddField(model_name="faq", name="question_en", field=models.CharField(blank=True, max_length=255, verbose_name="Question (English)")),
        migrations.AddField(model_name="sitesetting", name="about_us_en", field=models.TextField(blank=True, verbose_name="About Us Text (English)")),
        migrations.AddField(model_name="sitesetting", name="address_en", field=models.TextField(blank=True, verbose_name="Physical Address (English)")),
        migrations.AddField(model_name="sitesetting", name="site_name_en", field=models.CharField(blank=True, max_length=150, verbose_name="Site Name (English)")),
        migrations.AddField(model_name="sitesetting", name="working_hours_en", field=models.CharField(blank=True, max_length=150, verbose_name="Working Hours (English)")),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated At")),
                ("name", models.CharField(max_length=150, verbose_name="Name")),
                ("email", models.EmailField(max_length=254, verbose_name="Email Address")),
                ("phone_number", models.CharField(blank=True, max_length=30, verbose_name="Phone Number")),
                ("subject", models.CharField(max_length=255, verbose_name="Subject")),
                ("message", models.TextField(max_length=5000, verbose_name="Message")),
                ("is_read", models.BooleanField(default=False, verbose_name="Is Read")),
            ],
            options={"verbose_name": "Contact Message", "verbose_name_plural": "Contact Messages", "ordering": ["-created_at"]},
        ),
    ]
