from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from competitions.models import Competition

from .pdf import (
    generate_competition_summary_pdf,
    generate_fixture_list_pdf,
    generate_standings_pdf,
    generate_top_scorers_pdf,
)


def _pdf_response(buffer, filename):
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def reports_home(request):
    """Landing page listing all competitions — user picks one to see its reports."""
    competitions = Competition.objects.select_related("season").order_by(
        "-season__start_date", "name"
    )
    return render(request, "reports/reports_home.html", {"competitions": competitions})


@login_required
def report_index(request, competition_pk):
    """Landing page listing all available reports for a specific competition."""
    competition = get_object_or_404(Competition, pk=competition_pk)
    return render(request, "reports/report_index.html", {"competition": competition})


@login_required
def fixture_list_pdf(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)
    buffer = generate_fixture_list_pdf(competition)
    filename = f"fixtures_{competition.name.replace(' ', '_')}.pdf"
    return _pdf_response(buffer, filename)


@login_required
def standings_pdf(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)
    if not competition.affects_standings:
        messages.error(request, "Friendly competitions don't have standings.")
        return redirect("reports:index", competition_pk=competition_pk)
    buffer = generate_standings_pdf(competition)
    filename = f"standings_{competition.name.replace(' ', '_')}.pdf"
    return _pdf_response(buffer, filename)


@login_required
def top_scorers_pdf(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)
    buffer = generate_top_scorers_pdf(competition)
    filename = f"top_scorers_{competition.name.replace(' ', '_')}.pdf"
    return _pdf_response(buffer, filename)


@login_required
def summary_pdf(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)
    buffer = generate_competition_summary_pdf(competition)
    filename = f"summary_{competition.name.replace(' ', '_')}.pdf"
    return _pdf_response(buffer, filename)