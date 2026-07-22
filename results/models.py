from django.core.exceptions import ValidationError
from django.db import models

from fixtures.models import Fixture
from players.models import Player


class MatchResult(models.Model):
    """
    The official result for a Fixture. One-to-one with Fixture.

    For knockout matches that go to extra time and/or penalties:
    - `home_score` / `away_score` are the 90-minute scores
    - `home_score_et` / `away_score_et` are the extra-time addition
      (i.e. goals scored DURING extra time only, not cumulative)
    - `home_penalties` / `away_penalties` are the shootout scores

    The true winner is determined by `determine_winner()`, which respects
    the competition's extra_time_enabled and penalties_enabled settings.
    """

    fixture = models.OneToOneField(Fixture, on_delete=models.CASCADE, related_name="result")

    home_score = models.PositiveSmallIntegerField()
    away_score = models.PositiveSmallIntegerField()

    # Extra time — only relevant for knockout fixtures
    went_to_extra_time = models.BooleanField(default=False)
    home_score_et = models.PositiveSmallIntegerField(
        default=0, help_text="Goals scored during extra time only (not cumulative)."
    )
    away_score_et = models.PositiveSmallIntegerField(
        default=0, help_text="Goals scored during extra time only (not cumulative)."
    )

    # Penalties — only relevant for knockout fixtures
    went_to_penalties = models.BooleanField(default=False)
    home_penalties = models.PositiveSmallIntegerField(default=0)
    away_penalties = models.PositiveSmallIntegerField(default=0)

    played_at = models.DateTimeField(null=True, blank=True, help_text="Actual datetime the match was played.")
    notes = models.TextField(blank=True, help_text="e.g. match abandoned, crowd issues, etc.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.fixture.home_team.club.name} {self.home_score}–{self.away_score} "
            f"{self.fixture.away_team.club.name}"
        )

    def clean(self):
        if self.went_to_extra_time and not self.fixture.competition.extra_time_enabled:
            raise ValidationError("This competition does not have extra time enabled.")
        if self.went_to_penalties and not self.fixture.competition.penalties_enabled:
            raise ValidationError("This competition does not have penalty shootouts enabled.")
        if self.went_to_penalties and not self.went_to_extra_time:
            raise ValidationError("A match cannot go to penalties without first going to extra time.")

    @property
    def home_total(self):
        """Full-time score including extra time (not penalties)."""
        return self.home_score + self.home_score_et

    @property
    def away_total(self):
        return self.away_score + self.away_score_et

    def determine_winner(self):
        """
        Returns the winning CompetitionTeam, or None if it's a draw
        (draws are valid in league/group stage fixtures).
        Respects extra time and penalty shootout scores.
        """
        if self.went_to_penalties:
            if self.home_penalties > self.away_penalties:
                return self.fixture.home_team
            elif self.away_penalties > self.home_penalties:
                return self.fixture.away_team
            return None  # Should not happen in a valid penalty shootout

        if self.home_total > self.away_total:
            return self.fixture.home_team
        elif self.away_total > self.home_total:
            return self.fixture.away_team
        return None  # Draw


class GoalEvent(models.Model):
    """
    A single goal within a match. Supports own goals and penalties.
    Scorer is a FK to Player but nullable so a result can be recorded
    even if the club hasn't registered all their players in the system yet.
    """

    class Period(models.TextChoices):
        FIRST_HALF = "1H", "First Half"
        SECOND_HALF = "2H", "Second Half"
        EXTRA_TIME_FIRST = "ET1", "Extra Time — First Half"
        EXTRA_TIME_SECOND = "ET2", "Extra Time — Second Half"
        PENALTIES = "PEN", "Penalty Shootout"

    result = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name="goals")
    scorer = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="goals",
        help_text="Leave blank if the player hasn't been registered in FCMS yet.",
    )
    scorer_name_fallback = models.CharField(
        max_length=150, blank=True,
        help_text="Free-text name used when scorer FK is not set.",
    )
    minute = models.PositiveSmallIntegerField(help_text="Minute the goal was scored (e.g. 45, 90).")
    period = models.CharField(max_length=5, choices=Period.choices, default=Period.FIRST_HALF)
    is_own_goal = models.BooleanField(default=False)
    is_penalty = models.BooleanField(default=False)

    class Meta:
        ordering = ["minute"]

    def __str__(self):
        name = self.scorer.full_name if self.scorer else self.scorer_name_fallback or "Unknown"
        og = " (OG)" if self.is_own_goal else ""
        pen = " (P)" if self.is_penalty else ""
        return f"{name} {self.minute}'{og}{pen}"

    @property
    def scorer_display(self):
        if self.scorer:
            return self.scorer.full_name
        return self.scorer_name_fallback or "Unknown"

    @property
    def credited_team(self):
        """
        The team credited with the goal — for an own goal, it's the
        OPPONENT of the scorer's club, not the scorer's club.
        """
        if not self.scorer:
            return None
        club = self.scorer.club
        if self.is_own_goal:
            home_club = self.result.fixture.home_team.club
            return (
                self.result.fixture.away_team
                if club == home_club
                else self.result.fixture.home_team
            )
        return (
            self.result.fixture.home_team
            if club == self.result.fixture.home_team.club
            else self.result.fixture.away_team
        )