from django.urls import path

from . import views

app_name = "transfers"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("initiate/", views.initiate_transfer, name="initiate"),
    path("<int:pk>/", views.transfer_detail, name="detail"),
    path("<int:pk>/certificate/", views.transfer_certificate, name="certificate"),
    path("<int:pk>/accept/", views.respond_accept, name="respond_accept"),
    path("<int:pk>/reject/", views.respond_reject, name="respond_reject"),
    path("<int:pk>/cancel/", views.cancel_transfer, name="cancel"),
    path("<int:pk>/subcounty-approve/", views.subcounty_approve, name="subcounty_approve"),
    path("<int:pk>/subcounty-reject/", views.subcounty_reject, name="subcounty_reject"),
    path("player/<int:player_id>/history/", views.player_history, name="player_history"),
    path("club/<int:club_id>/history/", views.club_history, name="club_history"),
    path("windows/", views.window_list, name="window_list"),
    path("windows/new/", views.window_create, name="window_create"),
    path("windows/<int:pk>/edit/", views.window_edit, name="window_edit"),
]