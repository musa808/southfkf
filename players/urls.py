from django.urls import path

from . import views

app_name = "players"

urlpatterns = [
    path("club/<int:club_pk>/", views.player_list, name="list"),
    path("club/<int:club_pk>/register/", views.player_create, name="create"),
    path("<int:pk>/", views.player_detail, name="detail"),
    path("<int:pk>/edit/", views.player_edit, name="edit"),
]