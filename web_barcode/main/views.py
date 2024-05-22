from django.shortcuts import render

from .forms import AddPostSignal


def user_groups(request):
    user_groups = request.user.groups.all()
    print(' user_groups', user_groups)
    data = {
        'user_groups': user_groups
    }
    return render(request, 'main/layout.html', data)
