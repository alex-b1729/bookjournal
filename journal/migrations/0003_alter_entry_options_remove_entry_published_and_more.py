# Generated by Django 5.1.3 on 2024-11-09 19:56

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0002_entry_status"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="entry",
            options={"ordering": ("-publish_dt",)},
        ),
        migrations.RemoveField(
            model_name="entry",
            name="published",
        ),
        migrations.AddField(
            model_name="entry",
            name="publish_dt",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="time published"
            ),
        ),
    ]