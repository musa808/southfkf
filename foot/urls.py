from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from foot.pwa_views import service_worker, offline  # adjust import path if you placed these elsewhere

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("clubs/", include("clubs.urls")),
    path("", include("dashboard.urls")),
    path("players/", include("players.urls")),
    path("coaches/", include("coaches.urls")),
    path("referees/", include("referees.urls")),
    path("seasons/", include("seasons.urls")),
    path("competitions/", include("competitions.urls")),
    path("fixtures/", include("fixtures.urls")),
    path("results/", include("results.urls")),
    path("standings/", include("standings.urls")),
    path("reports/", include("reports.urls")),
    path("transfers/", include("transfers.urls")),
    path("lineups/", include("lineups.urls")),
    path("service-worker.js", service_worker, name="service-worker"),
    path("offline/", offline, name="offline"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)