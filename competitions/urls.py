from django.urls import path

from . import views

app_name = "competitions"

urlpatterns = [
    path("", views.competition_list, name="list"),
    path("create/", views.competition_create, name="create"),
    path("<int:pk>/", views.competition_detail, name="detail"),
    path("<int:pk>/edit/", views.competition_edit, name="edit"),
    path("<int:pk>/add-teams/", views.add_teams, name="add_teams"),
    path("<int:pk>/remove-team/<int:team_pk>/", views.remove_team, name="remove_team"),
    path("<int:pk>/setup-groups/", views.setup_groups, name="setup_groups"),
    path("<int:pk>/setup-knockout-rounds/", views.setup_knockout_rounds, name="setup_knockout_rounds"),
    path("<int:pk>/generate-bracket-slots/", views.generate_bracket_slots_view, name="generate_bracket_slots"),
    path("competition/<int:competition_pk>/bracket/", views.bracket_view, name="bracket"),
    path("bracket-fixture/<int:fixture_pk>/assign/", views.bracket_assign_slot, name="bracket_assign_slot"),
    path("bracket-fixture/<int:fixture_pk>/clear/", views.bracket_clear_slot, name="bracket_clear_slot"),
]