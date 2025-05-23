from django.db.models import Q
from django.views import generic
from django.contrib import messages
from django.forms import modelform_factory
from django.core.validators import slug_re
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.http import require_POST
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


@login_required
def journal_redirect(request):
    return HttpResponseRedirect(reverse('journal', args=[request.user.pk]))


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
        context.update({
            'section': 'journal',
        })
        return context


class OtherProfileMixin(object):
    follower = None
    request_from = False
    request_to = False

    def check_and_set_other_profile(self, pk):
        self.profile = get_object_or_404(
            models.Profile,
            pk=pk,
        )
        journal_visibility = self.profile.journal_visibility
        public_user = journal_visibility == models.journal.Visibility.PUBLIC
        if (
            journal_visibility == models.journal.Visibility.PRIVATE
            or (
                not self.request_user.is_authenticated
                and journal_visibility != models.journal.Visibility.PUBLIC
            )
        ):
            self.raise_404(self.profile.user)

        followed_user = False
        self_user = False
        self.request_from = False
        self.request_to = False
        if self.request_user.is_authenticated:
            # save to assume the journal author has at least visibility >= followers
            followed_user = self.request_user.following.all().filter(pk__contains=self.profile.pk).exists()

            if followed_user:
                self.follower = models.Follower.objects.get(
                    user_from=self.request_user,
                    user_to=self.profile.user,
                )
            else:
                # assumes there can only be one follow request from/to
                self.request_from = models.FollowRequest.objects.filter(
                    user_from=self.profile.user,
                    user_to=self.request_user,
                ).first()
                self.request_to = models.FollowRequest.objects.filter(
                    user_from=self.request_user,
                    user_to=self.profile.user,
                ).first()

        if not (public_user or followed_user or self_user):
            self.raise_404(self.profile.user)

    def visible_to_request_user_Q(self):
        """all entries that are visible to self.request.user"""
        published_q = Q(status=models.Entry.Status.PUBLISHED)
        public_q = (
                Q(author__profile__journal_visibility=models.journal.Visibility.PUBLIC)
                & Q(visibility=models.journal.Visibility.PUBLIC)
        )
        follower_q = Q()
        self_q = Q()
        if self.request.user.is_authenticated:
            follower_q = (
                    Q(author__profile__journal_visibility__gte=models.journal.Visibility.FOLLOWERS)
                    & Q(visibility__gte=models.journal.Visibility.FOLLOWERS)
                    & Q(author__in=self.request.user.following.all())
            )
            self_q = Q(author=self.request.user)
        return published_q & (self_q | public_q | follower_q)


class SearchMixin(object):
    form = forms.SearchForm()
    query = None
    query_params = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_params = {}

    def dispatch(self, request, *args, **kwargs):
        self.query = None
        if 'query' in request.GET:
            self.form = forms.SearchForm(request.GET)
            if self.form.is_valid():
                self.query = self.form.cleaned_data['query']
                self.query_params['query'] = self.query
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
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
            'form': self.form,
            'query_params': self.query_params,
        })
        return context


class TagMixin(object):
    tag = None
    query_params = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_params = {}

    def dispatch(self, request, *args, **kwargs):
        self.tag = None
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
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tag': self.tag,
            'query_params': self.query_params,
        })
        return context


class Journal(
    OtherProfileMixin,
    SearchMixin,
    TagMixin,
    generic.ListView,
):
    request_user = None
    profile = None
    is_self_profile: bool

    model = models.Entry
    context_object_name = 'entries'
    paginate_by = 50
    template_name = 'journal/list.html'

    def dispatch(self, request, *args, **kwargs):
        self.request_user = request.user
        user_pk = kwargs.get('user_pk')
        self.is_self_profile = user_pk == self.request_user.pk
        if self.is_self_profile:
            self.profile = self.request_user.profile
        else:
            self.check_and_set_other_profile(user_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(author=self.profile.user)
        if not self.is_self_profile:
            visible_Q = self.visible_to_request_user_Q()
            qs = qs.filter(visible_Q)
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'section': 'journal',
            'profile': self.profile,
            'follower': self.follower,
            'request_from': self.request_from,
            'request_to': self.request_to,
        })
        return context

    def raise_404(self, author):
        raise Http404(
            'Journal of %(author)s is not public or not followed by request.user'
            % {'author': author}
        )


