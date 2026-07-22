from django.urls import path
from . import views

app_name = "coaches"

urlpatterns = [
    path("", views.CoachListView.as_view(), name="coach-list"),
    path("add/", views.CoachCreateView.as_view(), name="coach-create"),
    path("<int:pk>/", views.CoachDetailView.as_view(), name="coach-detail"),
    path("<int:pk>/edit/", views.CoachUpdateView.as_view(), name="coach-update"),
    path("<int:pk>/delete/", views.CoachDeleteView.as_view(), name="coach-delete"),
]