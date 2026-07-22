"""
Round-robin fixture generation using the standard "circle method".

Used for:
- League competitions (all entered teams)
- Group-stage fixtures within a Group + Knockout competition (scoped per group)

The circle method: arrange teams in two rows, fix one team, rotate the
rest each round. Handles odd numbers of teams by adding a "bye" — the
team paired with the bye sits out that round.
"""

import datetime

from .models import Fixture


def generate_round_robin_pairings(teams):
    """
    Given a list of team objects (CompetitionTeam instances), return a list
    of rounds, where each round is a list of (home, away) tuples.

    Uses the circle method. If len(teams) is odd, a None "bye" placeholder
    is added so the algorithm works uniformly; bye pairings are filtered
    out by the caller.
    """
    teams = list(teams)
    if len(teams) < 2:
        return []

    has_bye = len(teams) % 2 == 1
    if has_bye:
        teams.append(None)

    n = len(teams)
    rounds = []
    fixed = teams[0]
    rotating = teams[1:]

    for round_index in range(n - 1):
        round_teams = [fixed] + rotating
        pairings = []
        for i in range(n // 2):
            home, away = round_teams[i], round_teams[n - 1 - i]
            # Alternate home/away advantage across rounds so one team
            # doesn't always play "home" against the same opponent.
            if round_index % 2 == 1:
                home, away = away, home
            if home is not None and away is not None:
                pairings.append((home, away))
        rounds.append(pairings)
        # Rotate: move the last element of `rotating` to the front.
        rotating = [rotating[-1]] + rotating[:-1]

    return rounds


def create_league_fixtures(competition, teams, start_date, days_between_rounds=7, venue=""):
    """
    Generates and saves Fixture rows for a League competition.
    Respects `competition.double_round_robin` to optionally create the
    return-leg fixtures (home/away reversed) as a second block of rounds.

    Returns the list of created Fixture objects.
    """
    rounds = generate_round_robin_pairings(teams)
    created = []
    current_date = start_date

    for round_index, pairings in enumerate(rounds, start=1):
        for home, away in pairings:
            created.append(
                Fixture(
                    competition=competition,
                    home_team=home,
                    away_team=away,
                    round_number=round_index,
                    leg=Fixture.Leg.FIRST,
                    match_date=current_date,
                    venue=venue,
                )
            )
        current_date += datetime.timedelta(days=days_between_rounds)

    if competition.double_round_robin:
        second_leg_start_round = len(rounds) + 1
        for round_index, pairings in enumerate(rounds, start=second_leg_start_round):
            for home, away in pairings:
                # Reverse home/away for the return fixture.
                created.append(
                    Fixture(
                        competition=competition,
                        home_team=away,
                        away_team=home,
                        round_number=round_index,
                        leg=Fixture.Leg.SECOND,
                        match_date=current_date,
                        venue=venue,
                    )
                )
            current_date += datetime.timedelta(days=days_between_rounds)

    Fixture.objects.bulk_create(created)
    return created


def create_group_stage_fixtures(group, start_date, days_between_rounds=7, venue=""):
    """
    Generates and saves Fixture rows for a single Group's round-robin,
    within a Group + Knockout competition. Always single round-robin
    (groups in sub-county cups don't typically play home/away).
    """
    competition_teams = [gt.competition_team for gt in group.teams.select_related("competition_team__club").all()]
    rounds = generate_round_robin_pairings(competition_teams)
    created = []
    current_date = start_date

    for round_index, pairings in enumerate(rounds, start=1):
        for home, away in pairings:
            created.append(
                Fixture(
                    competition=group.competition,
                    group=group,
                    home_team=home,
                    away_team=away,
                    round_number=round_index,
                    leg=Fixture.Leg.FIRST,
                    match_date=current_date,
                    venue=venue,
                )
            )
        current_date += datetime.timedelta(days=days_between_rounds)

    Fixture.objects.bulk_create(created)
    return created