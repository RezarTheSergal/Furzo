from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

def user_to_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'is_authenticated': user.is_authenticated,
    }


def init_profile(request):
    context = user_to_dict(request.user)
    return render(request, "userprofile/index.html", context)