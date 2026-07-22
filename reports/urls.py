from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_index, name="index"),
    path("home/", views.reports_home, name="home"),
    path("competition/<int:competition_pk>/", views.report_index, name="index"),
    path("competition/<int:competition_pk>/fixtures.pdf", views.fixture_list_pdf, name="fixtures_pdf"),
    path("competition/<int:competition_pk>/standings.pdf", views.standings_pdf, name="standings_pdf"),
    path("competition/<int:competition_pk>/top-scorers.pdf", views.top_scorers_pdf, name="top_scorers_pdf"),
    path("competition/<int:competition_pk>/summary.pdf", views.summary_pdf, name="summary_pdf"),
]