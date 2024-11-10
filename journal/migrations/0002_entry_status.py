# Generated by Django 5.1.3 on 2024-11-09 19:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="entry",
            name="status",
            field=models.CharField(
                choices=[("d", "Draft"), ("p", "Published")], default="p", max_length=1
            ),
        ),
    ]