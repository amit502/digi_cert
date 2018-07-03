from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from .forms import SignUpForm
from django.shortcuts import render, redirect
from .forms import UserForm, ProfileForm
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
import pdb
from django.urls import reverse
import json
from django.contrib.auth.models import User


def home(request):
    return render(request, 'base.html')


def get_users(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        users = User.objects.filter(username__icontains=q)[:20]
        results = []
        for user in users:
            user_json = user.username
            results.append(user_json)
        data = json.dumps(results)
        print(data)
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile, )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('profile', request.user.username)
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'profileUpdate.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def view_profile(request, username):
    person = User.objects.get(username=username)
    return render(request, 'profile.html', {"person": person})


@login_required
def login_redirect(request):
    return redirect('profile', request.user.username)
