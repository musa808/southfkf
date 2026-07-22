from django.urls import path
from . import views

app_name = "standings"

urlpatterns = [
    path("competition/<int:competition_pk>/", views.standings_table, name="table"),
]