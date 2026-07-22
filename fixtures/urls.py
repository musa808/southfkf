from django.urls import path

from . import views

app_name = "fixtures"

urlpatterns = [
    path("competition/<int:competition_pk>/", views.fixture_list, name="list"),
    path("competition/<int:competition_pk>/generate-league/", views.generate_league, name="generate_league"),
    path("group/<int:group_pk>/generate/", views.generate_group, name="generate_group"),
    path(
        "knockout-slot/<int:knockout_fixture_pk>/assign/",
        views.assign_knockout_slot,
        name="assign_knockout_slot",
    ),
    path("<int:pk>/edit/", views.fixture_edit, name="edit"),
]