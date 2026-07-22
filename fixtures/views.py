from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from competitions.models import Competition, CompetitionTeam, Group, KnockoutFixture

from .forms import (
    FixtureEditForm,
    GenerateGroupFixturesForm,
    GenerateLeagueFixturesForm,
    KnockoutFixtureScheduleForm,
    KnockoutSlotTeamsForm,
)
from .generator import create_group_stage_fixtures, create_league_fixtures
from .models import Fixture


def _can_manage(user):
    return user.is_authenticated and (user.is_super_admin or user.is_subcounty_admin)


@login_required
def fixture_list(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)
    fixtures = (
        competition.fixtures.select_related("home_team__club", "away_team__club", "group", "knockout_fixture__round")
        .order_by("match_date", "kickoff_time")
    )
    return render(
        request,
        "fixtures/fixture_list.html",
        {"competition": competition, "fixtures": fixtures},
    )


@login_required
@user_passes_test(_can_manage)
def generate_league(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)

    if competition.competition_type != Competition.CompetitionType.LEAGUE:
        messages.error(request, "Fixture auto-generation here is for League competitions only.")
        return redirect("competitions:detail", pk=competition.pk)

    if competition.fixtures.filter(group__isnull=True, knockout_fixture__isnull=True).exists():
        messages.warning(
            request,
            "League fixtures already exist for this competition. Delete them first (via Django Admin) "
            "if you want to regenerate.",
        )
        return redirect("competitions:detail", pk=competition.pk)

    teams = list(
        CompetitionTeam.objects.filter(
            competition=competition, status=CompetitionTeam.Status.ENTERED
        ).select_related("club")
    )

    if len(teams) < 2:
        messages.error(request, "At least 2 entered teams are needed to generate fixtures.")
        return redirect("competitions:detail", pk=competition.pk)

    if request.method == "POST":
        form = GenerateLeagueFixturesForm(request.POST)
        if form.is_valid():
            created = create_league_fixtures(
                competition=competition,
                teams=teams,
                start_date=form.cleaned_data["start_date"],
                days_between_rounds=form.cleaned_data["days_between_rounds"],
                venue=form.cleaned_data["venue"],
            )
            messages.success(request, f"Generated {len(created)} fixtures.")
            return redirect("fixtures:list", competition_pk=competition.pk)
    else:
        form = GenerateLeagueFixturesForm()

    return render(
        request,
        "fixtures/generate_league.html",
        {"form": form, "competition": competition, "team_count": len(teams)},
    )


@login_required
@user_passes_test(_can_manage)
def generate_group(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    competition = group.competition

    if group.fixtures.exists():
        messages.warning(
            request,
            f"Fixtures already exist for {group.name}. Delete them first (via Django Admin) to regenerate.",
        )
        return redirect("competitions:detail", pk=competition.pk)

    team_count = group.teams.count()
    if team_count < 2:
        messages.error(request, f"{group.name} needs at least 2 teams assigned before generating fixtures.")
        return redirect("competitions:detail", pk=competition.pk)

    if request.method == "POST":
        form = GenerateGroupFixturesForm(request.POST)
        if form.is_valid():
            created = create_group_stage_fixtures(
                group=group,
                start_date=form.cleaned_data["start_date"],
                days_between_rounds=form.cleaned_data["days_between_rounds"],
                venue=form.cleaned_data["venue"],
            )
            messages.success(request, f"Generated {len(created)} fixtures for {group.name}.")
            return redirect("fixtures:list", competition_pk=competition.pk)
    else:
        form = GenerateGroupFixturesForm()

    return render(
        request,
        "fixtures/generate_group.html",
        {"form": form, "group": group, "competition": competition, "team_count": team_count},
    )


@login_required
@user_passes_test(_can_manage)
def assign_knockout_slot(request, knockout_fixture_pk):
    """
    Lets the admin pick team A / team B for a bracket slot, then creates
    (or updates) the linked Fixture so it shows up in the schedule and,
    later, can have a result recorded against it.
    """
    knockout_fixture = get_object_or_404(KnockoutFixture, pk=knockout_fixture_pk)
    competition = knockout_fixture.round.competition

    if request.method == "POST":
        form = KnockoutSlotTeamsForm(request.POST, competition=competition)
        if form.is_valid():
            knockout_fixture.team_a = form.cleaned_data["team_a"]
            knockout_fixture.team_b = form.cleaned_data["team_b"]
            knockout_fixture.save()

            # Create the underlying Fixture once both teams are known
            # (or update it if the teams changed, e.g. one was re-assigned).
            if knockout_fixture.team_a and knockout_fixture.team_b:
                Fixture.objects.update_or_create(
                    knockout_fixture=knockout_fixture,
                    defaults={
                        "competition": competition,
                        "home_team": knockout_fixture.team_a,
                        "away_team": knockout_fixture.team_b,
                    },
                )
            messages.success(request, "Bracket slot updated.")
            return redirect("competitions:detail", pk=competition.pk)
    else:
        initial = {"team_a": knockout_fixture.team_a, "team_b": knockout_fixture.team_b}
        form = KnockoutSlotTeamsForm(competition=competition, initial=initial)

    return render(
        request,
        "fixtures/assign_knockout_slot.html",
        {"form": form, "knockout_fixture": knockout_fixture, "competition": competition},
    )


@login_required
@user_passes_test(_can_manage)
def fixture_edit(request, pk):
    fixture = get_object_or_404(Fixture, pk=pk)

    # Knockout fixtures get the schedule-only form (teams are edited via
    # the bracket slot, not here) so the two screens don't fight each other.
    form_class = KnockoutFixtureScheduleForm if fixture.is_knockout else FixtureEditForm

    if request.method == "POST":
        form = form_class(request.POST, instance=fixture)
        if form.is_valid():
            form.save()
            messages.success(request, "Fixture updated.")
            return redirect("fixtures:list", competition_pk=fixture.competition_id)
    else:
        form = form_class(instance=fixture)

    return render(request, "fixtures/fixture_edit.html", {"form": form, "fixture": fixture})