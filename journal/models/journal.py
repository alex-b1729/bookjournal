from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import media


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Entry.Status.PUBLISHED)


class Entry(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'd', _('Draft')
        PUBLISHED = 'p', _('Published')

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    book = models.ForeignKey(
        media.Book,
        on_delete=models.CASCADE,  # doesn't feel right, consider changing
    )
    title = models.CharField(
        max_length=200,
        blank=True,
    )
    body = models.TextField(
        blank=False,
    )
    status = models.CharField(
        max_length=1,
        choices=Status,
        default=Status.PUBLISHED,
    )
    publish_dt = models.DateTimeField(
        default=timezone.now,
        verbose_name='time published',
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    updated = models.DateTimeField(
        auto_now=True,
    )

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ('-publish_dt',)
        verbose_name = 'entry'
        verbose_name_plural = 'entries'

    def __str__(self):
        return f'{self.title if self.title else self.book} - {self.author}'

    def get_absolute_url(self):
        return reverse('journal:entry_detail', args=[self.pk])
