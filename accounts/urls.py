from django.urls import path

from .views import ProfileView, SignUpView
from django.contrib.auth.decorators import login_not_required

urlpatterns = [
     path("signup/", login_not_required(SignUpView.as_view()), name="signup"),
    path("profile/", ProfileView.as_view(), name="profile"),
]