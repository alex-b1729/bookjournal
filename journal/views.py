from django.http import HttpResponse
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from journal import forms
from journal import models


def register(request):
    """depreciated for registration wizard"""
    if request.method == 'POST':
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            return render(
                request,
                'registration/register_done.html',
                {'new_user': new_user},
            )
    else:
        form = forms.UserRegistrationForm()
    return render(
        request,
        'registration/register.html',
        {'form': form}
    )


@login_required
def account(request):
    return render(
        request,
        'account.html',
        {'section': 'account'},
    )


class EntryListView(
    LoginRequiredMixin,
    ListView,
):
    queryset = None
    context_object_name = 'entries'
    paginate_by = 3
    template_name = 'entry/list.html'

    def dispatch(self, request, *args, **kwargs):
        self.queryset = models.Entry.objects.filter(author=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'section': 'journal'})
        return context


@login_required
def entry_detail(request, entry_pk):
    entry = get_object_or_404(
        models.Entry,
        pk=entry_pk,
        author=request.user,
    )
    return render(
        request,
        'entry/detail.html',
        {
            'section': 'journal',
            'entry': entry,
        }
    )


class BookListView(
    ListView,
):
    queryset = models.Book.objects.all()
    context_object_name = 'books'
    paginate_by = 3
    template_name = 'library/book_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'section': 'books'})
        return context


def book_detail_view(request, book_pk):
    book = get_object_or_404(
        models.Book,
        pk=book_pk,
    )
    return render(
        request,
        'library/book_detail.html',
        {
            'section': 'books',
            'book': book,
        },
    )


class AuthorListView(
    ListView,
):
    queryset = models.Author.objects.all()
    context_object_name = 'authors'
    paginate_by = 3
    template_name = 'library/author_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'section': 'authors'})
        return context


def author_detail_view(request, author_pk):
    author = get_object_or_404(
        models.Author,
        pk=author_pk,
    )
    return render(
        request,
        'library/author_detail.html',
        {
            'section': 'authors',
            'author': author,
        },
    )
