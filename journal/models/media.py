from django.db import models
from django.urls import reverse


class Author(models.Model):
    first_name = models.CharField(
        blank=True,
        max_length=50,
    )
    middle_name = models.CharField(
        blank=True,
        max_length=50,
    )
    last_name = models.CharField(
        blank=False,
        max_length=50,
    )
    aka = models.CharField(
        blank=True,
        max_length=200,
        verbose_name='commonly known as',
    )

    class Meta:
        ordering = (
            'last_name',
            'first_name',
        )

    def __str__(self):
        if self.aka:
            return str(self.aka)
        else:
            return ' '.join([str(s) for s in [self.first_name, self.middle_name, self.last_name]])

    def get_absolute_url(self):
        return reverse('author_detail', args=[self.pk])


class Book(models.Model):
    title = models.CharField(
        max_length=200,
        blank=False,
    )
    authors = models.ManyToManyField(
        Author,
        blank=True,
    )
    published = models.SmallIntegerField(
        blank=True,
    )

    class Meta:
        ordering = (
            '-published',
            'title',
        )

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('book_detail', args=[self.pk])
