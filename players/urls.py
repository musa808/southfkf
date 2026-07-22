from django.urls import path
from . import views

app_name = "players"

urlpatterns = [
    path("club/<int:club_pk>/", views.player_list, name="list"),
    path("<int:pk>/", views.player_detail, name="detail"),
]