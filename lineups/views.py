from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from competitions.models import CompetitionTeam
from fixtures.models import Fixture
from players.models import Player

from .forms import LineupForm, LineupPlayerForm, build_lineup_player_forms
from .models import Lineup, LineupPlayer


# ── Permission helper ─────────────────────────────────────────────────────────

def _can_submit_for_team(user, team):
    """
    Club Admin of the team's club can submit.
    Sub-County Admin / Super Admin can submit for any team.
    """
    if user.is_super_admin or user.is_subcounty_admin:
        return True
    return user.is_club_admin and user.club == team.club


def _squad_data(squad):
    """Serializable squad list for the pitch picker JS."""
    return [
        {
            "id": player.id,
            "name": player.full_name,
            "number": player.jersey_number,
            "position": player.get_position_display(),
        }
        for player in squad
    ]


def _assignments_from_forms(player_forms):
    """
    Build a {player_id: {role, is_captain, shirt_number, position_label}}
    dict from the current player_forms (bound POST data or unbound initial
    data), so the pitch UI can restore state on both GET and a failed POST.
    """
    data = {}
    for player, pf in player_forms:
        if pf.is_bound:
            role = pf.data.get(pf.add_prefix("role"), "")
            raw_captain = pf.data.get(pf.add_prefix("is_captain"))
            is_captain = raw_captain in ("on", "true", "True", True)
            shirt = pf.data.get(pf.add_prefix("shirt_number")) or None
            position_label = pf.data.get(pf.add_prefix("position_label"), "")
        else:
            role = pf.initial.get("role", "")
            is_captain = bool(pf.initial.get("is_captain", False))
            shirt = pf.initial.get("shirt_number")
            position_label = pf.initial.get("position_label", "")

        if role:
            data[str(player.id)] = {
                "role": role,
                "is_captain": bool(is_captain),
                "shirt_number": shirt,
                "position_label": position_label,
            }
    return data


# ── Lineups landing page ──────────────────────────────────────────────────────

@login_required
def lineups_home(request):
    user = request.user

    fixtures_qs = Fixture.objects.select_related(
        "competition", "home_team__club", "away_team__club"
    ).order_by("match_date")

    if user.is_super_admin or user.is_subcounty_admin:
        fixtures = fixtures_qs
    elif user.is_club_admin:
        fixtures = fixtures_qs.filter(
            Q(home_team__club=user.club) | Q(away_team__club=user.club)
        )
    else:
        fixtures = fixtures_qs.none()

    rows = []
    for fixture in fixtures:
        for team in (fixture.home_team, fixture.away_team):
            if _can_submit_for_team(user, team):
                lineup = Lineup.objects.filter(fixture=fixture, team=team).first()
                rows.append({
                    "fixture": fixture,
                    "team": team,
                    "lineup": lineup,
                    "editable": (not lineup) or lineup.is_editable,
                })

    return render(request, "lineups/home.html", {"rows": rows})


# ── Submit / edit lineup ──────────────────────────────────────────────────────

