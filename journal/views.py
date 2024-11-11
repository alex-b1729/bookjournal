from django.views import generic
from django.urls import reverse_lazy
from django import forms as django_forms
from django.core.validators import slug_re
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404

from taggit.models import Tag

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


def feed(request):
    if request.user.is_authenticated:
        return redirect(reverse_lazy('entry_list', args=[request.user.username]))
    else:
        return render(
            request,
            'entry/feed.html',
            {
                'section': 'journal',
            }
        )


@login_required
def account(request):
    return render(
        request,
        'account.html',
        {'section': 'account'},
    )


class AuthorMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)


class AuthorEditMixin(object):
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class AuthorEntryMixin(AuthorMixin):
    model = models.Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'journal'
        return context


class EntryListView(
    LoginRequiredMixin,
    AuthorEntryMixin,
    generic.ListView,
):
    context_object_name = 'entries'
    paginate_by = 3
    template_name = 'entry/list.html'
    tag = None

    def dispatch(self, request, *args, **kwargs):
        tag_slug = request.GET.get('tag')
        if tag_slug:
            if slug_re.match(tag_slug):
                try:
                    self.tag = Tag.objects.get(slug=tag_slug)
                except Tag.DoesNotExist:
                    pass
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.tag:
            return qs.filter(tags__in=[self.tag])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context


class EntryDetailView(
    LoginRequiredMixin,
    AuthorEntryMixin,
    generic.DetailView,
):
    template_name = 'entry/detail.html'


class AuthorEntryEditMixin(AuthorEntryMixin, AuthorEditMixin):
    fields = (
        'title',
        'status',
        'section',
        'chapter',
        'body',
        'tags',
    )
    template_name = 'manage/entry.html'

    def get_success_url(self):
        return reverse_lazy('entry_detail', args=[self.object.author.username, self.object.pk])


# todo: what's the best UX way to associate a new entry with a book?
class EntryCreateView(
    LoginRequiredMixin,
    AuthorEntryEditMixin,
    generic.CreateView,
):
    book = None

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(
            models.Book,
            pk=kwargs.get('book_pk'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.book
        return context

    def form_valid(self, form):
        form.instance.book = self.book
        return super().form_valid(form)


class EntryUpdateView(
    LoginRequiredMixin,
    AuthorEntryEditMixin,
    generic.UpdateView,
):
    pass


class EntryDeleteView(
    LoginRequiredMixin,
    AuthorEntryMixin,
    generic.DeleteView,
):
    template_name = 'manage/entry_delete.html'

    def get_success_url(self):
        return reverse_lazy('entry_list', args=[self.object.author.username])


class BookCreateView(
    LoginRequiredMixin,
    generic.CreateView,
):
    model = models.Book
    template_name = 'manage/book_create.html'
    fields = ('title', 'authors', 'published',)


class BookListView(generic.ListView):
    queryset = models.Book.objects.all()
    context_object_name = 'books'
    paginate_by = 3
    template_name = 'library/book_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'books'
        return context


class BookDetailView(generic.ListView):
    book = None
    context_object_name = 'entries'
    template_name = 'library/book_detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(
            models.Book,
            pk=kwargs.get('book_pk'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return models.Entry.objects.filter(book=self.book).order_by('section', 'chapter', '-publish_dt')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.book
        context['section'] = 'books'
        return context


class AuthorCreateView(
    LoginRequiredMixin,
    generic.CreateView,
):
    model = models.Author
    template_name = 'manage/author_create.html'
    fields = '__all__'

    def get_form(self, **kwargs):
        form = super().get_form(**kwargs)
        form.fields['aka'].help_text = 'For example: J. R. R. Tolkien'
        return form


class AuthorListView(generic.ListView):
    queryset = models.Author.objects.all()
    context_object_name = 'authors'
    paginate_by = 3
    template_name = 'library/author_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'authors'
        return context


class AuthorDetailView(generic.ListView):
    author = None
    context_object_name = 'books'
    paginate_by = 3
    template_name = 'library/author_detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.author = get_object_or_404(
            models.Author,
            pk=kwargs.get('author_pk'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return models.Book.objects.filter(authors__in=[self.author])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        context['section'] = 'authors'
        return context
