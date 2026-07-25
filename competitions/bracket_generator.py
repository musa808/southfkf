"""
Generates the empty KnockoutFixture "slots" for each KnockoutRound already
created via setup_knockout_rounds, and wires up feeds_into so winners
advance automatically. Slots start empty (team_a/team_b = None) — teams
are placed afterwards via the drag-and-drop bracket page.

Safe to call more than once: any round that already has fixtures is left
untouched, so adding a round later and re-running only fills the gap.
"""

from .models import Competition, CompetitionTeam, KnockoutFixture, KnockoutRound

# Standard bracket size for each round — how many fixtures happen in that
# round in a full (non-preliminary) bracket.
STANDARD_ROUND_SIZE = {
    KnockoutRound.RoundName.ROUND_OF_32: 16,
    KnockoutRound.RoundName.ROUND_OF_16: 8,
    KnockoutRound.RoundName.QUARTER_FINAL: 4,
    KnockoutRound.RoundName.SEMI_FINAL: 2,
    KnockoutRound.RoundName.FINAL: 1,
}


def generate_bracket_slots(competition: Competition):
    """
    Creates empty KnockoutFixture rows for every KnockoutRound on this
    competition, wiring feeds_into so round N's winners advance into
    round N+1. Returns the list of newly created KnockoutFixture objects
    (empty list if slots already existed for every round).
    """
    rounds = list(
        competition.knockout_rounds.exclude(name=KnockoutRound.RoundName.THIRD_PLACE).order_by("order")
    )
    if not rounds:
        return []

    team_count = CompetitionTeam.objects.filter(
        competition=competition, status=CompetitionTeam.Status.ENTERED
    ).count()

    round_sizes = {}
    first_round = rounds[0]

    if first_round.name == KnockoutRound.RoundName.PRELIMINARY:
        # Preliminary round trims the entered teams down to the size of
        # the next round (e.g. 10 teams -> Quarter Finals(8) means 2
        # preliminary fixtures; the 2 winners join the 6 teams with byes).
        next_size = STANDARD_ROUND_SIZE.get(rounds[1].name, 1) if len(rounds) > 1 else 1
        round_sizes[first_round.pk] = max(team_count - next_size, 0)
    else:
        round_sizes[first_round.pk] = STANDARD_ROUND_SIZE.get(first_round.name, max(team_count // 2, 1))

    prev_size = round_sizes[first_round.pk]
    for rnd in rounds[1:]:
        size = STANDARD_ROUND_SIZE.get(rnd.name, max(prev_size // 2, 1))
        round_sizes[rnd.pk] = size
        prev_size = size

    created = []
    fixtures_by_round = {}

    for rnd in rounds:
        existing = list(rnd.fixtures.order_by("slot_number"))
        if existing:
            fixtures_by_round[rnd.pk] = existing
            continue

        size = round_sizes[rnd.pk]
        KnockoutFixture.objects.bulk_create(
            [KnockoutFixture(round=rnd, slot_number=slot) for slot in range(1, size + 1)]
        )
        # Re-fetch so every fixture has a real pk before we wire feeds_into.
        fixtures_by_round[rnd.pk] = list(rnd.fixtures.order_by("slot_number"))
        created.extend(fixtures_by_round[rnd.pk])

    # Pair (1,2) in round N feeds fixture 1 in round N+1, pair (3,4) feeds
    # fixture 2, and so on.
    for rnd, next_rnd in zip(rounds, rounds[1:]):
        current = fixtures_by_round[rnd.pk]
        upcoming = fixtures_by_round[next_rnd.pk]
        for i, fixture in enumerate(current):
            next_index = i // 2
            if next_index < len(upcoming) and fixture.feeds_into_id is None:
                fixture.feeds_into = upcoming[next_index]
                fixture.save(update_fields=["feeds_into"])

    return created