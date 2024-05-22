def user_groups(request):
    if request.user.is_authenticated:
        return {'user_groups': request.user.groups.values_list('name', flat=True)}
    else:
        return {}
