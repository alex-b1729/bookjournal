from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from . import library


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
        editable=False,
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

    class Meta:
        ordering = ('-publish_dt',)
        verbose_name = 'entry'
        verbose_name_plural = 'entries'

    def __str__(self):
        return f'{self.publish_dt} - {self.title if self.title else self.book} - {self.author}'

    def get_absolute_url(self):
        return reverse('entry_detail', args=[self.author.username, self.pk])


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        editable=False,
    )
    journal_visibility = models.CharField(
        max_length=1,
        choices=Visibility,
        default=Visibility.FOLLOWERS,
        verbose_name='journal visibility',
    )
    default_visibility = models.CharField(
        max_length=1,
        choices=Visibility,
        default=Visibility.PRIVATE,
        verbose_name='default entry visibility',
    )
    about = models.TextField(
        blank=True,
    )


class Follower(models.Model):
    user_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='follower_from_set',
        on_delete=models.CASCADE,
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='follower_to_set',
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ('user_to__username',)

    def __str__(self):
        return f'{self.user_from.username} follows {self.user_to.username}'


User.add_to_class(
    'following',
    models.ManyToManyField(
        'self',
        through=Follower,
        symmetrical=True,
    )
)


class RequestStatus(models.TextChoices):
    OUTSTANDING = 'o', _('Outstanding')
    ACCEPTED = 'a', _('Accepted')
    DECLINED = 'd', _('Declined')


class OutstandingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=RequestStatus.OUTSTANDING)


class AcceptedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=RequestStatus.ACCEPTED)


class DeclinedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=RequestStatus.DECLINED)


class FollowRequest(models.Model):
    user_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='request_from_set',
        on_delete=models.CASCADE,
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='request_to_set',
        on_delete=models.CASCADE,
    )
    message = models.CharField(
        max_length=200,
        blank=True,
    )
    requested = models.DateTimeField(
        auto_now_add=True,
    )
    status = models.CharField(
        max_length=1,
        choices=RequestStatus,
        default=RequestStatus.OUTSTANDING,
    )
    updated = models.DateTimeField(
        auto_now=True,
    )

    objects = models.Manager()
    outstanding = OutstandingManager()
    accepted = AcceptedManager()
    declined = DeclinedManager()

    class Meta:
        ordering = ('-requested',)

    def __str__(self):
        return f'{self.user_from.username} requested to follow {self.user_to.username}'

    def accept(self):
        self.status = RequestStatus.ACCEPTED
        self.save()
        self.user_from.followers.add(self.user_to)

    def decline(self):
        self.status = RequestStatus.DECLINED
        self.save()


User.add_to_class(
    'requests_made',
    models.ManyToManyField(
        'self',
        through=FollowRequest,
        related_name='requests_of',
        symmetrical=False,
    )
)
