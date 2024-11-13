from django.contrib.sitemaps import Sitemap

import journal.models as models

# todo: last mod


class AuthorSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return models.Author.objects.all()


class BookSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return models.Book.objects.all()
