from django.urls import path

from . import views

app_name = "seasons"

urlpatterns = [
    path("", views.season_list, name="list"),
    path("create/", views.season_create, name="create"),
    path("<int:pk>/", views.season_detail, name="detail"),
    path("<int:pk>/edit/", views.season_edit, name="edit"),
]