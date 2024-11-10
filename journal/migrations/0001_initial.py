# Generated by Django 5.1.3 on 2024-11-10 21:35

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Author",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=50)),
                ("middle_name", models.CharField(blank=True, max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                (
                    "aka",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="commonly known as"
                    ),
                ),
            ],
            options={
                "ordering": ("last_name", "first_name"),
            },
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("published", models.SmallIntegerField(blank=True)),
                ("authors", models.ManyToManyField(blank=True, to="journal.author")),
            ],
            options={
                "ordering": ("-published", "title"),
            },
        ),
        migrations.CreateModel(
            name="Entry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=200)),
                ("body", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("d", "Draft"), ("p", "Published")],
                        default="p",
                        max_length=1,
                    ),
                ),
                (
                    "publish_dt",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="time published"
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="journal.book"
                    ),
                ),
            ],
            options={
                "verbose_name": "entry",
                "verbose_name_plural": "entries",
                "ordering": ("-publish_dt",),
            },
        ),
    ]
