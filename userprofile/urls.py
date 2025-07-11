from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.init_profile, name="profile"),
]
