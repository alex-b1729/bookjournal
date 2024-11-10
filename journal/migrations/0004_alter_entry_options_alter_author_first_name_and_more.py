# Generated by Django 5.1.3 on 2024-11-09 22:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0003_alter_entry_options_remove_entry_published_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="entry",
            options={
                "ordering": ("-publish_dt",),
                "verbose_name": "entry",
                "verbose_name_plural": "entries",
            },
        ),
        migrations.AlterField(
            model_name="author",
            name="first_name",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name="author",
            name="middle_name",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]