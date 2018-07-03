from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', views.signup, name='signup'),
    path('login_redirect/', views.login_redirect, name='login_redirect'),
    path('profile/(?P<username>\w+)/$', views.view_profile, name='profile'),
    path('update_profile/', views.update_profile, name='updateProfile'),
    path('get_users/', views.get_users, name = 'get_users'),
]
