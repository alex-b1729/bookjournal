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
    return HttpResponse('Your account =)')


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
            'entry': entry,
        }
    )
