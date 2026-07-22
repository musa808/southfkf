"""
Signal handlers for the results app.

On every MatchResult save or delete:
1. Recalculate standings for the competition (league/group stage only).
2. If the fixture is a knockout match, auto-advance the winner to the
   next bracket slot (feeds_into on KnockoutFixture).
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from competitions.models import KnockoutFixture
from standings.calculator import recalculate_standings

from .models import MatchResult


@receiver(post_save, sender=MatchResult)
def on_result_saved(sender, instance, **kwargs):
    _handle_result_change(instance)


@receiver(post_delete, sender=MatchResult)
def on_result_deleted(sender, instance, **kwargs):
    _handle_result_change(instance)


def _handle_result_change(result: MatchResult):
    competition = result.fixture.competition

    # --- 1. Standings ---
    recalculate_standings(competition)

    # --- 2. Knockout advancement ---
    fixture = result.fixture
    if not fixture.is_knockout:
        return  # League/group fixtures don't feed into bracket slots.

    knockout_fixture = fixture.knockout_fixture
    winner = result.determine_winner()

    # Record winner on the bracket slot.
    knockout_fixture.winner = winner
    knockout_fixture.save(update_fields=["winner"])

    if winner is None:
        return  # Draw — valid only in a two-legged tie aggregate sense;
                # for now we don't auto-advance on draws.

    next_slot: KnockoutFixture | None = knockout_fixture.feeds_into
    if next_slot is None:
        return  # Final or Third Place — no "next" round to advance to.

    # Place the winner into the first empty slot of the next fixture.
    if next_slot.team_a is None:
        next_slot.team_a = winner
        next_slot.save(update_fields=["team_a"])
    elif next_slot.team_b is None:
        next_slot.team_b = winner
        next_slot.save(update_fields=["team_b"])
    # If both slots are already filled (e.g. result was corrected), leave as-is
    # and let the admin adjust manually via the assign_knockout_slot view.