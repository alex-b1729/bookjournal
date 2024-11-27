from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.journal_redirect, name='user_journal'),
    path(
        '<int:user_pk>/',
        include([
            path('', views.Journal.as_view(), name='journal'),
            path(
                'entry/<int:pk>/',
                include([
                    path('', views.UserEntryDetail.as_view(), name='entry_detail'),
                    path('update/', views.UserEntryUpdate.as_view(), name='entry_update'),
                    path('delete/', views.UserEntryDelete.as_view(), name='entry_delete'),
                ])
            ),
            path(
                'book/<int:book_pk>/',
                include([
                    path('',  views.JournalBook.as_view(), name='journal_book'),
                    path('create/', views.UserEntryCreateView.as_view(), name='entry_create'),
                ])
            ),
        ])
    ),
]
