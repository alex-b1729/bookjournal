from django.urls import path, include

from . import views

urlpatterns = [
    path(
        'journal/',
        include([
            path('', views.UserJournal.as_view(), name='user_journal'),
            path('entry/create/<int:book_pk>/', views.UserEntryCreateView.as_view(), name='user_entry_create'),
            path(
                'entry/<int:pk>/',
                include([
                    path('', views.UserEntryDetail.as_view(), name='user_entry_detail'),
                    path('update/', views.UserEntryUpdate.as_view(), name='user_entry_update'),
                    path('delete/', views.UserEntryDelete.as_view(), name='user_entry_delete'),
                ])
            ),
            path('book/<int:book_pk>/',  views.UserBookEntryList.as_view(), name='user_book_entry_list'),
            # path('author/<int:author_pk>/',  views.UserAuthorEntryList.as_view(), name='user_author_detail'),
        ])
    ),
    # path(
    #     'feed/',
    #     include([
    #         path('', views.Feed.as_view(), name='feed'),
    #         path(
    #             'user/<int:user_pk>/',
    #             include([
    #                 path('', views.UserDetail.as_view(), name='user_detail'),
    #                 path('entry/<int:entry_pk>/', views.FeedEntryDetail.as_view(), name='feed_user_entry_detail'),
    #                 path('book/<int:book_pk>/',  views.FeedBookDetail.as_view(), name='feed_user_book_detail'),
    #                 # path('author/<int:author_pk>/',  views.FeedAuthorDetail.as_view(), name='feed_user_author_detail'),
    #             ])
    #         ),
    #         path('entry/<int:entry_pk>/', views.FeedEntryDetail.as_view(), name='feed_entry_detail'),
    #         path('book/<int:book_pk>/',  views.FeedBookDetail.as_view(), name='feed_book_detail'),
    #         # path('author/<int:author_pk>/',  views.FeedAuthorDetail.as_view(), name='feed_author_detail'),
    #     ])
    # ),

    # these are all old
    # path('', views.feed, name='feed'),
    # path(
    #     '<str:username>/',
    #     include([
    #         path('', views.EntryListView.as_view(), name='entry_list'),
    #         # path('tag/<slug:tag_slug>/', views.EntryListView.as_view(), name='entry_list_by_tag'),
    #         path('create/<int:book_pk>/', views.EntryCreateView.as_view(), name='entry_create'),
    #         path(
    #             '<int:pk>/',
    #             include([
    #                 path('', views.EntryDetailView.as_view(), name='entry_detail'),
    #                 path('update/', views.EntryUpdateView.as_view(), name='entry_update'),
    #                 path('delete/', views.EntryDeleteView.as_view(), name='entry_delete'),
    #             ]),
    #         ),
    #     ]),
    # ),
]