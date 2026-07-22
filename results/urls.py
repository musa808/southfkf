from django.urls import path
from . import views

app_name = "results"

urlpatterns = [
    path("fixture/<int:fixture_pk>/enter/", views.enter_result, name="enter"),
    path("fixture/<int:fixture_pk>/edit/", views.edit_result, name="edit"),
    path("competition/<int:competition_pk>/", views.result_list, name="list"),
]