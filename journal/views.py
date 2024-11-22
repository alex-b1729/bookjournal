from django.db.models import Q
from django.views import generic
from django.contrib import messages
from django.core.validators import slug_re
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, Http404
from django.contrib.postgres.search import SearchVector
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View

from taggit.models import Tag

from journal import forms
from journal import models


def index(request):
    return render(
        request,
        'index.html',
    )


def register(request):
    """depreciated for registration wizard"""
    if request.method == 'POST':
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            messages.success(request, f'Welcome, {new_user.username}.')
            return HttpResponseRedirect(f'{reverse("login")}?next=/account/')
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


class AccountView(
    LoginRequiredMixin,
    generic.UpdateView,
):
    fields = ('journal_visibility', 'default_visibility', 'about',)
    template_name = 'account.html'
    success_url = '/account/'

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'account',
        })
        return context

    def form_valid(self, form):
        messages.success(request=self.request, message='Account updated successfully')
        return super().form_valid(form)


class EmailUpdateView(
    LoginRequiredMixin,
    generic.UpdateView,
):
    fields = ('email',)
    template_name = 'manage/email_update.html'
    success_url = '/account/'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'account',
        })
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Email updated successfully')
        return super().form_valid(form)


class UserMixin(object):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(author=self.request.user)


class UserEditMixin(object):
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class UserEntryMixin(UserMixin):
    model = models.Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['section'] = 'journal'
        return context


class UserJournal(
    LoginRequiredMixin,
    UserEntryMixin,
    generic.ListView,
):
    """ListView of all request.user's entries"""
    context_object_name = 'entries'
    paginate_by = 50
    template_name = 'journal/list.html'
    query_params = {}
    tag = None
    form = forms.SearchForm()
    query = None
    results = []

    def dispatch(self, request, *args, **kwargs):
        self.query_params = {}
        # search management
        if 'query' in request.GET:
            # todo: problem if this includes tag GET data?
            self.form = forms.SearchForm(request.GET)
            if self.form.is_valid():
                self.query = self.form.cleaned_data['query']
                self.query_params['query'] = self.query

        # tag management
        tag_slug = request.GET.get('tag')
        if tag_slug:
            if slug_re.match(tag_slug):
                try:
                    self.tag = Tag.objects.get(slug=tag_slug)
                    self.query_params['tag'] = self.tag.slug
                except Tag.DoesNotExist:
                    pass
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.tag:
            qs = qs.filter(tags__in=[self.tag])
        if self.query:
            qs = qs.annotate(
                search=SearchVector(
                    'title',
                    'body',
                    'book__title',
                ),
            ).filter(search=self.query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tag': self.tag,
            'form': self.form,
            'query_params': self.query_params,
        })
        return context


class UserEntryDetail(
    LoginRequiredMixin,
    UserEntryMixin,
    generic.DetailView,
):
    """DetailView of an entry of request.user"""
    template_name = 'journal/entry.html'


class UserEntryEditMixin(
    UserEntryMixin,
    UserEditMixin,
):
    fields = (
        'title',
        'visibility',
        'section',
        'chapter',
        'tags',
        'body',
    )
    template_name = 'manage/entry.html'

    def get_success_url(self):
        return reverse_lazy('user_entry_detail', args=[self.object.pk])


class UserEntryCreateView(
    LoginRequiredMixin,
    UserEntryEditMixin,
    generic.CreateView,
):
    book = None

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(
            models.Book,
            pk=kwargs.get('book_pk'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            'visibility': self.request.user.profile.default_visibility,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'book': self.book,
        })
        return context

    def form_valid(self, form):
        form.instance.book = self.book
        return super().form_valid(form)


class UserEntryUpdate(
    LoginRequiredMixin,
    UserEntryEditMixin,
    generic.UpdateView,
):
    pass


class UserEntryDelete(
    LoginRequiredMixin,
    UserEntryMixin,
    generic.DeleteView,
):
    template_name = 'manage/entry_delete.html'

    def get_success_url(self):
        # todo: accept a next page
        return reverse_lazy('user_journal')


class UserBookEntryList(
    LoginRequiredMixin,
    generic.ListView,
):
    """ListView of request.user's entries associated with a book"""
    book = None
    context_object_name = 'entries'
    template_name = 'journal/book.html'

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(
            models.Book,
            pk=kwargs.get('book_pk')
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return models.Entry.objects.filter(
            author=self.request.user,
            book=self.book,
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'section': 'journal',
            'book': self.book,
        })
        return context