@login_required
def submit_lineup(request, fixture_pk, team_pk):
    fixture = get_object_or_404(
        Fixture.objects.select_related(
            "competition", "home_team__club", "away_team__club"
        ),
        pk=fixture_pk,
    )
    team = get_object_or_404(CompetitionTeam, pk=team_pk)

    # Only the team's club admin (or higher) can submit
    if not _can_submit_for_team(request.user, team):
        messages.error(request, "You don't have permission to submit this lineup.")
        return redirect("lineups:fixture_lineups", fixture_pk=fixture_pk)

    # Get or prepare existing lineup
    existing_lineup = Lineup.objects.filter(fixture=fixture, team=team).first()

    # Check if fixture has passed kickoff — block edits
    if existing_lineup and not existing_lineup.is_editable:
        messages.warning(
            request,
            "The kickoff time has passed. This lineup can no longer be edited.",
        )
        return redirect("lineups:fixture_lineups", fixture_pk=fixture_pk)

    # Squad = active players registered to this club
    squad = Player.objects.filter(
        club=team.club, status=Player.Status.ACTIVE
    ).order_by("last_name", "first_name")

    if request.method == "POST":
        lineup_form = LineupForm(request.POST, instance=existing_lineup)
        player_forms = []
        for player in squad:
            pf = LineupPlayerForm(
                request.POST,
                prefix=f"p{player.id}",
            )
            player_forms.append((player, pf))

        # Validate
        all_valid = lineup_form.is_valid() and all(pf.is_valid() for _, pf in player_forms)

        if all_valid:
            # Collect selected players
            starters   = []
            subs       = []
            captain_id = None

            for player, pf in player_forms:
                role = pf.cleaned_data.get("role")
                if not role:
                    continue
                entry = {
                    "player":         player,
                    "role":           role,
                    "is_captain":     pf.cleaned_data.get("is_captain", False),
                    "shirt_number":   pf.cleaned_data.get("shirt_number"),
                    "position_label": pf.cleaned_data.get("position_label", ""),
                }
                if role == LineupPlayer.Role.STARTER:
                    starters.append(entry)
                else:
                    subs.append(entry)
                if entry["is_captain"]:
                    captain_id = player.id

            # ── Validation rules ──────────────────────────────────────────────
            errors = []
            if len(starters) != 11:
                errors.append(f"Select exactly 11 starters (you selected {len(starters)}).")
            if len(subs) > 7:
                errors.append(f"Maximum 7 substitutes allowed (you selected {len(subs)}).")
            captains = [e for e in starters + subs if e["is_captain"]]
            if len(captains) == 0:
                errors.append("Designate one player as captain.")
            elif len(captains) > 1:
                errors.append("Only one player can be captain.")

            if errors:
                for e in errors:
                    messages.error(request, e)
            else:
                # Save lineup header
                lineup = lineup_form.save(commit=False)
                lineup.fixture = fixture
                lineup.team = team
                lineup.submitted_by = request.user
                lineup.save()

                # Clear old player entries and rebuild
                lineup.players.all().delete()
                for i, entry in enumerate(starters + subs):
                    LineupPlayer.objects.create(
                        lineup=lineup,
                        player=entry["player"],
                        role=entry["role"],
                        is_captain=entry["is_captain"],
                        shirt_number=entry["shirt_number"],
                        position_label=entry["position_label"],
                        order=i,
                    )

                messages.success(
                    request,
                    f"Lineup for {team.club.name} submitted successfully!",
                )
                return redirect("lineups:fixture_lineups", fixture_pk=fixture_pk)

        # Re-build player forms with POST data for re-render
        player_forms_display = [
            (p, LineupPlayerForm(request.POST, prefix=f"p{p.id}"))
            for p in squad
        ]

    else:
        lineup_form = LineupForm(instance=existing_lineup)
        player_forms_display = build_lineup_player_forms(squad, existing_lineup)

    return render(request, "lineups/submit_lineup.html", {
        "fixture":        fixture,
        "team":           team,
        "lineup_form":    lineup_form,
        "player_forms":   player_forms_display,
        "existing_lineup": existing_lineup,
        "squad_count":    squad.count(),
        "squad_data":     _squad_data(squad),
        "initial_assignments": _assignments_from_forms(player_forms_display),
    })


# ── View both lineups for a fixture ──────────────────────────────────────────

@login_required
def fixture_lineups(request, fixture_pk):
    fixture = get_object_or_404(
        Fixture.objects.select_related(
            "competition",
            "home_team__club",
            "away_team__club",
        ),
        pk=fixture_pk,
    )

    home_lineup = Lineup.objects.filter(
        fixture=fixture, team=fixture.home_team
    ).prefetch_related("players__player").first()

    away_lineup = Lineup.objects.filter(
        fixture=fixture, team=fixture.away_team
    ).prefetch_related("players__player").first()

    user = request.user
    can_submit_home = _can_submit_for_team(user, fixture.home_team)
    can_submit_away = _can_submit_for_team(user, fixture.away_team)

    return render(request, "lineups/fixture_lineups.html", {
        "fixture":         fixture,
        "home_lineup":     home_lineup,
        "away_lineup":     away_lineup,
        "can_submit_home": can_submit_home,
        "can_submit_away": can_submit_away,
    })