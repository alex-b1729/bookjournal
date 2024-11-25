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
from django.contrib.sitemaps.views import sitemap
from django.contrib.auth import views as auth_views

from journal import views as journal_views
from journal import sitemaps as journal_sitemaps

sitemaps = {
    'authors': journal_sitemaps.AuthorSitemap,
    'books': journal_sitemaps.BookSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    # path('account/', journal_views.account, name='account'),
    path(
        'account/',
        include([
            path('', journal_views.AccountView.as_view(), name='account'),
            path('email/', journal_views.EmailUpdateView.as_view(), name='email_update'),
            path('', include('django.contrib.auth.urls')),
            path('register/', journal_views.register, name='register'),
        ]),
    ),
    path(
        'books/',
        include([
            path('', journal_views.BookListView.as_view(), name='book_list'),
            path('create/', journal_views.BookCreateView.as_view(), name='book_create'),
            path('<int:pk>/', journal_views.BookDetailView.as_view(), name='book_detail'),
        ])
    ),
    path(
        'authors/',
        include([
            path('', journal_views.AuthorListView.as_view(), name='author_list'),
            path('create/', journal_views.AuthorCreateView.as_view(), name='author_create'),
            path('<int:author_pk>/', journal_views.AuthorDetailView.as_view(), name='author_detail'),
        ])
    ),
    path(
        'discover/',
        include([
            path('', journal_views.Discover.as_view(), name='discover'),
        ])
    ),
    path(
        'user/',
        include([
            path(
                'following/',
                include([
                    path('', journal_views.FollowingList.as_view(), name='following_list'),
                    path(
                        'requests/',
                        include([
                            path('', journal_views.FollowRequestsView.as_view(), name='follow_requests'),
                            path('<int:request_pk>/accept/', journal_views.follow_accept, name='follow_accept'),
                            path('<int:request_pk>/decline/', journal_views.follow_decline, name='follow_decline'),
                        ])
                    ),
                ])
            ),
            path(
                '<int:pk>/',
                include([
                    path('', journal_views.UserDetail.as_view(), name='user_detail'),
                    path('follow/', journal_views.RequestFollowView.as_view(), name='request_follow'),
                ])
            ),
        ])
    ),
    path('', journal_views.index, name='index'),
    path('', include('journal.urls')),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'
    ),
]
