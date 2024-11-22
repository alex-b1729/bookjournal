from journal.models import FollowRequest


def follow_requests(request):
    context_data = dict()
    if request.user.is_authenticated:
        context_data['follow_request_count'] = FollowRequest.outstanding.filter(user_to=request.user).count()
    return context_data
