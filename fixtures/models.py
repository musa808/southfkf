from django.db import models

from competitions.models import Competition, CompetitionTeam, Group, KnockoutFixture


class Fixture(models.Model):
    """
    A single scheduled match. Used for:
    - League fixtures (round-robin, generated automatically)
    - Group-stage fixtures within a Group + Knockout competition (also
      round-robin, scoped to one Group)
    - Knockout fixtures (created manually by the admin per bracket slot)

    `knockout_fixture` links back to the bracket slot (competitions.KnockoutFixture)
    when this Fixture represents a knockout tie. It's null for league/group fixtures.
    `leg` distinguishes first/second leg when a knockout competition uses
    two-legged ties, or first/second meeting in a double round-robin league.
    """

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        PLAYED = "PLAYED", "Played"
        POSTPONED = "POSTPONED", "Postponed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Leg(models.IntegerChoices):
        """
        For single matches (most league rounds, most knockout ties), use FIRST.
        SECOND is only used for the return leg of a double round-robin
        league fixture or a two-legged knockout tie.
        """
        FIRST = 1, "First leg"
        SECOND = 2, "Second leg"

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="fixtures")
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, null=True, blank=True, related_name="fixtures",
        help_text="Set only for group-stage fixtures within a Group + Knockout competition.",
    )
    knockout_fixture = models.OneToOneField(
        KnockoutFixture, on_delete=models.CASCADE, null=True, blank=True, related_name="match",
        help_text="Set only when this fixture fulfils a knockout bracket slot.",
    )

    home_team = models.ForeignKey(
        CompetitionTeam, on_delete=models.CASCADE, related_name="home_fixtures"
    )
    away_team = models.ForeignKey(
        CompetitionTeam, on_delete=models.CASCADE, related_name="away_fixtures"
    )

    round_number = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="League/group round number, e.g. Matchday 1, 2, 3..."
    )
    leg = models.PositiveSmallIntegerField(choices=Leg.choices, default=Leg.FIRST)

    match_date = models.DateField(null=True, blank=True)
    kickoff_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=150, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["match_date", "kickoff_time", "id"]

    def __str__(self):
        date = self.match_date.strftime("%d %b %Y") if self.match_date else "TBD"
        return f"{self.home_team.club.name} vs {self.away_team.club.name} ({date})"

    @property
    def is_knockout(self):
        return self.knockout_fixture_id is not None

    @property
    def is_group_stage(self):
        return self.group_id is not None

    @property
    def is_league(self):
        return self.group_id is None and self.knockout_fixture_id is None