from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.EntryListView.as_view(), name='entry_list'),
    # path('create/', views.EntryCreateView.as_view(), name='entry_create'),
    path(
        '<int:pk>/',
        include([
            path('', views.EntryDetailView.as_view(), name='entry_detail'),
            path('update/', views.EntryUpdateView.as_view(), name='entry_update'),
            path('delete/', views.EntryDeleteView.as_view(), name='entry_delete'),
        ]),
    ),
]