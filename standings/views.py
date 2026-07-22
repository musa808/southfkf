from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from competitions.models import Competition

from .models import StandingsRow


@login_required
def standings_table(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)

    if competition.has_groups:
        # Group + Knockout: return standings split per group.
        groups = competition.groups.prefetch_related(
            "standings__team__club"
        ).order_by("name")
        return render(
            request,
            "standings/standings_table.html",
            {"competition": competition, "groups": groups, "by_group": True},
        )
    else:
        rows = (
            StandingsRow.objects.filter(competition=competition)
            .select_related("team__club")
            .order_by("-points", "-goals_for", "goals_against")
        )
        return render(
            request,
            "standings/standings_table.html",
            {"competition": competition, "rows": rows, "by_group": False},
        )