from django.urls import path
from . import views

app_name = "referees"

urlpatterns = [
    path("", views.RefereeListView.as_view(), name="referee-list"),
    path("add/", views.RefereeCreateView.as_view(), name="referee-create"),
    path("<int:pk>/", views.RefereeDetailView.as_view(), name="referee-detail"),
    path("<int:pk>/edit/", views.RefereeUpdateView.as_view(), name="referee-update"),
    path("<int:pk>/delete/", views.RefereeDeleteView.as_view(), name="referee-delete"),

    path("assignments/", views.AssignmentListView.as_view(), name="assignment-list"),
    path("assignments/add/", views.AssignmentCreateView.as_view(), name="assignment-create"),
    path("assignments/<int:pk>/edit/", views.AssignmentUpdateView.as_view(), name="assignment-update"),
    path("assignments/<int:pk>/delete/", views.AssignmentDeleteView.as_view(), name="assignment-delete"),
]