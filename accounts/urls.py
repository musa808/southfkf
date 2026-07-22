from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import FCMSLoginForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=FCMSLoginForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("create-club-admin/", views.create_club_admin, name="create_club_admin"),
]