class AsdfJournal(
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
    OtherProfileMixin,
    generic.DetailView,
):
    model = models.Entry
    template_name = 'journal/entry.html'

    def get_queryset(self):
        qs = super().get_queryset()
        visible_Q = self.visible_to_request_user_Q()
        qs = qs.filter(visible_Q)
        if qs.exists():
            return qs
        else:
            raise Http404('Entry does not exist or is not visible to the requesting user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'journal',
        })
        return context


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
        return reverse_lazy('entry_detail', args=[self.request.user.pk, self.object.pk])


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
        return reverse_lazy('journal', args=[self.request.user.pk])


class JournalBook(Journal):
    book = None
    template_name = 'journal/book.html'

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(
            models.Book,
            pk=kwargs.get('book_pk')
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(book=self.book)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
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
        return self.request.user.following.all().filter(
            profile__journal_visibility__gte=models.journal.Visibility.FOLLOWERS,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'following',
        })
        return context


class UserDetail(
    # LoginRequiredMixin,
    generic.DetailView,
):
    model = get_user_model()
    # context_object_name = 'user'
    template_name = 'user/detail.html'
    request_from = None
    request_to = None
    follower = None

    def get_object(self, **kwargs):
        obj = super().get_object(**kwargs)
        profile_visibility = obj.profile.journal_visibility
        public_user = profile_visibility == models.journal.Visibility.PUBLIC

        followed_user = False
        self_user = False
        self.request_from = False
        self.request_to = False
        if self.request.user.is_authenticated:
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
            else:
                # implicitly assumes there can only be one follow request from/to
                self.request_from = models.FollowRequest.objects.filter(
                    user_from=obj,
                    user_to=self.request.user,
                ).first()
                self.request_to = models.FollowRequest.objects.filter(
                    user_from=self.request.user,
                    user_to=obj,
                ).first()

        if not (public_user or followed_user or self_user):
            raise Http404(
                'User %(user)s is not public or not followed by request.user %(request_user)s'
                % {
                    'user': obj,
                    'request_user': self.request.user.username
                }
            )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'following' if self.follower else None,
            'request_from': self.request_from,
            'request_to': self.request_to,
            'follower': self.follower,
        })
        return context


class RequestFollowView(
    LoginRequiredMixin,
    generic.CreateView,
):
    model = models.FollowRequest
    fields = ('message',)
    template_name = 'user/request_follow.html'
    user_from = None
    user_to = None

    def dispatch(self, request, *args, **kwargs):
        self.user_from = request.user
        self.user_to = get_object_or_404(
            get_user_model(),
            pk=kwargs.get('pk'),
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user_from = self.user_from
        form.instance.user_to = self.user_to
        messages.success(
            request=self.request,
            message=f'Your request to follow {self.user_to.username} is sent'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            # 'section': 'discover',
            'user_to': self.user_to,
        })
        return context

    def get_success_url(self):
        return reverse_lazy('user_detail', args=[self.user_to.pk])


class FollowRequestsView(
    LoginRequiredMixin,
    generic.TemplateView,
):
    template_name = 'following/request_list.html'
    follow_requests = None

    def get(self, request, *args, **kwargs):
        self.follow_requests = dict()
        self.follow_requests['outstanding'] = models.FollowRequest.outstanding.filter(user_to=request.user)
        self.follow_requests['accepted'] = models.FollowRequest.accepted.filter(user_to=request.user)
        self.follow_requests['declined'] = models.FollowRequest.declined.filter(user_to=request.user)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'following',
            'follow_requests': self.follow_requests,
        })
        return context


@login_required
@require_POST
def follow_accept(request, request_pk):
    r = get_object_or_404(
        models.FollowRequest,
        pk=request_pk,
        user_to=request.user,
    )
    r.accept()
    next = 'follow_requests'
    if 'next' in request.POST:
        next = request.POST.get('next')
    return redirect(next)


@login_required
@require_POST
def follow_decline(request, request_pk):
    r = get_object_or_404(
        models.FollowRequest,
        pk=request_pk,
        user_to=request.user,
    )
    r.decline()
    next = 'follow_requests'
    if 'next' in request.POST:
        next = request.POST.get('next')
    return redirect(next)


class Discover(
    OtherProfileMixin,
    SearchMixin,
    TagMixin,
    generic.ListView,
):
    model = models.Entry
    context_object_name = 'entries'
    template_name = 'discover/list.html'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        visible_Q = self.visible_to_request_user_Q()
        return qs.filter(visible_Q)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'discover',
        })
        return context


class DiscoverBook(Discover):
    book = None
    template_name = 'discover/book.html'

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(
            models.Book,
            pk=kwargs.get('book_pk'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(book=self.book)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'book': self.book,
        })
        return context
