"""
Standings recalculation engine.

Called after every MatchResult save or delete. Rebuilds ALL StandingsRow
entries for a competition from scratch — simple, always correct, and fast
enough for sub-county scale (dozens of matches, not thousands).

Only League and Group-stage fixtures count toward standings.
Knockout fixtures and Friendly competitions are excluded.
"""

from competitions.models import Competition, CompetitionTeam
from fixtures.models import Fixture

from .models import StandingsRow


def recalculate_standings(competition: Competition):
    """
    Delete and recreate all StandingsRow entries for this competition.
    Safe to call multiple times — always produces the correct final state.
    """
    if not competition.affects_standings:
        # Friendly competitions never affect standings — bail early.
        return

    # ---------------------------------------------------------------
    # Step 1: Reset all standings rows for this competition.
    # ---------------------------------------------------------------
    StandingsRow.objects.filter(competition=competition).delete()

    # Create a blank row for every entered team.
    teams = list(
        CompetitionTeam.objects.filter(
            competition=competition, status=CompetitionTeam.Status.ENTERED
        ).select_related("club")
    )
    rows = {}  # team.pk → StandingsRow instance (in memory, not yet saved)

    for team in teams:
        group_entry = team.group_placement.first()  # GroupTeam, or None for league
        rows[team.pk] = StandingsRow(
            competition=competition,
            group=group_entry.group if group_entry else None,
            team=team,
        )

    # ---------------------------------------------------------------
    # Step 2: Walk every played fixture that counts for standings.
    # ---------------------------------------------------------------
    # For League competitions: all fixtures not linked to a group/knockout.
    # For Group + Knockout: only the group-stage fixtures (group IS NOT NULL).
    # Knockout-round fixtures never affect league/group standings.
    if competition.competition_type == Competition.CompetitionType.LEAGUE:
        fixture_qs = Fixture.objects.filter(
            competition=competition,
            status=Fixture.Status.PLAYED,
            group__isnull=True,
            knockout_fixture__isnull=True,
        )
    else:
        # GROUP_KNOCKOUT — group stage only
        fixture_qs = Fixture.objects.filter(
            competition=competition,
            status=Fixture.Status.PLAYED,
            group__isnull=False,
        )

    fixture_qs = fixture_qs.select_related(
        "home_team", "away_team", "result"
    )

    pts_win = competition.points_win
    pts_draw = competition.points_draw
    pts_loss = competition.points_loss

    for fixture in fixture_qs:
        if not hasattr(fixture, "result"):
            continue  # Played but result not yet recorded — skip.

        result = fixture.result
        home_pk = fixture.home_team_id
        away_pk = fixture.away_team_id

        if home_pk not in rows or away_pk not in rows:
            continue  # Safety guard for withdrawn/removed teams.

        home_row = rows[home_pk]
        away_row = rows[away_pk]

        hg = result.home_total  # goals incl. extra time
        ag = result.away_total

        home_row.played += 1
        away_row.played += 1
        home_row.goals_for += hg
        home_row.goals_against += ag
        away_row.goals_for += ag
        away_row.goals_against += hg

        if hg > ag:
            home_row.won += 1
            away_row.lost += 1
            home_row.points += pts_win
            away_row.points += pts_loss
        elif ag > hg:
            away_row.won += 1
            home_row.lost += 1
            away_row.points += pts_win
            home_row.points += pts_loss
        else:
            home_row.drawn += 1
            away_row.drawn += 1
            home_row.points += pts_draw
            away_row.points += pts_draw

    # ---------------------------------------------------------------
    # Step 3: Bulk-create all rows in one DB write.
    # ---------------------------------------------------------------
    StandingsRow.objects.bulk_create(rows.values())