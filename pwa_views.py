"""
Drop this into an existing app (e.g. dashboard/views.py) or keep as its own
pwa.py file imported from your project urls.py.
"""
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def service_worker(request):
    """
    Serves service-worker.js from the site ROOT (not /static/) so its scope
    covers the whole app. Whitenoise/static serving alone would scope it to
    /static/ only, which isn't enough to control page navigations.
    """
    sw_path = Path(settings.BASE_DIR) / "static" / "js" / "service-worker.js"
    content = sw_path.read_text()
    response = HttpResponse(content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "offline.html")