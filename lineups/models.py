from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from competitions.models import CompetitionTeam
from fixtures.models import Fixture
from players.models import Player


class Lineup(models.Model):
    """
    A submitted lineup for one team in a fixture.
    Each fixture has up to 2 lineups — one per team.
    Editable until the fixture kickoff time.
    """

    class Formation(models.TextChoices):
        F433  = "4-3-3",   "4-3-3"
        F442  = "4-4-2",   "4-4-2"
        F4231 = "4-2-3-1", "4-2-3-1"
        F352  = "3-5-2",   "3-5-2"
        F532  = "5-3-2",   "5-3-2"
        F451  = "4-5-1",   "4-5-1"
        F343  = "3-4-3",   "3-4-3"
        F541  = "5-4-1",   "5-4-1"

    fixture = models.ForeignKey(
        Fixture, on_delete=models.CASCADE, related_name="lineups"
    )
    team = models.ForeignKey(
        CompetitionTeam, on_delete=models.CASCADE, related_name="lineups"
    )
    formation = models.CharField(
        max_length=10, choices=Formation.choices, default=Formation.F433
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional tactical notes (visible to Sub-County Admin).",
    )
    submitted_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_lineups",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One lineup per team per fixture
        unique_together = ("fixture", "team")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.team.club.name} lineup — {self.fixture}"

    @property
    def starters(self):
        return self.players.filter(role=LineupPlayer.Role.STARTER).select_related("player")

    @property
    def substitutes(self):
        return self.players.filter(role=LineupPlayer.Role.SUBSTITUTE).select_related("player")

    @property
    def captain(self):
        return self.players.filter(is_captain=True).select_related("player").first()

    @property
    def is_editable(self):
        """Lineup is editable until fixture kickoff time (or all day if no kickoff time set)."""
        fixture = self.fixture
        if not fixture.match_date:
            return True
        now = timezone.localtime()
        if fixture.kickoff_time:
            from datetime import datetime
            kickoff = timezone.make_aware(
                datetime.combine(fixture.match_date, fixture.kickoff_time)
            )
            return now < kickoff
        # No kickoff time set — editable until end of match day
        from datetime import datetime, time
        end_of_day = timezone.make_aware(
            datetime.combine(fixture.match_date, time(23, 59))
        )
        return now < end_of_day

    @property
    def starter_count(self):
        return self.players.filter(role=LineupPlayer.Role.STARTER).count()

    @property
    def sub_count(self):
        return self.players.filter(role=LineupPlayer.Role.SUBSTITUTE).count()

    @property
    def is_complete(self):
        return self.starter_count == 11

    def clean(self):
        # On initial creation the instance has no pk yet, so the reverse
        # `players` relationship can't be queried. The view performs the
        # authoritative starters/subs/captain validation itself after the
        # LineupPlayer rows are built — this check only re-validates an
        # already-saved lineup (e.g. if something edits LineupPlayer rows
        # directly, outside the normal submit flow).
        if not self.pk:
            return

        starters = self.players.filter(role=LineupPlayer.Role.STARTER).count()
        subs = self.players.filter(role=LineupPlayer.Role.SUBSTITUTE).count()
        captains = self.players.filter(is_captain=True).count()
        if starters > 11:
            raise ValidationError("A lineup cannot have more than 11 starters.")
        if subs > 7:
            raise ValidationError("A lineup cannot have more than 7 substitutes.")
        if captains > 1:
            raise ValidationError("Only one player can be captain.")


class LineupPlayer(models.Model):
    """
    A single player entry within a lineup.
    Tracks their role (starter/sub), whether they're captain,
    and their position label within the formation.
    """

    class Role(models.TextChoices):
        STARTER    = "STARTER",    "Starter"
        SUBSTITUTE = "SUBSTITUTE", "Substitute"

    lineup   = models.ForeignKey(Lineup, on_delete=models.CASCADE, related_name="players")
    player   = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="lineup_appearances")
    role     = models.CharField(max_length=12, choices=Role.choices, default=Role.STARTER)
    is_captain = models.BooleanField(default=False)
    shirt_number = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Override jersey number for this match (optional).",
    )
    position_label = models.CharField(
        max_length=30, blank=True,
        help_text='e.g. "Left Wing", "Centre Back", "Defensive Midfielder"',
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order within starters or subs.",
    )

    class Meta:
        unique_together = ("lineup", "player")
        ordering = ["role", "order", "shirt_number"]

    def __str__(self):
        captain_str = " (C)" if self.is_captain else ""
        return f"{self.player.full_name}{captain_str} — {self.get_role_display()}"