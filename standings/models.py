from django.db import models

from competitions.models import Competition, CompetitionTeam, Group


class StandingsRow(models.Model):
    """
    A single team's running totals in a competition (or group).
    Recalculated from scratch every time a result is saved or deleted.

    `group` is set for Group + Knockout competitions so we can display
    separate tables per group. It's null for plain League/Knockout.
    """

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="standings")
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, null=True, blank=True, related_name="standings"
    )
    team = models.ForeignKey(CompetitionTeam, on_delete=models.CASCADE, related_name="standings_row")

    played = models.PositiveSmallIntegerField(default=0)
    won = models.PositiveSmallIntegerField(default=0)
    drawn = models.PositiveSmallIntegerField(default=0)
    lost = models.PositiveSmallIntegerField(default=0)
    goals_for = models.PositiveSmallIntegerField(default=0)
    goals_against = models.PositiveSmallIntegerField(default=0)
    points = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ["-points", "-goals_for", "goals_against"]
        unique_together = ("competition", "team")

    def __str__(self):
        return f"{self.team.club.name} — {self.competition.name} ({self.points} pts)"

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against