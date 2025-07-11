from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    
    path("accounts/profile/", include("userprofile.urls"), name="profile"),
    path("accounts/", include("allauth.urls"), name="accounts"),
    path('get-post/', views.get_post, name='get_post'),
    path('get-specific-post/', views.get_specific_post, name='get_specific_post'),
    path('toggle-like/', views.toggle_like, name='toggle_like'),
    path('toggle-dislike/', views.toggle_dislike, name='toggle_dislike'),
    path('increment-views/', views.increment_views, name='increment_views'),
    path('comments/', views.comments, name='comments'),
    path('add_comment/', views.add_comment, name='add_comment'),
]
