from django.db import models


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
        ordering = ['last_name']

    def __str__(self):
        if self.aka:
            return str(self.aka)
        else:
            return ' '.join([str(s) for s in [self.first_name, self.middle_name, self.last_name]])


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

    def __str__(self):
        return str(self.title)
