from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CompetitionForm, TeamEntryForm
from .models import Competition, CompetitionTeam, Group, KnockoutRound


def _can_manage(user):
    """Only Super Admin / Sub-County Admin manage competitions."""
    return user.is_authenticated and (user.is_super_admin or user.is_subcounty_admin)


@login_required
def competition_list(request):
    competitions = Competition.objects.select_related("season").all()
    return render(request, "competitions/competition_list.html", {"competitions": competitions})


@login_required
def competition_detail(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    teams = competition.entered_teams.select_related("club").all()
    groups = competition.groups.prefetch_related("teams__competition_team__club").all() if competition.has_groups else None
    knockout_rounds = (
        competition.knockout_rounds.prefetch_related("fixtures__team_a__club", "fixtures__team_b__club").all()
        if competition.has_knockout_bracket
        else None
    )
    return render(
        request,
        "competitions/competition_detail.html",
        {
            "competition": competition,
            "teams": teams,
            "groups": groups,
            "knockout_rounds": knockout_rounds,
        },
    )


@login_required
@user_passes_test(_can_manage)
def competition_create(request):
    if request.method == "POST":
        form = CompetitionForm(request.POST)
        if form.is_valid():
            competition = form.save()
            messages.success(request, f"{competition.name} created. Now add teams to it.")
            return redirect("competitions:detail", pk=competition.pk)
    else:
        form = CompetitionForm()
    return render(request, "competitions/competition_form.html", {"form": form, "is_create": True})


@login_required
@user_passes_test(_can_manage)
def competition_edit(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    if request.method == "POST":
        form = CompetitionForm(request.POST, instance=competition)
        if form.is_valid():
            form.save()
            messages.success(request, f"{competition.name} updated.")
            return redirect("competitions:detail", pk=competition.pk)
    else:
        form = CompetitionForm(instance=competition)
    return render(
        request,
        "competitions/competition_form.html",
        {"form": form, "is_create": False, "competition": competition},
    )


@login_required
@user_passes_test(_can_manage)
def add_teams(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    if request.method == "POST":
        form = TeamEntryForm(request.POST)
        if form.is_valid():
            created = form.save(competition)
            messages.success(request, f"Added {len(created)} club(s) to {competition.name}.")
            return redirect("competitions:detail", pk=competition.pk)
    else:
        form = TeamEntryForm()
        # Don't re-show clubs already entered.
        already_entered_ids = competition.entered_teams.values_list("club_id", flat=True)
        form.fields["clubs"].queryset = form.fields["clubs"].queryset.exclude(id__in=already_entered_ids)

    return render(request, "competitions/add_teams.html", {"form": form, "competition": competition})


@login_required
@user_passes_test(_can_manage)
def remove_team(request, pk, team_pk):
    competition = get_object_or_404(Competition, pk=pk)
    team = get_object_or_404(CompetitionTeam, pk=team_pk, competition=competition)
    if request.method == "POST":
        club_name = team.club.name
        team.delete()
        messages.success(request, f"{club_name} removed from {competition.name}.")
    return redirect("competitions:detail", pk=competition.pk)


@login_required
@user_passes_test(_can_manage)
def setup_groups(request, pk):
    """
    Creates the group skeleton (Group A, Group B, ...) for a
    Group + Knockout competition. Assigning teams into groups happens
    separately in the admin or a later phase's drag-and-drop UI.
    """
    competition = get_object_or_404(Competition, pk=pk)
    if not competition.has_groups:
        messages.error(request, f"{competition.get_competition_type_display()} competitions don't use groups.")
        return redirect("competitions:detail", pk=competition.pk)

    if request.method == "POST":
        try:
            num_groups = int(request.POST.get("num_groups", 0))
        except ValueError:
            num_groups = 0

        if num_groups < 2:
            messages.error(request, "Enter at least 2 groups.")
        else:
            existing = competition.groups.count()
            for i in range(existing, existing + num_groups):
                letter = chr(ord("A") + i)
                Group.objects.get_or_create(competition=competition, name=f"Group {letter}")
            messages.success(request, f"Created {num_groups} group(s).")
        return redirect("competitions:detail", pk=competition.pk)

    return render(request, "competitions/setup_groups.html", {"competition": competition})


# Rounds offered depend on how many teams a sub-county competition realistically has.
ROUND_CHOICES = [
    (KnockoutRound.RoundName.PRELIMINARY, KnockoutRound.RoundName.PRELIMINARY.label, 1),
    (KnockoutRound.RoundName.ROUND_OF_32, KnockoutRound.RoundName.ROUND_OF_32.label, 2),
    (KnockoutRound.RoundName.ROUND_OF_16, KnockoutRound.RoundName.ROUND_OF_16.label, 3),
    (KnockoutRound.RoundName.QUARTER_FINAL, KnockoutRound.RoundName.QUARTER_FINAL.label, 4),
    (KnockoutRound.RoundName.SEMI_FINAL, KnockoutRound.RoundName.SEMI_FINAL.label, 5),
    (KnockoutRound.RoundName.FINAL, KnockoutRound.RoundName.FINAL.label, 6),
]


@login_required
@user_passes_test(_can_manage)
def setup_knockout_rounds(request, pk):
    """
    Creates the knockout round skeleton chosen by the admin (e.g. just
    Semi Finals + Final for a small competition). Fixture slots within
    each round, and auto-pairing teams into them, is Phase 3.
    """
    competition = get_object_or_404(Competition, pk=pk)
    if not competition.has_knockout_bracket:
        messages.error(request, f"{competition.get_competition_type_display()} competitions don't use a knockout bracket.")
        return redirect("competitions:detail", pk=competition.pk)

    if request.method == "POST":
        selected = request.POST.getlist("rounds")
        if not selected:
            messages.error(request, "Select at least one round.")
        else:
            for round_name, round_label, order in ROUND_CHOICES:
                if round_name in selected:
                    KnockoutRound.objects.get_or_create(
                        competition=competition, name=round_name, defaults={"order": order}
                    )
            if competition.has_third_place_playoff and KnockoutRound.RoundName.SEMI_FINAL in selected:
                KnockoutRound.objects.get_or_create(
                    competition=competition,
                    name=KnockoutRound.RoundName.THIRD_PLACE,
                    defaults={"order": 5},
                )
            messages.success(request, "Knockout rounds created.")
        return redirect("competitions:detail", pk=competition.pk)

    return render(
        request,
        "competitions/setup_knockout_rounds.html",
        {"competition": competition, "round_choices": ROUND_CHOICES},
    )
from django.db import models as db_models
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from fixtures.models import Fixture

from .bracket_generator import generate_bracket_slots
from .models import KnockoutFixture  # add to your existing models import


@login_required
@user_passes_test(_can_manage)
def generate_bracket_slots_view(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    if not competition.has_knockout_bracket:
        messages.error(request, "This competition doesn't use a knockout bracket.")
        return redirect("competitions:detail", pk=competition.pk)

    if not competition.knockout_rounds.exists():
        messages.error(request, "Set up knockout rounds first.")
        return redirect("competitions:detail", pk=competition.pk)

    created = generate_bracket_slots(competition)
    if created:
        messages.success(request, f"Generated {len(created)} bracket slot(s).")
    else:
        messages.info(request, "Bracket slots already exist for every round.")
    return redirect("competitions:bracket", competition_pk=competition.pk)


@login_required
def bracket_view(request, competition_pk):
    competition = get_object_or_404(Competition, pk=competition_pk)

    if not competition.has_knockout_bracket:
        messages.error(request, "This competition doesn't have a knockout bracket.")
        return redirect("competitions:detail", pk=competition.pk)

    rounds = competition.knockout_rounds.prefetch_related(
        db_models.Prefetch(
            "fixtures",
            queryset=KnockoutFixture.objects.select_related(
                "team_a__club", "team_b__club", "winner__club", "match"
            ).order_by("slot_number"),
        )
    ).order_by("order")

    assigned_team_ids = set()
    for rnd in rounds:
        for kf in rnd.fixtures.all():
            if kf.team_a_id:
                assigned_team_ids.add(kf.team_a_id)
            if kf.team_b_id:
                assigned_team_ids.add(kf.team_b_id)

    unassigned_teams = (
        CompetitionTeam.objects.filter(competition=competition, status=CompetitionTeam.Status.ENTERED)
        .exclude(pk__in=assigned_team_ids)
        .select_related("club")
        .order_by("club__name")
    )

    return render(
        request,
        "competitions/bracket.html",
        {
            "competition": competition,
            "rounds": rounds,
            "unassigned_teams": unassigned_teams,
            "can_manage": _can_manage(request.user),
        },
    )


def _slot_is_locked(knockout_fixture):
    return hasattr(knockout_fixture, "match") and knockout_fixture.match.status == Fixture.Status.PLAYED


@login_required
@user_passes_test(_can_manage)
@require_POST
def bracket_assign_slot(request, fixture_pk):
    knockout_fixture = get_object_or_404(
        KnockoutFixture.objects.select_related("round__competition"), pk=fixture_pk
    )
    competition = knockout_fixture.round.competition

    slot = request.POST.get("slot")
    team_id = request.POST.get("team_id")
    if slot not in ("a", "b"):
        return JsonResponse({"error": "Invalid slot."}, status=400)
    if _slot_is_locked(knockout_fixture):
        return JsonResponse({"error": "This tie has already been played."}, status=400)

    team = get_object_or_404(CompetitionTeam, pk=team_id, competition=competition)
    if slot == "a":
        knockout_fixture.team_a = team
    else:
        knockout_fixture.team_b = team
    knockout_fixture.save(update_fields=["team_a", "team_b"])

    if knockout_fixture.team_a and knockout_fixture.team_b:
        Fixture.objects.update_or_create(
            knockout_fixture=knockout_fixture,
            defaults={
                "competition": competition,
                "home_team": knockout_fixture.team_a,
                "away_team": knockout_fixture.team_b,
            },
        )
    return JsonResponse({"ok": True})


@login_required
@user_passes_test(_can_manage)
@require_POST
def bracket_clear_slot(request, fixture_pk):
    knockout_fixture = get_object_or_404(KnockoutFixture, pk=fixture_pk)
    if _slot_is_locked(knockout_fixture):
        return JsonResponse({"error": "This tie has already been played."}, status=400)

    slot = request.POST.get("slot")
    if slot not in ("a", "b"):
        return JsonResponse({"error": "Invalid slot."}, status=400)

    if slot == "a":
        knockout_fixture.team_a = None
    else:
        knockout_fixture.team_b = None
    knockout_fixture.save(update_fields=["team_a", "team_b"])
    Fixture.objects.filter(knockout_fixture=knockout_fixture).delete()
    return JsonResponse({"ok": True})