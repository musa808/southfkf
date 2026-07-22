from django.db import models

from clubs.models import Club
from seasons.models import Season


class Competition(models.Model):
    """
    A single competition within a Season, e.g. "Garbatulla Sub-County League 2026"
    or "Garbatulla Cup 2026". Holds the format rules; actual fixtures/results
    live in their own apps (Phase 3+).
    """

    class CompetitionType(models.TextChoices):
        LEAGUE = "LEAGUE", "League"
        KNOCKOUT = "KNOCKOUT", "Knockout"
        GROUP_KNOCKOUT = "GROUP_KNOCKOUT", "Group + Knockout"
        FRIENDLY = "FRIENDLY", "Friendly"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REGISTRATION = "REGISTRATION", "Registration Open"
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"

    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="competitions")
    name = models.CharField(max_length=150, help_text='e.g. "Garbatulla Sub-County League"')
    competition_type = models.CharField(max_length=20, choices=CompetitionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # League-specific settings. Ignored for other types.
    double_round_robin = models.BooleanField(
        default=False,
        help_text="League only: teams play each other twice (home & away) instead of once.",
    )
    points_win = models.PositiveSmallIntegerField(default=3)
    points_draw = models.PositiveSmallIntegerField(default=1)
    points_loss = models.PositiveSmallIntegerField(default=0)

    # Knockout-specific settings. Ignored for league/friendly.
    two_legged_ties = models.BooleanField(
        default=False, help_text="Knockout only: each tie is played home & away (aggregate score)."
    )
    extra_time_enabled = models.BooleanField(default=True, help_text="Knockout only.")
    penalties_enabled = models.BooleanField(
        default=True, help_text="Knockout only: penalty shootout if still level after extra time."
    )
    has_third_place_playoff = models.BooleanField(default=False, help_text="Knockout only.")

    # Group + Knockout setting.
    teams_qualifying_per_group = models.PositiveSmallIntegerField(
        default=2,
        help_text="Group + Knockout only: how many teams from each group advance to the knockout stage.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("season", "name")

    def __str__(self):
        return f"{self.name} ({self.season.name})"

    @property
    def affects_standings(self):
        """Friendlies never affect standings; everything else does."""
        return self.competition_type != self.CompetitionType.FRIENDLY

    @property
    def has_groups(self):
        return self.competition_type == self.CompetitionType.GROUP_KNOCKOUT

    @property
    def has_knockout_bracket(self):
        return self.competition_type in (
            self.CompetitionType.KNOCKOUT,
            self.CompetitionType.GROUP_KNOCKOUT,
        )


class CompetitionTeam(models.Model):
    """
    A club entered into a specific competition. Kept separate from Club
    itself because a club may be active overall but withdraw from one
    competition while staying in another within the same season.
    """

    class Status(models.TextChoices):
        ENTERED = "ENTERED", "Entered"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"
        DISQUALIFIED = "DISQUALIFIED", "Disqualified"

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="entered_teams")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="competition_entries")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENTERED)
    entered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("competition", "club")
        ordering = ["club__name"]

    def __str__(self):
        return f"{self.club.name} in {self.competition.name}"


class Group(models.Model):
    """A group within a Group + Knockout competition, e.g. "Group A"."""

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=50, help_text='e.g. "Group A"')

    class Meta:
        unique_together = ("competition", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.competition.name}"


class GroupTeam(models.Model):
    """A team's placement within a specific group."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="teams")
    competition_team = models.ForeignKey(
        CompetitionTeam, on_delete=models.CASCADE, related_name="group_placement"
    )

    class Meta:
        unique_together = ("group", "competition_team")

    def __str__(self):
        return f"{self.competition_team.club.name} in {self.group.name}"


class KnockoutRound(models.Model):
    """
    An ordered stage of a knockout bracket, e.g. Quarter Finals.
    `order` controls sequence: lower numbers happen earlier.
    Created upfront as a skeleton; bracket-filling logic comes in Phase 3.
    """

    class RoundName(models.TextChoices):
        PRELIMINARY = "PRELIMINARY", "Preliminary Round"
        ROUND_OF_32 = "ROUND_OF_32", "Round of 32"
        ROUND_OF_16 = "ROUND_OF_16", "Round of 16"
        QUARTER_FINAL = "QUARTER_FINAL", "Quarter Finals"
        SEMI_FINAL = "SEMI_FINAL", "Semi Finals"
        THIRD_PLACE = "THIRD_PLACE", "Third Place Playoff"
        FINAL = "FINAL", "Final"

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="knockout_rounds")
    name = models.CharField(max_length=20, choices=RoundName.choices)
    order = models.PositiveSmallIntegerField(help_text="Lower = earlier round. Used for bracket sequencing.")

    class Meta:
        unique_together = ("competition", "name")
        ordering = ["order"]

    def __str__(self):
        return f"{self.get_name_display()} — {self.competition.name}"


class KnockoutFixture(models.Model):
    """
    A single tie within a knockout round, e.g. "Quarter Final 2".
    team_a / team_b are nullable because the bracket skeleton can exist
    before teams are assigned (auto-generation comes in Phase 3).
    `feeds_into` lets the winner be advanced automatically once that
    logic is built, without needing a schema change later.
    """

    round = models.ForeignKey(KnockoutRound, on_delete=models.CASCADE, related_name="fixtures")
    slot_number = models.PositiveSmallIntegerField(
        help_text="Position within the round, e.g. QF1, QF2, QF3, QF4 -> 1,2,3,4."
    )
    team_a = models.ForeignKey(
        CompetitionTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name="knockout_as_team_a"
    )
    team_b = models.ForeignKey(
        CompetitionTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name="knockout_as_team_b"
    )
    winner = models.ForeignKey(
        CompetitionTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name="knockout_wins"
    )
    feeds_into = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fed_from",
        help_text="The next-round fixture the winner of this tie advances to.",
    )

    class Meta:
        unique_together = ("round", "slot_number")
        ordering = ["round__order", "slot_number"]

    def __str__(self):
        a = self.team_a.club.name if self.team_a else "TBD"
        b = self.team_b.club.name if self.team_b else "TBD"
        return f"{self.round.get_name_display()} #{self.slot_number}: {a} vs {b}"