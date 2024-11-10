"""
URL configuration for bookjournal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from journal import views as journal_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # path('account/', journal_views.account, name='account'),
    path(
        'account/',
        include([
            path('', journal_views.account, name='account'),
            path('', include('django.contrib.auth.urls')),
            path('register/', journal_views.register, name='register'),
        ]),
    ),
    path('journal/', include('journal.urls')),
    path(
        'books/',
        include([
            path('', journal_views.BookListView.as_view(), name='book_list'),
            path('<int:pk>/', journal_views.BookDetailView.as_view(), name='book_detail'),
        ])
    ),
    path(
        'authors/',
        include([
            path('', journal_views.AuthorListView.as_view(), name='author_list'),
            path('<int:pk>/', journal_views.AuthorDetailView.as_view(), name='author_detail'),
        ])
    ),
]
