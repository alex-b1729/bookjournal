from django.contrib import admin

from .models import (
    Author,
    Book,
    Entry,
)


admin.site.register(Author)
admin.site.register(Book)
admin.site.register(Entry)
