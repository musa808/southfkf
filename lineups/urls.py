from django.urls import path

from . import views

app_name = "lineups"

urlpatterns = [
    # Lineups landing page — list of fixtures/teams needing lineups
    path(
        "",
        views.lineups_home,
        name="home",
    ),
    # Submit or edit lineup for a team in a fixture
    path(
        "fixture/<int:fixture_pk>/team/<int:team_pk>/submit/",
        views.submit_lineup,
        name="submit",
    ),
    # View both lineups for a fixture
    path(
        "fixture/<int:fixture_pk>/",
        views.fixture_lineups,
        name="fixture_lineups",
    ),
]