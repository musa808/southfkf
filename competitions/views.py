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