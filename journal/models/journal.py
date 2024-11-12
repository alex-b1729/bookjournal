from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from . import library


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Entry.Status.PUBLISHED)


class Visibility(models.TextChoices):
    PRIVATE = 'x', _('Private')
    FOLLOWERS = 'f', _('Followers')
    PUBLIC = 'p', _('Public')


class Entry(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'd', _('Draft')
        PUBLISHED = 'p', _('Published')

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    book = models.ForeignKey(
        library.Book,
        on_delete=models.CASCADE,  # doesn't feel right, consider changing
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='entry title',
    )
    body = models.TextField(
        blank=False,
    )
    status = models.CharField(
        max_length=1,
        choices=Status,
        default=Status.PUBLISHED,
    )
    tags = TaggableManager(blank=True)
    section = models.CharField(
        max_length=200,
        blank=True,
    )
    chapter = models.CharField(
        max_length=200,
        blank=True,
    )
    visibility = models.CharField(
        max_length=1,
        choices=Visibility,
        default=Visibility.PRIVATE,
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
        return f'{self.publish_dt} - {self.title if self.title else self.book} - {self.author}'

    def get_absolute_url(self):
        return reverse('entry_detail', args=[self.author.username, self.pk])
