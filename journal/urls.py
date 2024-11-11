from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path(
        '<str:username>/',
        include([
            path('', views.EntryListView.as_view(), name='entry_list'),
            # path('tag/<slug:tag_slug>/', views.EntryListView.as_view(), name='entry_list_by_tag'),
            path('create/<int:book_pk>/', views.EntryCreateView.as_view(), name='entry_create'),
            path(
                '<int:pk>/',
                include([
                    path('', views.EntryDetailView.as_view(), name='entry_detail'),
                    path('update/', views.EntryUpdateView.as_view(), name='entry_update'),
                    path('delete/', views.EntryDeleteView.as_view(), name='entry_delete'),
                ]),
            ),
        ]),
    ),
]