class BookCreateView(
    LoginRequiredMixin,
    generic.CreateView,
):
    model = models.Book
    template_name = 'manage/book_create.html'
    fields = ('title', 'authors', 'published',)


class BookListView(generic.ListView):
    context_object_name = 'books'
    paginate_by = 50
    template_name = 'library/book_list.html'
    query_params = {}
    form = forms.SearchForm()
    query = None
    results = []

    def dispatch(self, request, *args, **kwargs):
        self.query_params = {}
        if 'query' in request.GET:
            self.form = forms.SearchForm(request.GET)
            if self.form.is_valid():
                self.query = self.form.cleaned_data['query']
                self.query_params['query'] = self.query
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = models.Book.objects.all()
        if self.query:
            qs = qs.annotate(
                search=SearchVector(
                    'title',
                    # todo: how to search authors?
                ),
            ).filter(search=self.query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'books',
            'form': self.form,
            'query_params': self.query_params,
        })
        return context


class BookDetailView(generic.DetailView):
    model = models.Book
    context_object_name = 'book'
    template_name = 'library/book_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'books'
        })
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
    context_object_name = 'authors'
    paginate_by = 50
    template_name = 'library/author_list.html'
    query_params = {}
    form = forms.SearchForm()
    query = None
    results = []

    def dispatch(self, request, *args, **kwargs):
        self.query_params = {}
        if 'query' in request.GET:
            self.form = forms.SearchForm(request.GET)
            if self.form.is_valid():
                self.query = self.form.cleaned_data['query']
                self.query_params['query'] = self.query
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = models.Author.objects.all()
        if self.query:
            qs = qs.annotate(
                search=SearchVector(
                    'first_name',
                    'middle_name',
                    'last_name',
                    'aka',
                ),
            ).filter(search=self.query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'authors',
            'form': self.form,
            'query_params': self.query_params,
        })
        return context


class AuthorDetailView(generic.ListView):
    author = None
    context_object_name = 'books'
    # paginate_by = 3
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
        context.update({
            'section': 'authors',
            'author': self.author,
        })
        return context


class FollowingList(
    LoginRequiredMixin,
    generic.ListView,
):
    context_object_name = 'following'
    paginate_by = 50
    template_name = 'following/list.html'

    def get_queryset(self):
        return self.request.user.following.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'feed',
        })
        return context


class UserDetail(
    LoginRequiredMixin,
    generic.DetailView,
):
    model = get_user_model()
    # context_object_name = 'user'
    template_name = 'user/detail.html'
    follower = None

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        profile_visibility = obj.profile.journal_visibility
        public_user = profile_visibility == models.journal.Visibility.PUBLIC
        followed_user = (
                profile_visibility >= models.journal.Visibility.FOLLOWERS
                and self.request.user.following.all().filter(pk__contains=obj.pk).exists()
        )
        self_user = obj == self.request.user
        if followed_user:
            self.follower = models.Follower.objects.get(
                user_from=self.request.user,
                user_to=obj,
            )
        if not (public_user or followed_user or self_user):
            raise Http404(
                'User is not public or not followed by user %(request_user)s'
                % {'request_user': self.request.user.username}
            )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'feed',
            'follower': self.follower,
        })
        return context


class FeedList(
    LoginRequiredMixin,
    generic.ListView,
):
    context_object_name = 'entries'
    template_name = 'feed/list.html'
    paginate_by = 50
    view_form = None

    def dispatch(self, request, *args, **kwargs):
        # self.view_form = forms.FeedViewSelectForm()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        published_q = Q(status=models.Entry.Status.PUBLISHED)
        public_q = (
            Q(author__profile__journal_visibility=models.journal.Visibility.PUBLIC)
            & Q(visibility=models.journal.Visibility.PUBLIC)
        )
        follower_q = (
            Q(author__profile__journal_visibility__gte=models.journal.Visibility.FOLLOWERS)
            & Q(visibility__gte=models.journal.Visibility.FOLLOWERS)
            & Q(author__in=self.request.user.following.all())
        )
        self_q = Q(author=self.request.user)
        qs = models.Entry.objects.filter(
            published_q & (self_q | public_q | follower_q)
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'feed',
            # 'view_form': self.view_form,
        })
        return context
